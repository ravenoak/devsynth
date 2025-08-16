import networkx as nx
import pytest

from devsynth.application.ingestion import IngestionMetrics, ProjectStructureType
from devsynth.application.ingestion.phases import (
    run_differentiate_phase,
    run_expand_phase,
)


class DummyIngestion:
    def __init__(self, project_root):
        self.project_root = project_root
        self.manifest_path = project_root / "manifest.yaml"
        self.metrics = IngestionMetrics()
        self.project_graph = nx.DiGraph()
        self.manifest_data = {}
        self.artifacts = {}
        self.project_structure = ProjectStructureType.STANDARD
        self.previous_state = None
        self.validated = False

    # Helpers required by phase functions
    def _validate_standard_structure(
        self, verbose: bool
    ):  # pragma: no cover - simple flag
        self.validated = True

    def _validate_monorepo_structure(self, verbose: bool):  # pragma: no cover
        pass

    def _validate_federated_structure(self, verbose: bool):  # pragma: no cover
        pass

    def _validate_custom_structure(self, verbose: bool):  # pragma: no cover
        pass

    def _check_code_test_consistency(self, verbose: bool):  # pragma: no cover
        pass

    def _update_artifact_statuses(self, verbose: bool):  # pragma: no cover
        pass

    def _resolve_conflicts(self, verbose: bool):  # pragma: no cover
        pass

    def _enrich_artifact_metadata(self, verbose: bool):  # pragma: no cover
        pass

    def _identify_relationships(self, verbose: bool):  # pragma: no cover
        pass

    def _save_refined_data(self, data, verbose: bool):  # pragma: no cover
        pass

    def _evaluate_ingestion_process(self, verbose: bool):  # pragma: no cover
        return {}

    def _identify_improvement_areas(self, verbose: bool):  # pragma: no cover
        return []

    def _generate_recommendations(self, verbose: bool):  # pragma: no cover
        return []

    def _save_retrospective(self, data, verbose: bool):  # pragma: no cover
        pass


@pytest.mark.fast
def test_run_expand_phase_populates_artifacts(monkeypatch, tmp_path):
    class DummyProjectModel:
        def __init__(self, root, manifest):
            pass

        def build_model(self):
            pass

        def to_dict(self):
            return {
                "artifacts": {"a": {"type": "CODE", "metadata": {}}},
                "relationships": [],
            }

    monkeypatch.setattr(
        "devsynth.domain.models.project.ProjectModel", DummyProjectModel
    )
    ingestion = DummyIngestion(tmp_path)
    run_expand_phase(ingestion, dry_run=True, verbose=False)
    assert ingestion.artifacts
    assert ingestion.metrics.artifacts_discovered == 1


@pytest.mark.fast
def test_run_differentiate_phase_uses_structure(monkeypatch, tmp_path):
    ingestion = DummyIngestion(tmp_path)
    run_differentiate_phase(ingestion, dry_run=True, verbose=False)
    assert ingestion.validated
