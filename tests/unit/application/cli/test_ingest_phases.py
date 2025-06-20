import pytest
import sys
import types
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.modules.setdefault("typer", types.ModuleType("typer"))

spec = importlib.util.spec_from_file_location(
    "ingest_cmd",
    Path(__file__).parents[4] / "src" / "devsynth" / "application" / "cli" / "ingest_cmd.py",
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

    (src / "main.py").write_text("""def hello():\n    return 42\n""")
    (tests_dir / "test_main.py").write_text(
        """from src.main import hello\n\ndef test_hello():\n    assert hello() == 42\n"""
    )

    manifest = {
        "metadata": {"name": "sample"},
        "structure": {
            "type": "single_package",
            "directories": {"source": ["src"], "tests": ["tests"]},
        },
    }

    return manifest, tmp_path


@pytest.fixture
def mock_bridge():
    ingest_cmd.bridge = MagicMock()
    yield ingest_cmd.bridge


def test_expand_phase(sample_project, monkeypatch, mock_bridge):
    manifest, root = sample_project
    monkeypatch.chdir(root)

    result = expand_phase(manifest, verbose=False)

    assert result["artifacts_discovered"] >= 2
    assert result["files_processed"] == 2
    assert result["analysis_metrics"]["functions"] >= 1


def test_differentiate_phase(sample_project, monkeypatch, mock_bridge):
    manifest, root = sample_project
    monkeypatch.chdir(root)

    expand_res = expand_phase(manifest)
    result = differentiate_phase(manifest, expand_res)

    assert result["gaps_identified"] == 0
    assert result["inconsistencies_found"] == 0


def test_refine_phase(sample_project, monkeypatch, mock_bridge):
    manifest, root = sample_project
    monkeypatch.chdir(root)

    expand_res = expand_phase(manifest)
    diff_res = differentiate_phase(manifest, expand_res)
    result = refine_phase(manifest, diff_res)

    assert "relationships_created" in result
    assert result["relationships_created"] >= 0


def test_retrospect_phase(sample_project, monkeypatch, mock_bridge):
    manifest, root = sample_project
    monkeypatch.chdir(root)

    expand_res = expand_phase(manifest)
    diff_res = differentiate_phase(manifest, expand_res)
    refine_res = refine_phase(manifest, diff_res)
    result = retrospect_phase(manifest, refine_res)

    assert "insights_captured" in result
    assert "improvements_identified" in result
