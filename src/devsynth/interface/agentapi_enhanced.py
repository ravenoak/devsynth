"""Enhanced Agent API with improved error handling, documentation, and security.

This module extends the existing Agent API with:
1. More specific error handling for different types of errors
2. More informative error messages that provide guidance on how to fix issues
3. Better logging that includes more context about requests and errors
4. Detailed docstrings and examples for OpenAPI documentation
5. Rate limiting to prevent abuse
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict
from collections.abc import Sequence

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from devsynth.api import verify_token
from devsynth.interface.agentapi import APIBridge as BaseAPIBridge
from devsynth.interface.agentapi_models import (
    APIMetrics,
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    GatherRequest,
    HealthResponse,
    InitRequest,
    MetricsResponse,
    SpecRequest,
    SynthesizeRequest,
    TestSpecRequest,
    WorkflowResponse,
)
from devsynth.interface.ux_bridge import sanitize_output
from devsynth.logging_setup import DevSynthLogger

# Configure logging
logger = DevSynthLogger(__name__)

# Create a router for the API endpoints
router = APIRouter()


@dataclass(slots=True)
class RateLimiterState:
    """Track request timestamps for each client."""

    limit: int = 10
    window_seconds: int = 60
    buckets: DefaultDict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def prune(self, client_ip: str, *, now: float, window: int) -> None:
        """Drop timestamps outside the configured window."""

        bucket = self.buckets[client_ip]
        if not bucket:
            return
        self.buckets[client_ip] = [ts for ts in bucket if now - ts < window]

    def count(self, client_ip: str) -> int:
        """Return the number of tracked timestamps for the client."""

        return len(self.buckets[client_ip])

    def record(self, client_ip: str, *, timestamp: float) -> None:
        """Register a request timestamp for the client."""

        self.buckets[client_ip].append(timestamp)


@dataclass(slots=True)
class MetricsTracker:
    """Lightweight metrics accumulator that mirrors ``APIMetrics``."""

    start_time: float = field(default_factory=time.time)
    request_count: int = 0
    error_count: int = 0
    endpoint_counts: dict[str, int] = field(default_factory=dict)
    endpoint_latency: dict[str, list[float]] = field(default_factory=dict)

    def increment(self, endpoint: str) -> None:
        """Record a request for the provided endpoint."""

        self.request_count += 1
        self.endpoint_counts[endpoint] = self.endpoint_counts.get(endpoint, 0) + 1

    def record_latency(self, endpoint: str, latency: float) -> None:
        """Track latency for an endpoint, ignoring negative values."""

        if latency < 0:
            return
        samples = self.endpoint_latency.setdefault(endpoint, [])
        samples.append(latency)

    def record_error(self) -> None:
        """Increment the error counter."""

        self.error_count += 1

    def snapshot(self) -> APIMetrics:
        """Materialize the metrics in the shared Pydantic schema."""

        return APIMetrics(
            start_time=self.start_time,
            request_count=self.request_count,
            error_count=self.error_count,
            endpoint_counts=dict(self.endpoint_counts),
            endpoint_latency={
                endpoint: tuple(samples)
                for endpoint, samples in self.endpoint_latency.items()
            },
        )


@dataclass(slots=True)
class AgentAPIState:
    """Container for mutable API state to simplify testing."""

    latest_messages: tuple[str, ...] = tuple()
    rate_limiter: RateLimiterState = field(default_factory=RateLimiterState)
    metrics: MetricsTracker = field(default_factory=MetricsTracker)


STATE = AgentAPIState()


def get_state() -> AgentAPIState:
    """Expose the singleton API state for use within the module."""

    return STATE


def reset_state(state: AgentAPIState | None = None) -> AgentAPIState:
    """Reset the global state (primarily for tests)."""

    global STATE
    STATE = state or AgentAPIState()
    return STATE


class APIBridge(BaseAPIBridge):
    """Bridge for API interactions that records prompts and answers."""

    def __init__(self, answers: Sequence[str] | None = None) -> None:
        super().__init__(answers=answers)

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        self.messages.append(sanitize_output(message))
        return super().ask_question(
            message,
            choices=choices,
            default=default,
            show_default=show_default,
        )

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        self.messages.append(sanitize_output(message))
        return super().confirm_choice(message, default=default)


def _increment_endpoint(endpoint: str) -> None:
    get_state().metrics.increment(endpoint)


def _record_latency(endpoint: str, start_time: float) -> None:
    get_state().metrics.record_latency(endpoint, time.time() - start_time)


def _record_error() -> None:
    get_state().metrics.record_error()


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: str = Field(
        description="Error message",
        json_schema_extra={"example": "Failed to initialize project: File not found"},
    )
    details: str | None = Field(
        default=None,
        description="Additional details about the error",
        json_schema_extra={"example": "The specified path does not exist"},
    )
    suggestions: tuple[str, ...] | None = Field(
        default=None,
        description="Suggestions for resolving the error",
        json_schema_extra={
            "example": (
                "Create the directory before initializing",
                "Check the path and try again",
            )
        },
    )


def _store_messages(messages: Sequence[str]) -> tuple[str, ...]:
    """Persist workflow messages and expose them as an immutable tuple."""

    state = get_state()
    state.latest_messages = tuple(messages)
    return state.latest_messages


def _error_detail(
    message: str,
    *,
    details: str | None = None,
    suggestions: Sequence[str] | None = None,
) -> dict[str, object]:
    """Create a structured error payload for HTTP exceptions."""

    return ErrorResponse(
        error=message,
        details=details,
        suggestions=tuple(suggestions) if suggestions is not None else None,
    ).model_dump()


def rate_limit(
    request: Request,
    limit: int | None = None,
    window: int | None = None,
    *,
    state: AgentAPIState | None = None,
    current_time: float | None = None,
) -> None:
    """Rate limit requests based on client IP address.

    Args:
        request: The FastAPI request object
        limit: Maximum number of requests allowed in the window
        window: Time window in seconds

    Raises:
        HTTPException: If the rate limit is exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    now = current_time if current_time is not None else time.time()
    state_obj = state or get_state()

    limiter = state_obj.rate_limiter
    effective_limit = limit if limit is not None else limiter.limit
    window_seconds = window if window is not None else limiter.window_seconds

    limiter.prune(client_ip, now=now, window=window_seconds)

    if limiter.count(client_ip) >= effective_limit:
        logger.warning(f"Rate limit exceeded for client {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_error_detail(
                "Rate limit exceeded",
                details=f"Try again in {window_seconds} seconds.",
                suggestions=("Wait before retrying the request",),
            ),
        )

    limiter.record(client_ip, timestamp=now)


@router.post(
    "/init",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Initialize a project",
    description="Initialize or onboard a project with the specified parameters.",
)
async def init_endpoint(
    request: Request, init_request: InitRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Initialize or onboard a project.

    This endpoint initializes a new DevSynth project or onboards an existing project.
    It creates the necessary configuration files and directories.

    Args:
        request: The FastAPI request object
        init_request: The initialization request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the initialization process

    Raises:
        HTTPException: If initialization fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    bridge = APIBridge()
    try:
        from devsynth.application.cli import init_cmd

        # Check if the path exists
        if not os.path.exists(init_request.path):
            logger.error(f"Path not found: {init_request.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Path not found: {init_request.path}",
                    suggestions=(
                        "Create the directory before initializing",
                        "Check the path and try again",
                    ),
                ),
            )

        init_cmd(
            path=init_request.path,
            project_root=init_request.project_root,
            language=init_request.language,
            goals=init_request.goals,
            bridge=bridge,
        )
        messages = _store_messages(bridge.messages)
        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in init endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    f"Permission denied: {str(e)}",
                    suggestions=(
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to initialize project: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/gather",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Gather project requirements",
    description="Gather project goals and constraints via the interactive wizard.",
)
async def gather_endpoint(
    request: Request, gather_request: GatherRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Gather project requirements.

    This endpoint gathers project goals and constraints via the interactive wizard.
    It creates a requirements plan file with the gathered information.

    Args:
        request: The FastAPI request object
        gather_request: The gather request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the gathering process

    Raises:
        HTTPException: If gathering fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("gather")

    try:
        answers = [
            gather_request.goals,
            gather_request.constraints or "",
            gather_request.priority.value,
        ]
        bridge = APIBridge(answers)
        from devsynth.application.cli import gather_cmd

        gather_cmd(bridge=bridge)
        messages = _store_messages(bridge.messages)

        _record_latency("gather", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in gather endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Invalid input: {str(e)}",
                    suggestions=(
                        "Check the input values",
                        "Ensure all required fields are provided",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to gather requirements: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/synthesize",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Synthesize code",
    description="Execute the synthesis pipeline to generate code.",
)
async def synthesize_endpoint(
    request: Request,
    synthesize_request: SynthesizeRequest,
    token: None = Depends(verify_token),
) -> WorkflowResponse:
    """Synthesize code from requirements.

    This endpoint executes the synthesis pipeline to generate code from requirements.

    Args:
        request: The FastAPI request object
        synthesize_request: The synthesize request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the synthesis process

    Raises:
        HTTPException: If synthesis fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("synthesize")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import run_pipeline_cmd

        run_pipeline_cmd(
            target=(
                synthesize_request.target.value if synthesize_request.target else None
            ),
            bridge=bridge,
        )
        messages = _store_messages(bridge.messages)

        _record_latency("synthesize", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in synthesize endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to run synthesis pipeline: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/spec",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Generate specifications",
    description="Generate specifications from requirements.",
)
async def spec_endpoint(
    request: Request, spec_request: SpecRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate specifications from requirements.

    This endpoint generates specifications from the provided requirements file.

    Args:
        request: The FastAPI request object
        spec_request: The spec request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the specification generation process

    Raises:
        HTTPException: If specification generation fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("spec")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import spec_cmd

        # Check if the requirements file exists
        if not os.path.exists(spec_request.requirements_file):
            logger.error(
                f"Requirements file not found: {spec_request.requirements_file}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Requirements file not found: {spec_request.requirements_file}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )

        spec_cmd(requirements_file=spec_request.requirements_file, bridge=bridge)
        messages = _store_messages(bridge.messages)

        _record_latency("spec", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in spec endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    f"Permission denied: {str(e)}",
                    suggestions=(
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to generate specifications: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/test",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Generate tests",
    description="Generate tests from specifications.",
)
async def test_endpoint(
    request: Request, test_request: TestSpecRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate tests from specifications.

    This endpoint generates tests from the provided specifications file.

    Args:
        request: The FastAPI request object
        test_request: The test request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the test generation process

    Raises:
        HTTPException: If test generation fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("test")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import test_cmd

        # Check if the spec file exists
        if not os.path.exists(test_request.spec_file):
            logger.error(f"Spec file not found: {test_request.spec_file}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Spec file not found: {test_request.spec_file}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )

        # Check if the output directory exists if provided
        if test_request.output_dir and not os.path.exists(test_request.output_dir):
            logger.error(f"Output directory not found: {test_request.output_dir}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Output directory not found: {test_request.output_dir}",
                    suggestions=(
                        "Create the directory before generating tests",
                        "Provide the correct directory path",
                    ),
                ),
            )

        test_cmd(
            spec_file=test_request.spec_file,
            output_dir=test_request.output_dir,
            bridge=bridge,
        )
        messages = _store_messages(bridge.messages)

        _record_latency("test", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in test endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    f"Permission denied: {str(e)}",
                    suggestions=(
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to generate tests: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/code",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Generate code",
    description="Generate code from tests.",
)
async def code_endpoint(
    request: Request, code_request: CodeRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Generate code from tests.

    This endpoint generates code from the existing tests.

    Args:
        request: The FastAPI request object
        code_request: The code request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the code generation process

    Raises:
        HTTPException: If code generation fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("code")

    try:
        bridge = APIBridge()
        from devsynth.application.cli import code_cmd

        # Check if the output directory exists if provided
        if code_request.output_dir and not os.path.exists(code_request.output_dir):
            logger.error(f"Output directory not found: {code_request.output_dir}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Output directory not found: {code_request.output_dir}",
                    suggestions=(
                        "Create the directory before generating code",
                        "Provide the correct directory path",
                    ),
                ),
            )

        code_cmd(output_dir=code_request.output_dir, bridge=bridge)
        messages = _store_messages(bridge.messages)

        _record_latency("code", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in code endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    f"Permission denied: {str(e)}",
                    suggestions=(
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to generate code: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/doctor",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Run diagnostics",
    description="Run diagnostics on a project.",
)
async def doctor_endpoint(
    request: Request, doctor_request: DoctorRequest, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Run diagnostics on a project.

    This endpoint runs diagnostics on a project and optionally fixes issues.

    Args:
        request: The FastAPI request object
        doctor_request: The doctor request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the diagnostics process

    Raises:
        HTTPException: If diagnostics fail or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("doctor")

    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        # Check if the path exists
        if not os.path.exists(doctor_request.path):
            logger.error(f"Path not found: {doctor_request.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Path not found: {doctor_request.path}",
                    suggestions=(
                        "Check that the directory exists",
                        "Provide the correct directory path",
                    ),
                ),
            )

        doctor_cmd(path=doctor_request.path, fix=doctor_request.fix, bridge=bridge)
        messages = _store_messages(bridge.messages)

        _record_latency("doctor", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in doctor endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"File not found: {str(e)}",
                    suggestions=(
                        "Check that the file exists",
                        "Provide the correct file path",
                    ),
                ),
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(
                    f"Permission denied: {str(e)}",
                    suggestions=(
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to run diagnostics: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.post(
    "/edrr-cycle",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Project Management"],
    summary="Run EDRR cycle",
    description="Run an EDRR cycle with the specified prompt.",
)
async def edrr_cycle_endpoint(
    request: Request,
    edrr_cycle_request: EDRRCycleRequest,
    token: None = Depends(verify_token),
) -> WorkflowResponse:
    """Run an EDRR cycle.

    This endpoint runs an EDRR cycle with the specified prompt and context.

    Args:
        request: The FastAPI request object
        edrr_cycle_request: The EDRR cycle request parameters
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the EDRR cycle

    Raises:
        HTTPException: If the EDRR cycle fails or rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    # Track metrics
    start_time = time.time()
    _increment_endpoint("edrr-cycle")

    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd

        # Validate max_iterations
        if (
            edrr_cycle_request.max_iterations < 1
            or edrr_cycle_request.max_iterations > 10
        ):
            logger.error(f"Invalid max_iterations: {edrr_cycle_request.max_iterations}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Invalid max_iterations: {edrr_cycle_request.max_iterations}",
                    suggestions=("Use a value between 1 and 10 for max_iterations",),
                ),
            )

        edrr_cycle_cmd(
            prompt=edrr_cycle_request.prompt,
            context=edrr_cycle_request.context,
            max_iterations=edrr_cycle_request.max_iterations,
            bridge=bridge,
        )
        messages = _store_messages(bridge.messages)

        _record_latency("edrr-cycle", start_time)

        return WorkflowResponse(messages=messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        _record_error()
        raise
    except Exception as e:
        _record_error()
        logger.error(f"Error in edrr-cycle endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    f"Invalid input: {str(e)}",
                    suggestions=(
                        "Check the input values",
                        "Ensure all required fields are provided",
                    ),
                ),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_error_detail(
                    f"Failed to run EDRR cycle: {str(e)}",
                    details=str(e),
                    suggestions=(
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ),
                ),
            )


@router.get(
    "/health",
    responses={
        200: {"description": "API is healthy"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    tags=["Monitoring"],
    summary="Check API health",
    description="Check if the API is healthy and responding to requests.",
)
async def health_endpoint(
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
    _increment_endpoint("health")

    metrics = get_state().metrics
    uptime = time.time() - metrics.start_time
    payload = HealthResponse(status="ok", uptime=uptime)
    return JSONResponse(content=payload.model_dump())


@router.get(
    "/metrics",
    responses={
        200: {"description": "API metrics"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    tags=["Monitoring"],
    summary="Get API metrics",
    description="Get metrics about API usage and performance.",
)
async def metrics_endpoint(
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
    _increment_endpoint("metrics")

    # Snapshot metrics for rendering
    metrics_state = get_state().metrics.snapshot()
    uptime = time.time() - metrics_state.start_time

    # Generate metrics in Prometheus format
    lines: list[str] = []
    lines.append("# HELP api_uptime_seconds The uptime of the API in seconds")
    lines.append("# TYPE api_uptime_seconds gauge")
    lines.append(f"api_uptime_seconds {uptime}")

    lines.append("# HELP request_count Total number of requests received")
    lines.append("# TYPE request_count counter")
    lines.append(f"request_count {metrics_state.request_count}")

    lines.append("# HELP error_count Total number of errors")
    lines.append("# TYPE error_count counter")
    lines.append(f"error_count {metrics_state.error_count}")

    lines.append("# HELP endpoint_requests Number of requests per endpoint")
    lines.append("# TYPE endpoint_requests counter")
    for endpoint, count in metrics_state.endpoint_counts.items():
        lines.append(f'endpoint_requests{{endpoint="{endpoint}"}} {count}')

    lines.append("# HELP endpoint_latency_seconds Latency per endpoint in seconds")
    lines.append("# TYPE endpoint_latency_seconds histogram")
    for endpoint, latencies in metrics_state.endpoint_latency.items():
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            lines.append(
                f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="avg"}} {avg_latency}'
            )
            if len(latencies) >= 2:
                sorted_latencies = sorted(latencies)
                p50 = sorted_latencies[len(sorted_latencies) // 2]
                p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
                lines.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50}'
                )
                lines.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95}'
                )
                lines.append(
                    f'endpoint_latency_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99}'
                )

    metrics_payload = MetricsResponse(metrics=tuple(lines))
    return PlainTextResponse(content="\n".join(metrics_payload.metrics))


@router.get(
    "/status",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    tags=["Workflow"],
    summary="Get workflow status",
    description="Get the status of the most recent workflow execution.",
)
async def status_endpoint(
    request: Request, token: None = Depends(verify_token)
) -> WorkflowResponse:
    """Get the status of the most recent workflow execution.

    This endpoint returns the messages from the most recent workflow invocation.

    Args:
        request: The FastAPI request object
        token: Authentication token (injected by FastAPI)

    Returns:
        A response containing messages from the most recent workflow

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Apply rate limiting
    rate_limit(request)

    return WorkflowResponse(messages=get_state().latest_messages)


# Create a FastAPI app with the enhanced router
app = FastAPI(
    title="DevSynth Agent API",
    description="API for interacting with DevSynth workflows",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add exception handlers for common errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return a structured error response."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions and return a structured error response."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_detail(
            "An unexpected error occurred",
            details=str(exc),
            suggestions=(
                "Check the logs for more information",
                "Contact support if the issue persists",
            ),
        ),
    )


# Include the router in the app
app.include_router(router)
