import pytest

from devsynth.domain.models.project import Artifact, ProjectModel, ProjectStructureType


@pytest.mark.fast
def test_project_model_structure_type_default_standard(tmp_path):
    """ReqID: PROJECT-STRUCTURE-01 — defaults to STANDARD when unspecified."""
    model = ProjectModel(tmp_path, {})
    assert model.structure_type == ProjectStructureType.STANDARD


@pytest.mark.fast
def test_project_model_structure_type_monorepo(tmp_path):
    """ReqID: PROJECT-STRUCTURE-02 — recognizes monorepo manifest type."""
    manifest = {"structure": {"type": "monorepo"}}
    model = ProjectModel(tmp_path, manifest)
    assert model.structure_type == ProjectStructureType.MONOREPO


@pytest.mark.fast
def test_artifact_metadata_defaults_to_separate_dicts():
    """ReqID: PROJECT-ARTIFACT-01 — metadata defaults to a unique dict."""
    a1 = Artifact("/a")
    a2 = Artifact("/b")
    a1.metadata["x"] = 1
    assert a2.metadata == {}
