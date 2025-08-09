"""Enhanced Agent API with improved error handling, documentation, and security.

This module extends the existing Agent API with:
1. More specific error handling for different types of errors
2. More informative error messages that provide guidance on how to fix issues
3. Better logging that includes more context about requests and errors
4. Detailed docstrings and examples for OpenAPI documentation
5. Rate limiting to prevent abuse
"""

from __future__ import annotations

import datetime
import os
import time
from typing import Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from devsynth.api import verify_token
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge, sanitize_output
from devsynth.logging_setup import DevSynthLogger

# Configure logging
logger = DevSynthLogger(__name__)

# Create a router for the API endpoints
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


class APIBridge(UXBridge):
    """Bridge for API interactions that captures all messages."""

    def __init__(self, answers: Optional[Sequence[str]] = None) -> None:
        """Initialize with optional pre-defined answers for questions."""
        self.messages: List[str] = []
        self._answers = list(answers or [])

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Return the next pre-defined answer or a default."""
        self.messages.append(sanitize_output(message))
        if self._answers:
            return self._answers.pop(0)
        return default or (choices[0] if choices else "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Return the next pre-defined answer as a boolean or the default."""
        self.messages.append(sanitize_output(message))
        if self._answers:
            answer = self._answers.pop(0)
            return answer.lower() in ("y", "yes", "true", "1")
        return default

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Capture the message for later retrieval."""
        self.messages.append(sanitize_output(message))

    class _APIProgress(ProgressIndicator):
        """Progress indicator that captures progress updates."""

        def __init__(self, messages: List[str], description: str, total: int) -> None:
            """Initialize with a message list, description, and total steps."""
            self.messages = messages
            self.description = description
            self.total = total
            self.current = 0
            self.subtasks: Dict[str, Dict[str, Any]] = {}
            self.messages.append(f"Starting: {description} (0/{total})")

        def update(
            self,
            *,
            advance: float = 1,
            description: Optional[str] = None,
            status: Optional[str] = None,
        ) -> None:
            """Update the progress and optionally change the description."""
            self.current += advance
            if description:
                self.description = description
            if status is None:
                if self.current >= self.total:
                    status = "Complete"
                elif self.current >= 0.99 * self.total:
                    status = "Finalizing..."
                elif self.current >= 0.75 * self.total:
                    status = "Almost done..."
                elif self.current >= 0.5 * self.total:
                    status = "Halfway there..."
                elif self.current >= 0.25 * self.total:
                    status = "Processing..."
                else:
                    status = "Starting..."
            self.messages.append(
                f"Progress: {self.description} ({self.current}/{self.total}) - {status}"
            )

        def complete(self) -> None:
            """Mark the progress as complete."""
            self.current = self.total
            self.messages.append(f"Completed: {self.description}")

        def add_subtask(self, description: str, total: int = 100) -> str:
            """Add a subtask with its own progress tracking."""
            task_id = f"subtask_{len(self.subtasks)}"
            self.subtasks[task_id] = {
                "description": description,
                "total": total,
                "current": 0,
            }
            self.messages.append(f"Subtask started: {description} (0/{total})")
            return task_id

        def update_subtask(
            self, task_id: str, advance: float = 1, description: Optional[str] = None
        ) -> None:
            """Update a subtask's progress."""
            if task_id not in self.subtasks:
                raise ValueError(f"Unknown subtask ID: {task_id}")

            subtask = self.subtasks[task_id]
            subtask["current"] += advance
            if description:
                subtask["description"] = description

            self.messages.append(
                f"Subtask progress: {subtask['description']} ({subtask['current']}/{subtask['total']})"
            )

        def complete_subtask(self, task_id: str) -> None:
            """Mark a subtask as complete."""
            if task_id not in self.subtasks:
                raise ValueError(f"Unknown subtask ID: {task_id}")

            subtask = self.subtasks[task_id]
            subtask["current"] = subtask["total"]
            self.messages.append(f"Subtask completed: {subtask['description']}")

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator with the given description and total steps."""
        return self._APIProgress(self.messages, sanitize_output(description), total)


class InitRequest(BaseModel):
    """Request model for initializing a project."""

    path: str = Field(
        default=".",
        description="Path where the project will be initialized",
        example="./my-project",
    )
    project_root: Optional[str] = Field(
        default=None,
        description="Root directory of the project (if different from path)",
        example="src",
    )
    language: Optional[str] = Field(
        default=None,
        description="Primary programming language for the project",
        example="python",
    )
    goals: Optional[str] = Field(
        default=None,
        description="High-level goals or description of the project",
        example="A CLI tool for managing tasks",
    )


class GatherRequest(BaseModel):
    """Request model for gathering project requirements."""

    goals: str = Field(
        description="High-level goals or objectives for the project",
        example="Create a web application for tracking expenses",
    )
    constraints: str = Field(
        description="Constraints or limitations for the project",
        example="Must work on mobile devices and support offline mode",
    )
    priority: str = Field(
        default="medium",
        description="Priority level for the requirements (low, medium, high)",
        example="high",
    )


class SynthesizeRequest(BaseModel):
    """Request model for synthesizing code from requirements."""

    target: Optional[str] = Field(
        default=None,
        description="Target component to synthesize (e.g., 'unit', 'integration')",
        example="unit",
    )


class SpecRequest(BaseModel):
    """Request model for generating specifications from requirements."""

    requirements_file: str = Field(
        default="requirements.md",
        description="Path to the requirements file",
        example="docs/requirements.md",
    )


class TestRequest(BaseModel):
    """Request model for generating tests from specifications."""

    spec_file: str = Field(
        default="specs.md",
        description="Path to the specifications file",
        example="docs/specs.md",
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Directory where the tests will be generated",
        example="tests",
    )

    # Prevent pytest from collecting this Pydantic model as a test class
    __test__ = False


class CodeRequest(BaseModel):
    """Request model for generating code from tests."""

    output_dir: Optional[str] = Field(
        default=None,
        description="Directory where the code will be generated",
        example="src",
    )


class DoctorRequest(BaseModel):
    """Request model for running diagnostics on a project."""

    path: str = Field(
        default=".", description="Path to the project directory", example="./my-project"
    )
    fix: bool = Field(
        default=False, description="Whether to automatically fix issues", example=True
    )


class EDRRCycleRequest(BaseModel):
    """Request model for running an EDRR cycle."""

    prompt: str = Field(
        description="Prompt for the EDRR cycle",
        example="Improve the error handling in the API endpoints",
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context for the EDRR cycle",
        example="Focus on providing more informative error messages",
    )
    max_iterations: int = Field(
        default=3,
        description="Maximum number of iterations for the EDRR cycle",
        example=5,
    )


class WorkflowResponse(BaseModel):
    """Response model for all workflow endpoints."""

    messages: List[str] = Field(
        description="Messages generated during the workflow execution",
        example=["Initializing project...", "Project initialized successfully"],
    )


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: str = Field(
        description="Error message",
        example="Failed to initialize project: File not found",
    )
    details: Optional[str] = Field(
        default=None,
        description="Additional details about the error",
        example="The specified path does not exist",
    )
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for resolving the error",
        example=[
            "Create the directory before initializing",
            "Check the path and try again",
        ],
    )


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
                detail={
                    "error": f"Path not found: {init_request.path}",
                    "suggestions": [
                        "Create the directory before initializing",
                        "Check the path and try again",
                    ],
                },
            )

        init_cmd(
            path=init_request.path,
            project_root=init_request.project_root,
            language=init_request.language,
            goals=init_request.goals,
            bridge=bridge,
        )
        LATEST_MESSAGES[:] = bridge.messages
        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in init endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to initialize project: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["gather"] = (
        API_METRICS["endpoint_counts"].get("gather", 0) + 1
    )

    try:
        answers = [
            gather_request.goals,
            gather_request.constraints,
            gather_request.priority,
        ]
        bridge = APIBridge(answers)
        from devsynth.application.cli import gather_cmd

        # Validate priority
        if gather_request.priority.lower() not in ["low", "medium", "high"]:
            logger.error(f"Invalid priority: {gather_request.priority}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid priority: {gather_request.priority}",
                    "suggestions": [
                        "Use 'low', 'medium', or 'high' for priority",
                    ],
                },
            )

        gather_cmd(bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "gather" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["gather"] = []
        API_METRICS["endpoint_latency"]["gather"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in gather endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid input: {str(e)}",
                    "suggestions": [
                        "Check the input values",
                        "Ensure all required fields are provided",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to gather requirements: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["synthesize"] = (
        API_METRICS["endpoint_counts"].get("synthesize", 0) + 1
    )

    try:
        bridge = APIBridge()
        from devsynth.application.cli import run_pipeline_cmd

        # Validate target if provided
        if synthesize_request.target and synthesize_request.target not in [
            "unit",
            "integration",
            "behavior",
        ]:
            logger.error(f"Invalid target: {synthesize_request.target}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid target: {synthesize_request.target}",
                    "suggestions": [
                        "Use 'unit', 'integration', or 'behavior' for target",
                        "Omit target to run all tests",
                    ],
                },
            )

        run_pipeline_cmd(target=synthesize_request.target, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "synthesize" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["synthesize"] = []
        API_METRICS["endpoint_latency"]["synthesize"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in synthesize endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to run synthesis pipeline: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["spec"] = (
        API_METRICS["endpoint_counts"].get("spec", 0) + 1
    )

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
                detail={
                    "error": f"Requirements file not found: {spec_request.requirements_file}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )

        spec_cmd(requirements_file=spec_request.requirements_file, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "spec" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["spec"] = []
        API_METRICS["endpoint_latency"]["spec"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in spec endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to generate specifications: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    request: Request, test_request: TestRequest, token: None = Depends(verify_token)
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["test"] = (
        API_METRICS["endpoint_counts"].get("test", 0) + 1
    )

    try:
        bridge = APIBridge()
        from devsynth.application.cli import test_cmd

        # Check if the spec file exists
        if not os.path.exists(test_request.spec_file):
            logger.error(f"Spec file not found: {test_request.spec_file}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Spec file not found: {test_request.spec_file}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )

        # Check if the output directory exists if provided
        if test_request.output_dir and not os.path.exists(test_request.output_dir):
            logger.error(f"Output directory not found: {test_request.output_dir}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Output directory not found: {test_request.output_dir}",
                    "suggestions": [
                        "Create the directory before generating tests",
                        "Provide the correct directory path",
                    ],
                },
            )

        test_cmd(
            spec_file=test_request.spec_file,
            output_dir=test_request.output_dir,
            bridge=bridge,
        )
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "test" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["test"] = []
        API_METRICS["endpoint_latency"]["test"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in test endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to generate tests: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["code"] = (
        API_METRICS["endpoint_counts"].get("code", 0) + 1
    )

    try:
        bridge = APIBridge()
        from devsynth.application.cli import code_cmd

        # Check if the output directory exists if provided
        if code_request.output_dir and not os.path.exists(code_request.output_dir):
            logger.error(f"Output directory not found: {code_request.output_dir}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Output directory not found: {code_request.output_dir}",
                    "suggestions": [
                        "Create the directory before generating code",
                        "Provide the correct directory path",
                    ],
                },
            )

        code_cmd(output_dir=code_request.output_dir, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "code" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["code"] = []
        API_METRICS["endpoint_latency"]["code"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in code endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to generate code: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["doctor"] = (
        API_METRICS["endpoint_counts"].get("doctor", 0) + 1
    )

    try:
        bridge = APIBridge()
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        # Check if the path exists
        if not os.path.exists(doctor_request.path):
            logger.error(f"Path not found: {doctor_request.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Path not found: {doctor_request.path}",
                    "suggestions": [
                        "Check that the directory exists",
                        "Provide the correct directory path",
                    ],
                },
            )

        doctor_cmd(path=doctor_request.path, fix=doctor_request.fix, bridge=bridge)
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "doctor" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["doctor"] = []
        API_METRICS["endpoint_latency"]["doctor"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in doctor endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, FileNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"File not found: {str(e)}",
                    "suggestions": [
                        "Check that the file exists",
                        "Provide the correct file path",
                    ],
                },
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to run diagnostics: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["edrr-cycle"] = (
        API_METRICS["endpoint_counts"].get("edrr-cycle", 0) + 1
    )

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
                detail={
                    "error": f"Invalid max_iterations: {edrr_cycle_request.max_iterations}",
                    "suggestions": [
                        "Use a value between 1 and 10 for max_iterations",
                    ],
                },
            )

        edrr_cycle_cmd(
            prompt=edrr_cycle_request.prompt,
            context=edrr_cycle_request.context,
            max_iterations=edrr_cycle_request.max_iterations,
            bridge=bridge,
        )
        LATEST_MESSAGES[:] = bridge.messages

        # Update latency metrics
        latency = time.time() - start_time
        if "edrr-cycle" not in API_METRICS["endpoint_latency"]:
            API_METRICS["endpoint_latency"]["edrr-cycle"] = []
        API_METRICS["endpoint_latency"]["edrr-cycle"].append(latency)

        return WorkflowResponse(messages=bridge.messages)
    except HTTPException:
        # Re-raise HTTP exceptions
        API_METRICS["error_count"] += 1
        raise
    except Exception as e:
        API_METRICS["error_count"] += 1
        logger.error(f"Error in edrr-cycle endpoint: {str(e)}", exc_info=True)

        # Provide more specific error messages based on the exception type
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid input: {str(e)}",
                    "suggestions": [
                        "Check the input values",
                        "Ensure all required fields are provided",
                    ],
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to run EDRR cycle: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters",
                    ],
                },
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
    API_METRICS["request_count"] += 1
    API_METRICS["endpoint_counts"]["health"] = (
        API_METRICS["endpoint_counts"].get("health", 0) + 1
    )

    return JSONResponse(content={"status": "ok"})


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

    return WorkflowResponse(messages=LATEST_MESSAGES)


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
        content={
            "error": "An unexpected error occurred",
            "details": str(exc),
            "suggestions": [
                "Check the logs for more information",
                "Contact support if the issue persists",
            ],
        },
    )


# Include the router in the app
app.include_router(router)
