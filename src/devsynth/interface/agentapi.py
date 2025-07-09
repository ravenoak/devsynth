"""FastAPI wrapper exposing core workflows.

This module provides a minimal HTTP interface that mirrors the CLI and
WebUI workflows via the :class:`UXBridge` abstraction. Each route
forwards request data to the existing workflow functions and captures
any output generated through the bridge. Responses contain those
messages so API clients receive the same feedback normally shown in
the terminal or WebUI.
"""

from __future__ import annotations

from typing import Optional, Sequence, List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from devsynth.api import verify_token
from devsynth.logging_setup import DevSynthLogger
from devsynth.interface.ux_bridge import (
    UXBridge,
    ProgressIndicator,
    sanitize_output,
)

logger = DevSynthLogger(__name__)
router = APIRouter()
app = FastAPI(
    title="DevSynth Agent API",
    description="HTTP API for driving DevSynth workflows programmatically",
    version="0.1.0",
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

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Capture workflow output for the API response."""
        self.messages.append(sanitize_output(message))

    class _APIProgress(ProgressIndicator):
        def __init__(self, messages: List[str], description: str, total: int) -> None:
            self._messages = messages
            self._description = sanitize_output(description)
            self._total = total
            self._current = 0
            self._messages.append(self._description)

        def update(
            self, *, advance: float = 1, description: Optional[str] = None
        ) -> None:
            if description:
                self._description = sanitize_output(description)
            self._current += advance
            self._messages.append(
                f"{self._description} ({self._current}/{self._total})"
            )

        def complete(self) -> None:
            self._messages.append(f"{self._description} complete")

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return self._APIProgress(self.messages, description, total)


LATEST_MESSAGES: List[str] = []


class InitRequest(BaseModel):
    path: str = "."
    project_root: Optional[str] = None
    language: Optional[str] = None
    goals: Optional[str] = None


class GatherRequest(BaseModel):
    goals: str
    constraints: str
    priority: str = "medium"


class SynthesizeRequest(BaseModel):
    target: Optional[str] = None


class SpecRequest(BaseModel):
    requirements_file: str = "requirements.md"


class TestSpecRequest(BaseModel):
    spec_file: str = "specs.md"
    output_dir: Optional[str] = None


class CodeRequest(BaseModel):
    output_dir: Optional[str] = None


class DoctorRequest(BaseModel):
    path: str = "."
    fix: bool = False


class EDRRCycleRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    max_iterations: int = 3


class WorkflowResponse(BaseModel):
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
            prompt=prompt, context=context, max_iterations=max_iterations, bridge=self.bridge
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

        test_cmd(spec_file=request.spec_file, output_dir=request.output_dir, bridge=bridge)
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
