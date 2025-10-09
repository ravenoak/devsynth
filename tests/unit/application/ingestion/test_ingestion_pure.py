"""Unit tests for pure helpers in the ingestion module."""

import pytest

from devsynth.application.ingestion import (
    ArtifactStatus,
    ArtifactType,
    Ingestion,
    IngestionMetrics,
    IngestionPhase,
    ProjectStructureType,
)

pytestmark = pytest.mark.fast


def _fresh_metrics() -> IngestionMetrics:
    """Create metrics with deterministic timestamps for assertions."""

    metrics = IngestionMetrics()
    # Stabilise timestamps for reproducibility in assertions that inspect metadata.
    metrics.start_time = 0.0
    metrics.phase_durations = {phase: 0.0 for phase in IngestionPhase}
    metrics.artifacts_by_type = {atype: 0 for atype in ArtifactType}
    metrics.artifacts_by_status = {status: 0 for status in ArtifactStatus}
    return metrics


def test_is_artifact_changed_respects_metadata_differences() -> None:
    """``_is_artifact_changed`` compares metadata dictionaries only.

    ReqID: N/A
    """

    ingestion = object.__new__(Ingestion)

    current = {"metadata": {"hash": "abc"}}
    previous = {"metadata": {"hash": "def"}}
    unchanged = {"metadata": {"hash": "abc"}}

    assert ingestion._is_artifact_changed(current, previous) is True
    assert ingestion._is_artifact_changed(current, unchanged) is False
    assert ingestion._is_artifact_changed({}, {}) is False


def test_identify_improvement_areas_flags_missing_manifest_information() -> None:
    """The helper highlights absent manifest data and weak coverage.

    ReqID: N/A
    """

    ingestion = object.__new__(Ingestion)
    ingestion.manifest_data = {
        "structure": {
            "directories": {},
        }
    }
    ingestion.metrics = _fresh_metrics()
    ingestion.metrics.artifacts_by_type[ArtifactType.CODE] = 4
    ingestion.metrics.artifacts_by_type[ArtifactType.TEST] = 1
    ingestion.metrics.artifacts_by_type[ArtifactType.DOCUMENTATION] = 0
    ingestion.metrics.phase_durations[IngestionPhase.REFINE] = 6.2

    improvements = ingestion._identify_improvement_areas(verbose=False)

    def _has(area: str, issue: str) -> bool:
        return any(
            entry["area"] == area and entry["issue"] == issue for entry in improvements
        )

    assert _has("Project Configuration", "Missing project name")
    assert _has("Project Configuration", "Missing version")
    assert _has("Project Structure", "No source directories specified")
    assert _has("Testing", "Low test coverage")
    assert _has("Documentation", "No documentation artifacts found")
    assert _has(
        "Performance",
        "Slow REFINE phase (6.20 seconds)",
    )


def test_generate_recommendations_reflects_project_context() -> None:
    """Recommendations combine structure, type counts, and statuses.

    ReqID: N/A
    """

    ingestion = object.__new__(Ingestion)
    ingestion.project_structure = ProjectStructureType.MONOREPO
    ingestion.metrics = _fresh_metrics()
    ingestion.metrics.artifacts_by_type[ArtifactType.CONFIGURATION] = 11
    ingestion.metrics.artifacts_by_status[ArtifactStatus.DEPRECATED] = 2

    recommendations = ingestion._generate_recommendations(verbose=False)

    texts = {
        (entry["category"], entry["recommendation"], entry.get("priority"))
        for entry in recommendations
    }

    assert (
        "Project Structure",
        "Consider using a monorepo management tool like Lerna or Nx",
        "Medium",
    ) in texts
    assert (
        "Configuration",
        "Consider consolidating configuration files to reduce complexity",
        "Medium",
    ) in texts
    assert (
        "Code Cleanup",
        "Remove deprecated artifacts to reduce technical debt",
        "High",
    ) in texts
    assert (
        "Project Configuration",
        "Keep .devsynth/project.yaml updated as the project evolves",
        "High",
    ) in texts
    assert (
        "Process",
        "Run ingestion regularly to keep project model up to date",
        "Medium",
    ) in texts
