import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli.ingest_models import (
    DifferentiationPhaseResult,
    ExpandPhaseResult,
    ManifestModel,
    RefinePhaseResult,
    RetrospectPhaseResult,
)

sys.modules.setdefault("typer", types.ModuleType("typer"))
spec = importlib.util.spec_from_file_location(
    "ingest_cmd",
    Path(__file__).parents[4]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "ingest_cmd.py",
)
ingest_cmd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_cmd)
expand_phase = ingest_cmd.expand_phase
differentiate_phase = ingest_cmd.differentiate_phase
refine_phase = ingest_cmd.refine_phase
retrospect_phase = ingest_cmd.retrospect_phase


@pytest.fixture
def sample_project(tmp_path):
    src = tmp_path / "src"
    tests_dir = tmp_path / "tests"
    src.mkdir()
    tests_dir.mkdir()
    (src / "main.py").write_text("def hello():\n    return 42\n")
    (tests_dir / "test_main.py").write_text(
        "from src.main import hello\n\ndef test_hello():\n    assert hello() == 42\n"
    )
    manifest: ManifestModel = {
        "metadata": {"name": "sample"},
        "structure": {
            "type": "single_package",
            "directories": {"source": ["src"], "tests": ["tests"]},
        },
    }
    return (manifest, tmp_path)


@pytest.fixture
def mock_bridge():
    ingest_cmd.bridge = MagicMock()
    yield ingest_cmd.bridge


@pytest.fixture
def mock_memory_manager():
    with patch.object(ingest_cmd, "MemoryManager") as cls:
        inst = MagicMock()
        cls.return_value = inst
        yield inst


@pytest.mark.medium
def test_expand_phase_succeeds(
    sample_project, monkeypatch, mock_bridge, mock_memory_manager
):
    """Test that expand phase succeeds.

    ReqID: N/A"""
    manifest, root = sample_project
    monkeypatch.chdir(root)
    result: ExpandPhaseResult = expand_phase(manifest, verbose=False)
    assert result["artifacts_discovered"] >= 2
    assert result["files_processed"] == 2
    assert result["analysis_metrics"]["functions"] >= 1
    assert isinstance(result["analysis_metrics"]["lines_of_code"], int)
    mock_memory_manager.store_with_edrr_phase.assert_called_once()


@pytest.mark.medium
def test_differentiate_phase_succeeds(
    sample_project, monkeypatch, mock_bridge, mock_memory_manager
):
    """Test that differentiate phase succeeds.

    ReqID: N/A"""
    manifest, root = sample_project
    monkeypatch.chdir(root)
    expand_res: ExpandPhaseResult = expand_phase(manifest)
    mock_memory_manager.reset_mock()
    result: DifferentiationPhaseResult = differentiate_phase(manifest, expand_res)
    assert result["gaps_identified"] == 0
    assert result["inconsistencies_found"] == 0
    assert isinstance(result["missing"], list)
    mock_memory_manager.store_with_edrr_phase.assert_called_once()


@pytest.mark.medium
def test_refine_phase_succeeds(
    sample_project, monkeypatch, mock_bridge, mock_memory_manager
):
    """Test that refine phase succeeds.

    ReqID: N/A"""
    manifest, root = sample_project
    monkeypatch.chdir(root)
    expand_res = expand_phase(manifest)
    diff_res: DifferentiationPhaseResult = differentiate_phase(manifest, expand_res)
    mock_memory_manager.reset_mock()
    result: RefinePhaseResult = refine_phase(manifest, diff_res)
    assert "relationships_created" in result
    assert result["relationships_created"] >= 0
    assert "quality_checks" in result
    mock_memory_manager.store_with_edrr_phase.assert_called_once()


@pytest.mark.medium
def test_retrospect_phase_succeeds(
    sample_project, monkeypatch, mock_bridge, mock_memory_manager
):
    """Test that retrospect phase succeeds.

    ReqID: N/A"""
    manifest, root = sample_project
    monkeypatch.chdir(root)
    expand_res = expand_phase(manifest)
    diff_res = differentiate_phase(manifest, expand_res)
    refine_res: RefinePhaseResult = refine_phase(manifest, diff_res)
    mock_memory_manager.reset_mock()
    result: RetrospectPhaseResult = retrospect_phase(manifest, refine_res)
    assert "insights_captured" in result
    assert "improvements_identified" in result
    assert isinstance(result["duration_seconds"], int)
    mock_memory_manager.store_with_edrr_phase.assert_called_once()
