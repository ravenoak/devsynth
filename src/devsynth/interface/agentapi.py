"""FastAPI wrapper exposing core workflows.

This module provides a minimal HTTP interface that mirrors the CLI and
WebUI workflows via the :class:`UXBridge` abstraction. Each route
forwards request data to the existing workflow functions and captures
any output generated through the bridge. Responses contain those
messages so API clients receive the same feedback normally shown in
the terminal or WebUI.
"""

from __future__ import annotations

import os
import time
import datetime
from typing import Optional, Sequence, List, Dict, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from devsynth.api import verify_token
from devsynth.logging_setup import DevSynthLogger
from devsynth.interface.ux_bridge import (
    UXBridge,
    ProgressIndicator,
    sanitize_output,
)

logger = DevSynthLogger(__name__)
router = APIRouter()

# Store the latest messages from the API
LATEST_MESSAGES: List[str] = []

# Store request timestamps for rate limiting
REQUEST_TIMESTAMPS: Dict[str, List[float]] = {}

# Store metrics for the API
API_METRICS = {
    "start_time": time.time(),
    "request_count": 0,
    "endpoint_counts": {},
    "error_count": 0,
    "endpoint_latency": {},
}

app = FastAPI(
    title="DevSynth Agent API",
    description="HTTP API for driving DevSynth workflows programmatically",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class APIBridge(UXBridge):
    """Bridge that feeds canned responses and collects output messages."""

    def __init__(self, answers: Optional[Sequence[str]] = None) -> None:
        """Create bridge with optional scripted answers."""
        self._answers = list(answers or [])
        self.messages: List[str] = []

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Return a scripted answer or the provided default."""
        return str(self._answers.pop(0)) if self._answers else str(default or "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Return a scripted boolean answer or the default."""
        if self._answers:
            return bool(self._answers.pop(0))
        return default

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str = None
    ) -> None:
        """Capture workflow output for the API response.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
            message_type: Optional type of message (info, success, warning, error, etc.)
        """
        self.messages.append(sanitize_output(message))

    class _APIProgress(ProgressIndicator):
        def __init__(self, messages: List[str], description: str, total: int) -> None:
            self._messages = messages
            self._description = sanitize_output(description)
            self._total = total
            self._current = 0
            self._status = "Starting..."
            self._subtasks = {}
            self._nested_subtasks = {}
            self._messages.append(self._description)

        def update(
            self,
            *,
            advance: float = 1,
            description: Optional[str] = None,
            status: Optional[str] = None,
        ) -> None:
            if description:
                self._description = sanitize_output(description)

            # Handle status
            if status:
                self._status = sanitize_output(status)
            else:
                # If no status is provided, use a default based on progress
                if self._current >= self._total:
                    self._status = "Complete"
                elif self._current >= 0.99 * self._total:
                    self._status = "Finalizing..."
                elif self._current >= 0.75 * self._total:
                    self._status = "Almost done..."
                elif self._current >= 0.5 * self._total:
                    self._status = "Halfway there..."
                elif self._current >= 0.25 * self._total:
                    self._status = "Processing..."
                else:
                    self._status = "Starting..."

            self._current += advance
            self._messages.append(
                f"{self._description} ({self._current}/{self._total}) - {self._status}"
            )

        def complete(self) -> None:
            # Complete all subtasks first
            for task_id in list(self._subtasks.keys()):
                self.complete_subtask(task_id)

            self._status = "Complete"
            self._messages.append(f"{self._description} complete")

        def add_subtask(
            self, description: str, total: int = 100, status: str = "Starting..."
        ) -> str:
            """Add a subtask to the progress indicator.

            Args:
                description: Description of the subtask
                total: Total steps for the subtask
                status: Initial status message for the subtask

            Returns:
                task_id: ID of the created subtask
            """
            task_id = f"subtask_{len(self._subtasks)}"
            self._subtasks[task_id] = {
                "description": sanitize_output(description),
                "total": total,
                "current": 0,
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
            description: Optional[str] = None,
            status: Optional[str] = None,
        ) -> None:
            """Update a subtask's progress.

            Args:
                task_id: ID of the subtask to update
                advance: Amount to advance the progress
                description: New description for the subtask
                status: Status message to display
            """
            if task_id not in self._subtasks:
                return

            if description:
                self._subtasks[task_id]["description"] = sanitize_output(description)

            # Handle status
            if status:
                self._subtasks[task_id]["status"] = sanitize_output(status)
            else:
                # If no status is provided, use a default based on progress
                current = self._subtasks[task_id]["current"]
                total = self._subtasks[task_id]["total"]
                if current >= total:
                    self._subtasks[task_id]["status"] = "Complete"
                elif current >= 0.99 * total:
                    self._subtasks[task_id]["status"] = "Finalizing..."
                elif current >= 0.75 * total:
                    self._subtasks[task_id]["status"] = "Almost done..."
                elif current >= 0.5 * total:
                    self._subtasks[task_id]["status"] = "Halfway there..."
                elif current >= 0.25 * total:
                    self._subtasks[task_id]["status"] = "Processing..."
                else:
                    self._subtasks[task_id]["status"] = "Starting..."

            self._subtasks[task_id]["current"] += advance
            self._messages.append(
                f"  ↳ {self._subtasks[task_id]['description']} ({self._subtasks[task_id]['current']}/{self._subtasks[task_id]['total']}) - {self._subtasks[task_id]['status']}"
            )

        def complete_subtask(self, task_id: str) -> None:
            """Mark a subtask as complete.

            Args:
                task_id: ID of the subtask to complete
            """
            if task_id not in self._subtasks:
                return

            # Complete all nested subtasks first if any
            if task_id in self._nested_subtasks:
                for nested_id in list(self._nested_subtasks[task_id].keys()):
                    self.complete_nested_subtask(task_id, nested_id)

            self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]
            self._subtasks[task_id]["status"] = "Complete"
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
            """Add a nested subtask to a subtask.

            Args:
                parent_id: ID of the parent subtask
                description: Description of the nested subtask
                total: Total steps for the nested subtask
                status: Initial status message for the nested subtask

            Returns:
                task_id: ID of the created nested subtask
            """
            if parent_id not in self._subtasks:
                return ""

            # Initialize nested subtasks dictionary for parent if it doesn't exist
            if parent_id not in self._nested_subtasks:
                self._nested_subtasks[parent_id] = {}

            task_id = f"nested_{parent_id}_{len(self._nested_subtasks[parent_id])}"
            self._nested_subtasks[parent_id][task_id] = {
                "description": sanitize_output(description),
                "total": total,
                "current": 0,
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
            description: Optional[str] = None,
            status: Optional[str] = None,
        ) -> None:
            """Update a nested subtask's progress.

            Args:
                parent_id: ID of the parent subtask
                task_id: ID of the nested subtask to update
                advance: Amount to advance the progress
                description: New description for the nested subtask
                status: Status message to display
            """
            if (
                parent_id not in self._nested_subtasks
                or task_id not in self._nested_subtasks[parent_id]
            ):
                return

            if description:
                self._nested_subtasks[parent_id][task_id]["description"] = (
                    sanitize_output(description)
                )

            # Handle status
            if status:
                self._nested_subtasks[parent_id][task_id]["status"] = sanitize_output(
                    status
                )
            else:
                # If no status is provided, use a default based on progress
                current = self._nested_subtasks[parent_id][task_id]["current"]
                total = self._nested_subtasks[parent_id][task_id]["total"]
                if current >= total:
                    self._nested_subtasks[parent_id][task_id]["status"] = "Complete"
                elif current >= 0.99 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = "Finalizing..."
                elif current >= 0.75 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = "Almost done..."
                elif current >= 0.5 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = "Halfway there..."
                elif current >= 0.25 * total:
                    self._nested_subtasks[parent_id][task_id][
                        "status"
                    ] = "Processing..."
                else:
                    self._nested_subtasks[parent_id][task_id]["status"] = "Starting..."

            self._nested_subtasks[parent_id][task_id]["current"] += advance
            self._messages.append(
                f"    ↳ {self._nested_subtasks[parent_id][task_id]['description']} ({self._nested_subtasks[parent_id][task_id]['current']}/{self._nested_subtasks[parent_id][task_id]['total']}) - {self._nested_subtasks[parent_id][task_id]['status']}"
            )

        def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
            """Mark a nested subtask as complete.

            Args:
                parent_id: ID of the parent subtask
                task_id: ID of the nested subtask to complete
            """
            if (
                parent_id not in self._nested_subtasks
                or task_id not in self._nested_subtasks[parent_id]
            ):
                return

            self._nested_subtasks[parent_id][task_id]["current"] = (
                self._nested_subtasks[parent_id][task_id]["total"]
            )
            self._nested_subtasks[parent_id][task_id]["status"] = "Complete"
            self._messages.append(
                f"    ↳ {self._nested_subtasks[parent_id][task_id]['description']} complete"
            )

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return self._APIProgress(self.messages, description, total)


LATEST_MESSAGES: List[str] = []


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


class InitRequest(BaseModel):
    __test__ = False
    path: str = "."
    project_root: Optional[str] = None
    language: Optional[str] = None
    goals: Optional[str] = None


class GatherRequest(BaseModel):
    __test__ = False
    goals: str
    constraints: str
    priority: str = "medium"


class SynthesizeRequest(BaseModel):
    __test__ = False
    target: Optional[str] = None


class SpecRequest(BaseModel):
    __test__ = False
    requirements_file: str = "requirements.md"


class TestSpecRequest(BaseModel):
    spec_file: str = "specs.md"
    output_dir: Optional[str] = None

    # Prevent pytest from collecting this model as a test class
    __test__ = False


class CodeRequest(BaseModel):
    __test__ = False
    output_dir: Optional[str] = None


class DoctorRequest(BaseModel):
    __test__ = False
    path: str = "."
    fix: bool = False


class EDRRCycleRequest(BaseModel):
    __test__ = False
    prompt: str
    context: Optional[str] = None
    max_iterations: int = 3


class WorkflowResponse(BaseModel):
    __test__ = False
    messages: List[str]


class AgentAPI:
    """Programmatic wrapper around the CLI workflows."""

    def __init__(self, bridge: UXBridge) -> None:
        """Create the API using ``bridge`` for all interactions."""
        self.bridge = bridge

    def _collect_messages(self) -> List[str]:
        """Return messages captured by the bridge if available."""
        msgs = list(getattr(self.bridge, "messages", []))
        LATEST_MESSAGES[:] = msgs
        return msgs

    def init(
        self,
        *,
        path: str = ".",
        project_root: Optional[str] = None,
        language: Optional[str] = None,
        goals: Optional[str] = None,
    ) -> List[str]:
        """Initialize or onboard a project via :func:`init_cmd`."""
        from devsynth.application.cli import init_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        init_cmd(
            path=path,
            project_root=project_root,
            language=language,
            goals=goals,
            bridge=self.bridge,
        )
        return self._collect_messages()

    def gather(
        self,
        *,
        goals: str,
        constraints: str,
        priority: str = "medium",
    ) -> List[str]:
        """Run the requirements gathering wizard via :func:`gather_cmd`."""
        from devsynth.application.cli import gather_cmd

        if isinstance(self.bridge, APIBridge):
            self.bridge._answers.extend([goals, constraints, priority])
            self.bridge.messages.clear()

        gather_cmd(bridge=self.bridge)
        return self._collect_messages()

    def synthesize(self, *, target: Optional[str] = None) -> List[str]:
        """Execute the synthesis pipeline via :func:`run_pipeline_cmd`."""
        from devsynth.application.cli import run_pipeline_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        run_pipeline_cmd(target=target, bridge=self.bridge)
        return self._collect_messages()

    def spec(self, *, requirements_file: str = "requirements.md") -> List[str]:
        """Generate specifications from requirements via :func:`spec_cmd`."""
        from devsynth.application.cli import spec_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        spec_cmd(requirements_file=requirements_file, bridge=self.bridge)
        return self._collect_messages()

    def test(
        self, *, spec_file: str = "specs.md", output_dir: Optional[str] = None
    ) -> List[str]:
        """Generate tests from specifications via :func:`test_cmd`."""
        from devsynth.application.cli import test_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        test_cmd(spec_file=spec_file, output_dir=output_dir, bridge=self.bridge)
        return self._collect_messages()

    def code(self, *, output_dir: Optional[str] = None) -> List[str]:
        """Generate code from tests via :func:`code_cmd`."""
        from devsynth.application.cli import code_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        code_cmd(output_dir=output_dir, bridge=self.bridge)
        return self._collect_messages()

    def doctor(self, *, path: str = ".", fix: bool = False) -> List[str]:
        """Run diagnostics via :func:`doctor_cmd`."""
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        doctor_cmd(path=path, fix=fix, bridge=self.bridge)
        return self._collect_messages()

    def edrr_cycle(
        self, *, prompt: str, context: Optional[str] = None, max_iterations: int = 3
    ) -> List[str]:
        """Run EDRR cycle via :func:`edrr_cycle_cmd`."""
        from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd

        if hasattr(self.bridge, "messages"):
            self.bridge.messages.clear()

        edrr_cycle_cmd(
            prompt=prompt,
            context=context,
            max_iterations=max_iterations,
            bridge=self.bridge,
        )
        return self._collect_messages()

    def status(self) -> List[str]:
        """Return messages from the most recent workflow invocation."""
        return LATEST_MESSAGES


@router.post("/init", response_model=WorkflowResponse)
def init_endpoint(
    request: InitRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Initialize or onboard a project."""
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
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in init endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize project: {str(e)}",
        )


@router.post("/gather", response_model=WorkflowResponse)
def gather_endpoint(
    request: GatherRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Gather project goals and constraints via the interactive wizard."""
    try:
        answers = [request.goals, request.constraints, request.priority]
        bridge = APIBridge(answers)
        from devsynth.application.cli import gather_cmd

        gather_cmd(bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in gather endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to gather requirements: {str(e)}",
        )


@router.post("/synthesize", response_model=WorkflowResponse)
def synthesize_endpoint(
    request: SynthesizeRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Execute the synthesis pipeline."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli import run_pipeline_cmd

        run_pipeline_cmd(target=request.target, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in synthesize endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run synthesis pipeline: {str(e)}",
        )


@router.post("/spec", response_model=WorkflowResponse)
def spec_endpoint(
    request: SpecRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate specifications from requirements."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli import spec_cmd

        spec_cmd(requirements_file=request.requirements_file, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in spec endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate specifications: {str(e)}",
        )


@router.post("/test", response_model=WorkflowResponse)
def test_endpoint(
    request: TestSpecRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate tests from specifications."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli import test_cmd

        test_cmd(
            spec_file=request.spec_file, output_dir=request.output_dir, bridge=bridge
        )
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {str(e)}",
        )


@router.post("/code", response_model=WorkflowResponse)
def code_endpoint(
    request: CodeRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate code from tests."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli import code_cmd

        code_cmd(output_dir=request.output_dir, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in code endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code: {str(e)}",
        )


@router.post("/doctor", response_model=WorkflowResponse)
def doctor_endpoint(
    request: DoctorRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Run diagnostics."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        doctor_cmd(path=request.path, fix=request.fix, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in doctor endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run diagnostics: {str(e)}",
        )


@router.post("/edrr-cycle", response_model=WorkflowResponse)
def edrr_cycle_endpoint(
    request: EDRRCycleRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Run EDRR cycle."""
    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd

        edrr_cycle_cmd(
            prompt=request.prompt,
            context=request.context,
            max_iterations=request.max_iterations,
            bridge=bridge,
        )
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except Exception as e:
        logger.error(f"Error in edrr-cycle endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run EDRR cycle: {str(e)}",
        )


@router.get("/status", response_model=WorkflowResponse)
def status_endpoint(token: None = Depends(verify_token)) -> WorkflowResponse:
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
    request: Request, token: None = Depends(verify_token)
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["health"] = (
        API_METRICS["endpoint_counts"].get("health", 0) + 1
    )

    return JSONResponse(content={"status": "ok"})


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
    request: Request, token: None = Depends(verify_token)
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["metrics"] = (
        API_METRICS["endpoint_counts"].get("metrics", 0) + 1
    )

    # Calculate uptime
    uptime = time.time() - API_METRICS["start_time"]

    # Generate metrics in Prometheus format
    metrics = []
    metrics.append("# HELP api_uptime_seconds The uptime of the API in seconds")
    metrics.append("# TYPE api_uptime_seconds gauge")
    metrics.append(f"api_uptime_seconds {uptime}")

    metrics.append("# HELP request_count Total number of requests received")
    metrics.append("# TYPE request_count counter")
    metrics.append(f"request_count {API_METRICS['request_count']}")

    metrics.append("# HELP error_count Total number of errors")
    metrics.append("# TYPE error_count counter")
    metrics.append(f"error_count {API_METRICS['error_count']}")

    metrics.append("# HELP endpoint_requests Number of requests per endpoint")
    metrics.append("# TYPE endpoint_requests counter")
    for endpoint, count in API_METRICS["endpoint_counts"].items():
        metrics.append(f'endpoint_requests{{endpoint="{endpoint}"}} {count}')

    metrics.append("# HELP endpoint_latency_seconds Latency per endpoint in seconds")
    metrics.append("# TYPE endpoint_latency_seconds histogram")
    for endpoint, latencies in API_METRICS["endpoint_latency"].items():
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            metrics.append(
                f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="avg"}} {avg_latency}'
            )
            if len(latencies) >= 2:
                latencies.sort()
                p50 = latencies[len(latencies) // 2]
                p95 = latencies[int(len(latencies) * 0.95)]
                p99 = latencies[int(len(latencies) * 0.99)]
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50}'
                )
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95}'
                )
                metrics.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99}'
                )

    return PlainTextResponse(content="\n".join(metrics))


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
    API_METRICS["error_count"] += 1
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
