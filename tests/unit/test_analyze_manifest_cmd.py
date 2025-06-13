"""Tests for the analyze_manifest_cmd CLI command."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml

from devsynth.application.cli.commands.analyze_manifest_cmd import analyze_manifest_cmd


@patch("devsynth.application.cli.commands.analyze_manifest_cmd.Console")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.analyze_project_structure")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.compare_with_manifest")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.update_manifest")
@patch("yaml.dump")
def test_analyze_manifest_update(mock_dump, mock_update, mock_compare, mock_analyze, mock_console, tmp_path):
    manifest_path = tmp_path / "devsynth.yaml"
    yaml.safe_dump({"projectName": "Test"}, manifest_path.open("w"))

    mock_analyze.return_value = {}
    mock_compare.return_value = [{"type": "source", "path": "src", "status": "missing in manifest"}]
    mock_update.return_value = {"updated": True}

    analyze_manifest_cmd(path=str(tmp_path), update=True)

    mock_analyze.assert_called_once_with(Path(str(tmp_path)))
    mock_compare.assert_called_once()
    mock_update.assert_called_once()
    mock_dump.assert_called_once()
    assert any(
        "Configuration updated successfully" in str(call.args[0])
        for call in mock_console.return_value.print.call_args_list
    )


@patch("devsynth.application.cli.commands.analyze_manifest_cmd.Console")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.analyze_project_structure")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.compare_with_manifest")
@patch("devsynth.application.cli.commands.analyze_manifest_cmd.prune_manifest")
@patch("yaml.dump")
def test_analyze_manifest_prune(mock_dump, mock_prune, mock_compare, mock_analyze, mock_console, tmp_path):
    manifest_path = tmp_path / "devsynth.yaml"
    yaml.safe_dump({"projectName": "Test"}, manifest_path.open("w"))

    mock_analyze.return_value = {}
    mock_compare.return_value = [{"type": "tests", "path": "tests", "status": "missing in project"}]
    mock_prune.return_value = {"pruned": True}

    analyze_manifest_cmd(path=str(tmp_path), prune=True)

    mock_analyze.assert_called_once_with(Path(str(tmp_path)))
    mock_compare.assert_called_once()
    mock_prune.assert_called_once()
    mock_dump.assert_called_once()
    assert any(
        "Configuration pruned successfully" in str(call.args[0])
        for call in mock_console.return_value.print.call_args_list
    )


@patch("devsynth.application.cli.commands.analyze_manifest_cmd.Console")
def test_analyze_manifest_no_config(mock_console, tmp_path):
    analyze_manifest_cmd(path=str(tmp_path))
    mock_console.return_value.print.assert_any_call("[yellow]Warning: No configuration file found. Run 'devsynth init' to create it.[/yellow]")

