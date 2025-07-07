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
from typing import Optional, Sequence, List, Dict, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from devsynth.api import verify_token
from devsynth.logging_setup import DevSynthLogger
from devsynth.interface.ux_bridge import (
    UXBridge,
    ProgressIndicator,
    sanitize_output,
)

# Configure logging
logger = DevSynthLogger(__name__)

# Create a router for the API endpoints
router = APIRouter()

# Store the latest messages from the API
LATEST_MESSAGES: List[str] = []

# Store request timestamps for rate limiting
REQUEST_TIMESTAMPS: Dict[str, List[float]] = {}


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
            self, *, advance: float = 1, description: Optional[str] = None
        ) -> None:
            """Update the progress and optionally change the description."""
            self.current += advance
            if description:
                self.description = description
            self.messages.append(
                f"Progress: {self.description} ({self.current}/{self.total})"
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
        example="./my-project"
    )
    project_root: Optional[str] = Field(
        default=None,
        description="Root directory of the project (if different from path)",
        example="src"
    )
    language: Optional[str] = Field(
        default=None,
        description="Primary programming language for the project",
        example="python"
    )
    goals: Optional[str] = Field(
        default=None,
        description="High-level goals or description of the project",
        example="A CLI tool for managing tasks"
    )


class GatherRequest(BaseModel):
    """Request model for gathering project requirements."""
    
    goals: str = Field(
        description="High-level goals or objectives for the project",
        example="Create a web application for tracking expenses"
    )
    constraints: str = Field(
        description="Constraints or limitations for the project",
        example="Must work on mobile devices and support offline mode"
    )
    priority: str = Field(
        default="medium",
        description="Priority level for the requirements (low, medium, high)",
        example="high"
    )


class SynthesizeRequest(BaseModel):
    """Request model for synthesizing code from requirements."""
    
    target: Optional[str] = Field(
        default=None,
        description="Target component to synthesize (e.g., 'unit', 'integration')",
        example="unit"
    )


class SpecRequest(BaseModel):
    """Request model for generating specifications from requirements."""
    
    requirements_file: str = Field(
        default="requirements.md",
        description="Path to the requirements file",
        example="docs/requirements.md"
    )


class TestRequest(BaseModel):
    """Request model for generating tests from specifications."""
    
    spec_file: str = Field(
        default="specs.md",
        description="Path to the specifications file",
        example="docs/specs.md"
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Directory where the tests will be generated",
        example="tests"
    )


class CodeRequest(BaseModel):
    """Request model for generating code from tests."""
    
    output_dir: Optional[str] = Field(
        default=None,
        description="Directory where the code will be generated",
        example="src"
    )


class DoctorRequest(BaseModel):
    """Request model for running diagnostics on a project."""
    
    path: str = Field(
        default=".",
        description="Path to the project directory",
        example="./my-project"
    )
    fix: bool = Field(
        default=False,
        description="Whether to automatically fix issues",
        example=True
    )


class EDRRCycleRequest(BaseModel):
    """Request model for running an EDRR cycle."""
    
    prompt: str = Field(
        description="Prompt for the EDRR cycle",
        example="Improve the error handling in the API endpoints"
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context for the EDRR cycle",
        example="Focus on providing more informative error messages"
    )
    max_iterations: int = Field(
        default=3,
        description="Maximum number of iterations for the EDRR cycle",
        example=5
    )


class WorkflowResponse(BaseModel):
    """Response model for all workflow endpoints."""
    
    messages: List[str] = Field(
        description="Messages generated during the workflow execution",
        example=["Initializing project...", "Project initialized successfully"]
    )


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    
    error: str = Field(
        description="Error message",
        example="Failed to initialize project: File not found"
    )
    details: Optional[str] = Field(
        default=None,
        description="Additional details about the error",
        example="The specified path does not exist"
    )
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for resolving the error",
        example=["Create the directory before initializing", "Check the path and try again"]
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
            detail=f"Rate limit exceeded. Try again in {window} seconds."
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
    description="Initialize or onboard a project with the specified parameters."
)
async def init_endpoint(
    request: Request,
    init_request: InitRequest,
    token: None = Depends(verify_token)
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
                        "Check the path and try again"
                    ]
                }
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
                        "Provide the correct file path"
                    ]
                }
            )
        elif isinstance(e, PermissionError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": f"Permission denied: {str(e)}",
                    "suggestions": [
                        "Check file permissions",
                        "Run the command with appropriate permissions"
                    ]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": f"Failed to initialize project: {str(e)}",
                    "details": str(e),
                    "suggestions": [
                        "Check the logs for more information",
                        "Try again with different parameters"
                    ]
                }
            )


# Add similar enhancements to other endpoints...


@router.get(
    "/status",
    response_model=WorkflowResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    tags=["Workflow"],
    summary="Get workflow status",
    description="Get the status of the most recent workflow execution."
)
async def status_endpoint(
    request: Request,
    token: None = Depends(verify_token)
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
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

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
                "Contact support if the issue persists"
            ]
        }
    )

# Include the router in the app
app.include_router(router)