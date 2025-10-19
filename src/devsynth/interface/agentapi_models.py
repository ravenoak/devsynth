"""Shared request/response models for the DevSynth Agent API.

The original ``agentapi`` and ``agentapi_enhanced`` modules both defined
nearly identical Pydantic models.  Consolidating them into this module keeps
the HTTP surface area consistent between the two routers and provides a single
location for field validation, enum definitions, and typed payloads shared by
the FastAPI handlers and service layer.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, assert_type

from pydantic import BaseModel, Field, conint


class PriorityLevel(str, Enum):
    """Supported priority levels for the gather workflow."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SynthesisTarget(str, Enum):
    """Valid synthesis pipeline targets exposed by the CLI."""

    UNIT = "unit"
    UNIT_TESTS = "unit-tests"
    INTEGRATION = "integration"
    INTEGRATION_TESTS = "integration-tests"
    BEHAVIOR = "behavior"
    BEHAVIOR_TESTS = "behavior-tests"
    ALL = "all"


class ProgressStatus(str, Enum):
    """Discrete progress states surfaced to API consumers."""

    STARTING = "Starting..."
    PROCESSING = "Processing..."
    HALF_COMPLETE = "Halfway there..."
    ALMOST_DONE = "Almost done..."
    FINALIZING = "Finalizing..."
    COMPLETE = "Complete"


class ProgressSnapshot(BaseModel):
    """Structured representation of a progress indicator update."""

    __test__ = False

    description: str = Field(..., min_length=1, max_length=1024)
    current: float = Field(..., ge=0)
    total: float = Field(..., gt=0)
    status: ProgressStatus = Field(default=ProgressStatus.STARTING)


class WorkflowMetadata(BaseModel):
    """Optional metadata returned with workflow responses."""

    __test__ = False

    started_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    progress: tuple[ProgressSnapshot, ...] = Field(default_factory=tuple)


class InitRequest(BaseModel):
    __test__ = False

    path: str = Field(".", min_length=1)
    project_root: str | None = Field(default=None, min_length=1)
    language: str | None = Field(default=None, min_length=1)
    goals: str | None = Field(default=None, min_length=1)


class GatherRequest(BaseModel):
    __test__ = False

    goals: str = Field(..., min_length=1)
    constraints: str | None = Field(default=None, min_length=1)
    priority: PriorityLevel = PriorityLevel.MEDIUM


class SynthesizeRequest(BaseModel):
    __test__ = False

    target: SynthesisTarget


class SpecRequest(BaseModel):
    __test__ = False

    requirements_file: str = Field("requirements.md", min_length=1)


class TestSpecRequest(BaseModel):
    __test__ = False

    spec_file: str = Field(..., min_length=1)
    output_dir: str | None = Field(default=None, min_length=1)


class CodeRequest(BaseModel):
    __test__ = False

    output_dir: str | None = Field(default=None, min_length=1)


class DoctorRequest(BaseModel):
    __test__ = False

    path: str = Field(".", min_length=1)
    fix: bool = False


class EDRRCycleRequest(BaseModel):
    __test__ = False

    prompt: str = Field(..., min_length=1)
    context: str | None = Field(default=None, min_length=1)
    max_iterations: int = Field(3, ge=1, le=50)


class WorkflowResponse(BaseModel):
    __test__ = False

    messages: tuple[str, ...] = Field(default_factory=tuple)
    metadata: WorkflowMetadata | None = None


class EndpointMetrics(BaseModel):
    """Metrics collected for a single API endpoint."""

    __test__ = False

    count: int = 0
    latencies: tuple[float, ...] = Field(default_factory=tuple)


class APIMetrics(BaseModel):
    """Aggregated metrics exposed by the Agent API."""

    __test__ = False

    start_time: float = Field(..., ge=0)
    request_count: int = Field(0, ge=0)
    error_count: int = Field(0, ge=0)
    endpoint_counts: dict[str, int] = Field(default_factory=dict)
    endpoint_latency: dict[str, tuple[float, ...]] = Field(default_factory=dict)

    def record_latency(self, endpoint: str, latency: float) -> None:
        """Store a latency measurement for an endpoint."""

        if latency < 0:
            return
        latencies = list(self.endpoint_latency.get(endpoint, tuple()))
        latencies.append(latency)
        self.endpoint_latency[endpoint] = tuple(latencies)


class MetricsResponse(BaseModel):
    """Prometheus-style metrics payload."""

    __test__ = False

    metrics: tuple[str, ...]


class HealthResponse(BaseModel):
    """Simple health-check payload."""

    __test__ = False

    status: str = Field(..., min_length=1)
    uptime: float = Field(..., ge=0)
    additional_info: Mapping[str, str] | None = None


if TYPE_CHECKING:
    _metrics = APIMetrics(start_time=0.0)
    assert_type(_metrics.endpoint_counts, dict[str, int])
    assert_type(_metrics.endpoint_latency, dict[str, tuple[float, ...]])
