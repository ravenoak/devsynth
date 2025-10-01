"""FastAPI wrapper exposing core workflows.

This module provides a minimal HTTP interface that mirrors the CLI and
WebUI workflows via the :class:`UXBridge` abstraction. Each route
forwards request data to the existing workflow functions and captures
any output generated through the bridge. Responses contain those
messages so API clients receive the same feedback normally shown in
the terminal or WebUI.
"""

from __future__ import annotations

import time
from typing import Sequence

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse

from devsynth.interface.agentapi_models import (
    APIMetrics,
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    GatherRequest,
    HealthResponse,
    InitRequest,
    MetricsResponse,
    PriorityLevel,
    ProgressSnapshot,
    ProgressStatus,
    SpecRequest,
    SynthesizeRequest,
    TestSpecRequest,
    WorkflowMetadata,
    WorkflowResponse,
    SynthesisTarget,
)
from devsynth.interface.ux_bridge import (
    ProgressIndicator,
    SubtaskProgressSnapshot,
    UXBridge,
    sanitize_output,
)
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
router = APIRouter()


def _verify_token(authorization: str | None = Header(default=None)) -> None:
    """Lazy import to avoid circular dependency during FastAPI setup."""
    from devsynth.api import verify_token as _verify

    return _verify(authorization)


# Store the latest messages from the API
LATEST_MESSAGES: tuple[str, ...] = tuple()

# Store request timestamps for rate limiting
REQUEST_TIMESTAMPS: dict[str, list[float]] = {}

# Store metrics for the API
API_METRICS = APIMetrics(start_time=time.time())

app = FastAPI(
    title="DevSynth Agent API",
    description="HTTP API for driving DevSynth workflows programmatically",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class APIBridge(UXBridge):
    """Bridge that feeds scripted responses and records workflow output."""

    def __init__(self, answers: Sequence[str] | None = None) -> None:
        self._answers = list(answers or [])
        self.messages: list[str] = []
        self._progress_log: list[ProgressSnapshot] = []

    @property
    def progress_snapshots(self) -> tuple[ProgressSnapshot, ...]:
        """Expose captured progress updates as an immutable tuple."""

        return tuple(self._progress_log)

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        del choices, show_default  # Questions are scripted for the API bridge.
        return str(self._answers.pop(0)) if self._answers else str(default or "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        del message
        if self._answers:
            answer = str(self._answers.pop(0)).strip().lower()
            return answer in {"y", "yes", "true", "1"}
        return default

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        del highlight, message_type
        self.messages.append(sanitize_output(message))

    class _APIProgress(ProgressIndicator):
        def __init__(
            self,
            messages: list[str],
            progress_log: list[ProgressSnapshot],
            description: str,
            total: int,
        ) -> None:
            self._messages = messages
            self._progress_log = progress_log
            self._description = sanitize_output(description)
            self._total = float(total)
            self._current = 0.0
            self._status = ProgressStatus.STARTING
            self._subtasks: dict[str, SubtaskProgressSnapshot] = {}
            self._nested_subtasks: dict[str, dict[str, SubtaskProgressSnapshot]] = {}
            self._messages.append(self._description)
            self._record_snapshot()

        def _record_snapshot(self) -> None:
            self._progress_log.append(
                ProgressSnapshot(
                    description=self._description,
                    current=self._current,
                    total=self._total,
                    status=self._status,
                )
            )

        def _auto_status(self, current: float, total: float) -> ProgressStatus:
            if current >= total:
                return ProgressStatus.COMPLETE
            if current >= 0.99 * total:
                return ProgressStatus.FINALIZING
            if current >= 0.75 * total:
                return ProgressStatus.ALMOST_DONE
            if current >= 0.5 * total:
                return ProgressStatus.HALF_COMPLETE
            if current >= 0.25 * total:
                return ProgressStatus.PROCESSING
            return ProgressStatus.STARTING

        def _sanitize_status(self, status: str | None) -> ProgressStatus:
            if status:
                for candidate in ProgressStatus:
                    if candidate.value == status:
                        return candidate
            return self._auto_status(self._current, self._total)

        def update(
            self,
            *,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            if description:
                self._description = sanitize_output(description)

            self._current = max(0.0, self._current + float(advance))
            self._status = self._sanitize_status(status)
            self._messages.append(
                f"{self._description} ({self._current}/{self._total}) - {self._status.value}"
            )
            self._record_snapshot()

        def complete(self) -> None:
            for task_id in list(self._subtasks.keys()):
                self.complete_subtask(task_id)

            self._status = ProgressStatus.COMPLETE
            self._messages.append(f"{self._description} complete")
            self._record_snapshot()

        def add_subtask(
            self, description: str, total: int = 100, status: str = "Starting..."
        ) -> str:
            task_id = f"subtask_{len(self._subtasks)}"
            self._subtasks[task_id] = {
                "description": sanitize_output(description),
                "total": float(total),
                "current": 0.0,
                "status": status,
            }
            self._messages.append(
                f"  ↳ {self._subtasks[task_id]['description']} - {status}"
            )
            return task_id

        def update_subtask(
            self,
            task_id: str,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            if task_id not in self._subtasks:
                return

            if description:
                self._subtasks[task_id]["description"] = sanitize_output(description)

            if status:
                self._subtasks[task_id]["status"] = sanitize_output(status)
            else:
                current = self._subtasks[task_id]["current"]
                total = self._subtasks[task_id]["total"]
                if current >= total:
                    self._subtasks[task_id]["status"] = ProgressStatus.COMPLETE.value
                elif current >= 0.99 * total:
                    self._subtasks[task_id]["status"] = ProgressStatus.FINALIZING.value
                elif current >= 0.75 * total:
                    self._subtasks[task_id]["status"] = ProgressStatus.ALMOST_DONE.value
                elif current >= 0.5 * total:
                    self._subtasks[task_id]["status"] = ProgressStatus.HALF_COMPLETE.value
                elif current >= 0.25 * total:
                    self._subtasks[task_id]["status"] = ProgressStatus.PROCESSING.value
                else:
                    self._subtasks[task_id]["status"] = ProgressStatus.STARTING.value

            self._subtasks[task_id]["current"] += float(advance)
            self._messages.append(
                f"  ↳ {self._subtasks[task_id]['description']} ({self._subtasks[task_id]['current']}/{self._subtasks[task_id]['total']}) - {self._subtasks[task_id]['status']}"
            )

        def complete_subtask(self, task_id: str) -> None:
            if task_id not in self._subtasks:
                return

            self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]
            self._subtasks[task_id]["status"] = ProgressStatus.COMPLETE.value
            self._messages.append(
                f"  ↳ {self._subtasks[task_id]['description']} complete"
            )

        def add_nested_subtask(
            self,
            parent_id: str,
            description: str,
            total: int = 100,
            status: str = "Starting...",
        ) -> str:
            if parent_id not in self._nested_subtasks:
                self._nested_subtasks[parent_id] = {}
            task_id = f"nested_{len(self._nested_subtasks[parent_id])}"
            self._nested_subtasks[parent_id][task_id] = {
                "description": sanitize_output(description),
                "total": float(total),
                "current": 0.0,
                "status": status,
            }
            self._messages.append(
                f"    ↳ {self._nested_subtasks[parent_id][task_id]['description']} - {status}"
            )
            return task_id

        def update_nested_subtask(
            self,
            parent_id: str,
            task_id: str,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            if (
                parent_id not in self._nested_subtasks
                or task_id not in self._nested_subtasks[parent_id]
            ):
                return

            if description:
                self._nested_subtasks[parent_id][task_id]["description"] = (
                    sanitize_output(description)
                )

            if status:
                self._nested_subtasks[parent_id][task_id]["status"] = sanitize_output(
                    status
                )
            else:
                current = self._nested_subtasks[parent_id][task_id]["current"]
                total = self._nested_subtasks[parent_id][task_id]["total"]
                if current >= total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.COMPLETE.value
                elif current >= 0.99 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.FINALIZING.value
                elif current >= 0.75 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.ALMOST_DONE.value
                elif current >= 0.5 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.HALF_COMPLETE.value
                elif current >= 0.25 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.PROCESSING.value
                else:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = ProgressStatus.STARTING.value

            self._nested_subtasks[parent_id][task_id]["current"] += float(advance)
            self._messages.append(
                f"    ↳ {self._nested_subtasks[parent_id][task_id]['description']} ({self._nested_subtasks[parent_id][task_id]['current']}/{self._nested_subtasks[parent_id][task_id]['total']}) - {self._nested_subtasks[parent_id][task_id]['status']}"
            )

        def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
            if (
                parent_id not in self._nested_subtasks
                or task_id not in self._nested_subtasks[parent_id]
            ):
                return

            self._nested_subtasks[parent_id][task_id]["current"] = (
                self._nested_subtasks[parent_id][task_id]["total"]
            )
            self._nested_subtasks[parent_id][task_id]["status"] = (
                ProgressStatus.COMPLETE.value
            )
            self._messages.append(
                f"    ↳ {self._nested_subtasks[parent_id][task_id]['description']} complete"
            )

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return self._APIProgress(self.messages, self._progress_log, description, total)


def rate_limit(request: Request, limit: int = 10, window: int = 60) -> None:
    """Rate limit requests based on client IP address.

    Args:
        request: The FastAPI request object
        limit: Maximum number of requests allowed in the window
        window: Time window in seconds

    Raises:
        HTTPException: If the rate limit is exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # Initialize or update timestamps for this client
    if client_ip not in REQUEST_TIMESTAMPS:
        REQUEST_TIMESTAMPS[client_ip] = []

    # Remove timestamps older than the window
    REQUEST_TIMESTAMPS[client_ip] = [
        ts for ts in REQUEST_TIMESTAMPS[client_ip] if current_time - ts < window
    ]

    # Check if the rate limit is exceeded
    if len(REQUEST_TIMESTAMPS[client_ip]) >= limit:
        logger.warning(f"Rate limit exceeded for client {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {window} seconds.",
        )

    # Add the current timestamp
    REQUEST_TIMESTAMPS[client_ip].append(current_time)
class AgentAPI:
    """Programmatic wrapper around the CLI workflows."""

    def __init__(self, bridge: UXBridge) -> None:
        self.bridge = bridge

    def _collect_response(self) -> WorkflowResponse:
        messages = tuple(getattr(self.bridge, "messages", []))
        metadata: WorkflowMetadata | None = None
        if isinstance(self.bridge, APIBridge):
            metadata = WorkflowMetadata(progress=self.bridge.progress_snapshots)

        global LATEST_MESSAGES
        LATEST_MESSAGES = messages
        return WorkflowResponse(messages=messages, metadata=metadata)

    def _clear_messages(self) -> None:
        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

    def init(
        self,
        *,
        path: str = ".",
        project_root: str | None = None,
        language: str | None = None,
        goals: str | None = None,
    ) -> WorkflowResponse:
        from devsynth.application.cli import init_cmd

        self._clear_messages()
        init_cmd(
            path=path,
            project_root=project_root,
            language=language,
            goals=goals,
            bridge=self.bridge,
        )
        return self._collect_response()

    def gather(
        self,
        *,
        goals: str,
        constraints: str,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
    ) -> WorkflowResponse:
        from devsynth.application.cli import gather_cmd

        if isinstance(self.bridge, APIBridge):
            self.bridge._answers.extend([goals, constraints, priority.value])
            self._clear_messages()

        gather_cmd(bridge=self.bridge)
        return self._collect_response()

    def synthesize(
        self, *, target: SynthesisTarget | None = None
    ) -> WorkflowResponse:
        from devsynth.application.cli import run_pipeline_cmd

        self._clear_messages()
        run_pipeline_cmd(target=target.value if target else None, bridge=self.bridge)
        return self._collect_response()

    def spec(self, *, requirements_file: str = "requirements.md") -> WorkflowResponse:
        from devsynth.application.cli import spec_cmd

        self._clear_messages()
        spec_cmd(requirements_file=requirements_file, bridge=self.bridge)
        return self._collect_response()

    def test(
        self, *, spec_file: str = "specs.md", output_dir: str | None = None
    ) -> WorkflowResponse:
        from devsynth.application.cli import test_cmd

        self._clear_messages()
        test_cmd(spec_file=spec_file, output_dir=output_dir, bridge=self.bridge)
        return self._collect_response()

    def code(self, *, output_dir: str | None = None) -> WorkflowResponse:
        from devsynth.application.cli import code_cmd

        self._clear_messages()
        code_cmd(output_dir=output_dir, bridge=self.bridge)
        return self._collect_response()

    def doctor(self, *, path: str = ".", fix: bool = False) -> WorkflowResponse:
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        self._clear_messages()
        doctor_cmd(path=path, fix=fix, bridge=self.bridge)
        return self._collect_response()

    def edrr_cycle(
        self,
        *,
        prompt: str,
        context: str | None = None,
        max_iterations: int = 3,
    ) -> WorkflowResponse:
        from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd

        self._clear_messages()
        edrr_cycle_cmd(
            prompt=prompt,
            context=context,
            max_iterations=max_iterations,
            bridge=self.bridge,
        )
        return self._collect_response()

    def status(self) -> WorkflowResponse:
        return WorkflowResponse(messages=LATEST_MESSAGES)


@router.post("/init", response_model=WorkflowResponse)
def init_endpoint(
    request: InitRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Initialize or onboard a project."""
    if request.path is None:
        raise HTTPException(status_code=400, detail="path is required")
    if request.path == "":
        raise HTTPException(status_code=400, detail="path cannot be empty")

    bridge = APIBridge()
    try:
        from devsynth.application.cli import init_cmd

        init_cmd(
            path=request.path,
            project_root=request.project_root,
            language=request.language,
            goals=request.goals,
            bridge=bridge,
        )
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in init endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize project: {str(e)}",
        )


@router.post("/gather", response_model=WorkflowResponse)
def gather_endpoint(
    request: GatherRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Gather project goals and constraints via the interactive wizard."""
    if request.goals is None:
        raise HTTPException(status_code=400, detail="goals are required")
    if request.goals == "":
        raise HTTPException(status_code=400, detail="goals cannot be empty")

    try:
        answers = [request.goals, request.constraints, request.priority]
        bridge = APIBridge(answers)
        from devsynth.application.cli import gather_cmd

        gather_cmd(bridge=bridge)
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in gather endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to gather requirements: {str(e)}",
        )


@router.post("/synthesize", response_model=WorkflowResponse)
def synthesize_endpoint(
    request: SynthesizeRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Execute the synthesis pipeline."""
    if request.target is None:
        raise HTTPException(status_code=400, detail="target is required")
    if request.target == "":
        raise HTTPException(status_code=400, detail="target cannot be empty")
    valid_targets = {
        "unit",
        "unit-tests",
        "integration",
        "integration-tests",
        "behavior",
        "behavior-tests",
        "all",
    }
    if request.target not in valid_targets:
        raise HTTPException(
            status_code=400,
            detail="target must be one of " + ", ".join(sorted(valid_targets)),
        )

    try:
        bridge = APIBridge()
        from devsynth.application.cli import run_pipeline_cmd

        run_pipeline_cmd(target=request.target, bridge=bridge)
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in synthesize endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run synthesis pipeline: {str(e)}",
        )


@router.post("/spec", response_model=WorkflowResponse)
def spec_endpoint(
    request: SpecRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Generate specifications from requirements."""
    if request.requirements_file is None:
        raise HTTPException(status_code=400, detail="requirements_file is required")
    if request.requirements_file == "":
        raise HTTPException(status_code=400, detail="requirements_file cannot be empty")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import spec_cmd

        spec_cmd(requirements_file=request.requirements_file, bridge=bridge)
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in spec endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate specifications: {str(e)}",
        )


@router.post("/test", response_model=WorkflowResponse)
def test_endpoint(
    request: TestSpecRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Generate tests from specifications."""
    if request.spec_file is None:
        raise HTTPException(status_code=400, detail="spec_file is required")
    if request.spec_file == "":
        raise HTTPException(status_code=400, detail="spec_file cannot be empty")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import test_cmd

        test_cmd(
            spec_file=request.spec_file, output_dir=request.output_dir, bridge=bridge
        )
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {str(e)}",
        )


# Prevent pytest from collecting the router function as a test
test_endpoint.__test__ = False


@router.post("/code", response_model=WorkflowResponse)
def code_endpoint(
    request: CodeRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Generate code from tests."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli import code_cmd

        code_cmd(output_dir=request.output_dir, bridge=bridge)
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in code endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code: {str(e)}",
        )


@router.post("/doctor", response_model=WorkflowResponse)
def doctor_endpoint(
    request: DoctorRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Run diagnostics."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        doctor_cmd(path=request.path, fix=request.fix, bridge=bridge)
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in doctor endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run diagnostics: {str(e)}",
        )


@router.post("/edrr-cycle", response_model=WorkflowResponse)
def edrr_cycle_endpoint(
    request: EDRRCycleRequest, token: None = Depends(_verify_token)
) -> WorkflowResponse:
    """Run EDRR cycle."""
    if request.prompt is None:
        raise HTTPException(status_code=400, detail="prompt is required")
    if request.prompt == "":
        raise HTTPException(status_code=400, detail="prompt cannot be empty")
    if request.max_iterations <= 0:
        raise HTTPException(status_code=400, detail="max_iterations must be positive")

    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd

        edrr_cycle_cmd(
            prompt=request.prompt,
            context=request.context,
            max_iterations=request.max_iterations,
            bridge=bridge,
        )
        global LATEST_MESSAGES
        LATEST_MESSAGES = tuple(bridge.messages)
        return WorkflowResponse(messages=LATEST_MESSAGES)
    except Exception as e:
        logger.error(f"Error in edrr-cycle endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run EDRR cycle: {str(e)}",
        )


@router.get("/status", response_model=WorkflowResponse)
def status_endpoint(token: None = Depends(_verify_token)) -> WorkflowResponse:
    """Return messages from the most recent workflow invocation."""
    return WorkflowResponse(messages=LATEST_MESSAGES)


@router.get(
    "/health",
    responses={
        200: {"description": "API is healthy"},
        401: {"model": WorkflowResponse, "description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
    },
    tags=["Monitoring"],
    summary="Check API health",
    description="Check if the API is healthy and responding to requests.",
)
def health_endpoint(
    request: Request, token: None = Depends(_verify_token)
) -> JSONResponse:
    """Check if the API is healthy.

    This endpoint returns a simple health check response.

    Args:
        request: The FastAPI request object
        token: Authentication token (injected by FastAPI)

    Returns:
        A JSON response indicating the API is healthy

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    API_METRICS.request_count += 1
    API_METRICS.endpoint_counts["health"] = (
        API_METRICS.endpoint_counts.get("health", 0) + 1
    )

    uptime = time.time() - API_METRICS.start_time
    payload = HealthResponse(status="ok", uptime=uptime)
    return JSONResponse(content=payload.model_dump())


@router.get(
    "/metrics",
    responses={
        200: {"description": "API metrics"},
        401: {"model": WorkflowResponse, "description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
    },
    tags=["Monitoring"],
    summary="Get API metrics",
    description="Get metrics about API usage and performance.",
)
def metrics_endpoint(
    request: Request, token: None = Depends(_verify_token)
) -> PlainTextResponse:
    """Get API metrics.

    This endpoint returns metrics about API usage and performance.

    Args:
        request: The FastAPI request object
        token: Authentication token (injected by FastAPI)

    Returns:
        A plain text response with metrics in Prometheus format

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    API_METRICS.request_count += 1
    API_METRICS.endpoint_counts["metrics"] = (
        API_METRICS.endpoint_counts.get("metrics", 0) + 1
    )

    # Calculate uptime
    uptime = time.time() - API_METRICS.start_time

    # Generate metrics in Prometheus format
    metrics = []
    metrics.append("# HELP api_uptime_seconds The uptime of the API in seconds")
    metrics.append("# TYPE api_uptime_seconds gauge")
    metrics.append(f"api_uptime_seconds {uptime}")

    metrics.append("# HELP request_count Total number of requests received")
    metrics.append("# TYPE request_count counter")
    metrics.append(f"request_count {API_METRICS.request_count}")

    metrics.append("# HELP error_count Total number of errors")
    metrics.append("# TYPE error_count counter")
    metrics.append(f"error_count {API_METRICS.error_count}")

    metrics.append("# HELP endpoint_requests Number of requests per endpoint")
    metrics.append("# TYPE endpoint_requests counter")
    for endpoint, count in API_METRICS.endpoint_counts.items():
        metrics.append(f'endpoint_requests{{endpoint="{endpoint}"}} {count}')

    metrics.append("# HELP endpoint_latency_seconds Latency per endpoint in seconds")
    metrics.append("# TYPE endpoint_latency_seconds histogram")
    for endpoint, latencies in API_METRICS.endpoint_latency.items():
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            metrics.append(
                f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="avg"}} {avg_latency}'
            )
            if len(latencies) >= 2:
                sorted_latencies = sorted(latencies)
                p50 = sorted_latencies[len(sorted_latencies) // 2]
                p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50}'
                )
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95}'
                )
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99}'
                )

    metrics_payload = MetricsResponse(metrics=tuple(metrics))
    return PlainTextResponse(content="\n".join(metrics_payload.metrics))


# Add exception handlers for common errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return a structured error response."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Maintain compatibility with original format for unauthorized errors
    if exc.status_code == status.HTTP_401_UNAUTHORIZED and exc.detail == "Unauthorized":
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions and return a structured error response."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    API_METRICS.error_count += 1
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": f"Failed to process request: {str(exc)}",
            "details": str(exc),
            "suggestions": [
                "Check the logs for more information",
                "Contact support if the issue persists",
            ],
        },
    )


app.include_router(router)


__all__ = [
    "app",
    "router",
    "APIBridge",
    "AgentAPI",
    "InitRequest",
    "GatherRequest",
    "SynthesizeRequest",
    "SpecRequest",
    "TestSpecRequest",
    "CodeRequest",
    "DoctorRequest",
    "EDRRCycleRequest",
    "WorkflowResponse",
]
