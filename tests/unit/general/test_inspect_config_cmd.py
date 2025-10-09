"""Tests for the inspect_config_cmd CLI command."""

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
import yaml

from devsynth.application.cli.commands.inspect_config_cmd import (
    analyze_project_structure,
    compare_with_manifest,
    inspect_config_cmd,
    update_manifest,
)
from devsynth.application.cli.ingest_models import (
    ManifestModel,
    ProjectStructureReport,
    StructureDifference,
)


@patch("devsynth.application.cli.commands.inspect_config_cmd.bridge")
@patch("devsynth.application.cli.commands.inspect_config_cmd.analyze_project_structure")
@patch("devsynth.application.cli.commands.inspect_config_cmd.compare_with_manifest")
@patch("devsynth.application.cli.commands.inspect_config_cmd.update_manifest")
@patch("yaml.dump")
@pytest.mark.fast
def test_inspect_config_update_succeeds(
    mock_dump, mock_update, mock_compare, mock_analyze, mock_bridge, tmp_path
):
    """Test that inspect config update succeeds.

    ReqID: N/A"""
    manifest_path = tmp_path / "devsynth.yaml"
    yaml.safe_dump({"projectName": "Test"}, manifest_path.open("w"))
    mock_analyze.return_value = cast(
        ProjectStructureReport,
        {"directories": {"source": [], "tests": [], "docs": []}, "files": []},
    )
    mock_compare.return_value = [
        cast(
            StructureDifference,
            {"type": "source", "path": "src", "status": "missing in manifest"},
        )
    ]
    mock_update.return_value = cast(ManifestModel, {"projectName": "Updated"})
    inspect_config_cmd(path=str(tmp_path), update=True)
    mock_analyze.assert_called_once_with(Path(str(tmp_path)))
    mock_compare.assert_called_once()
    mock_update.assert_called_once()
    mock_dump.assert_called_once()
    assert any(
        "Configuration updated successfully" in str(call.args[0])
        for call in mock_bridge.print.call_args_list
    )


@patch("devsynth.application.cli.commands.inspect_config_cmd.bridge")
@patch("devsynth.application.cli.commands.inspect_config_cmd.analyze_project_structure")
@patch("devsynth.application.cli.commands.inspect_config_cmd.compare_with_manifest")
@patch("devsynth.application.cli.commands.inspect_config_cmd.prune_manifest")
@patch("yaml.dump")
@pytest.mark.fast
def test_inspect_config_prune_succeeds(
    mock_dump, mock_prune, mock_compare, mock_analyze, mock_bridge, tmp_path
):
    """Test that inspect config prune succeeds.

    ReqID: N/A"""
    manifest_path = tmp_path / "devsynth.yaml"
    yaml.safe_dump({"projectName": "Test"}, manifest_path.open("w"))
    mock_analyze.return_value = cast(
        ProjectStructureReport,
        {"directories": {"source": [], "tests": [], "docs": []}, "files": []},
    )
    mock_compare.return_value = [
        cast(
            StructureDifference,
            {"type": "tests", "path": "tests", "status": "missing in project"},
        )
    ]
    mock_prune.return_value = cast(ManifestModel, {"projectName": "Pruned"})
    inspect_config_cmd(path=str(tmp_path), prune=True)
    mock_analyze.assert_called_once_with(Path(str(tmp_path)))
    mock_compare.assert_called_once()
    mock_prune.assert_called_once()
    mock_dump.assert_called_once()
    assert any(
        "Configuration pruned successfully" in str(call.args[0])
        for call in mock_bridge.print.call_args_list
    )


@patch("devsynth.application.cli.commands.inspect_config_cmd.bridge")
@pytest.mark.fast
def test_inspect_config_no_config_succeeds(mock_bridge, tmp_path):
    """Test that inspect config no config succeeds.

    ReqID: N/A"""
    inspect_config_cmd(path=str(tmp_path))
    mock_bridge.print.assert_any_call(
        "[yellow]Warning: No configuration file found. Run 'devsynth init' to create it.[/yellow]"
    )


@pytest.mark.fast
def test_analyze_project_structure_returns_directories(tmp_path):
    """Project structure analysis records files and typed directories."""

    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("info")

    report = analyze_project_structure(tmp_path)

    assert "src" in report["directories"]["source"]
    assert "docs" in report["directories"]["docs"]
    assert "README.md" in report["files"]


@pytest.mark.fast
def test_compare_with_manifest_returns_differences():
    """Manifest comparison honors typed manifests."""

    manifest: ManifestModel = {
        "structure": {
            "directories": {
                "source": ["src"],
                "tests": [],
                "docs": [],
            }
        }
    }
    structure = cast(
        ProjectStructureReport,
        {
            "directories": {"source": ["src", "lib"], "tests": [], "docs": []},
            "files": [],
        },
    )

    differences = compare_with_manifest(manifest, structure)

    assert any(diff["path"] == "lib" for diff in differences)


@pytest.mark.fast
def test_update_manifest_adds_directory():
    """Updating manifests respects typed directory annotations."""

    manifest: ManifestModel = {
        "structure": {"directories": {"source": []}},
    }
    diffs: list[StructureDifference] = [
        cast(
            StructureDifference,
            {"type": "source", "path": "src", "status": "missing in manifest"},
        )
    ]

    updated = update_manifest(manifest, diffs)

    assert "src" in updated["structure"]["directories"]["source"]
