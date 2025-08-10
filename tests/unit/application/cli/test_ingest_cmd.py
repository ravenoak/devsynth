import os
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli.cli_commands import ingest_cmd
from devsynth.interface.cli import CLIUXBridge


@pytest.mark.medium
@patch("devsynth.application.cli.ingest_cmd.validate_manifest")
@patch("devsynth.application.cli.ingest_cmd.Ingestion")
def test_ingest_cmd_non_interactive_skips_prompts(
    mock_ingestion,
    _mock_validate_manifest,
    monkeypatch,
):
    """``--non-interactive`` skips prompts and auto-confirms."""

    monkeypatch.delenv("DEVSYNTH_NONINTERACTIVE", raising=False)
    monkeypatch.delenv("DEVSYNTH_AUTO_CONFIRM", raising=False)

    bridge = CLIUXBridge()
    bridge.ask_question = MagicMock()
    bridge.confirm_choice = MagicMock()

    mock_instance = mock_ingestion.return_value
    mock_instance.run_ingestion.return_value = {"success": True, "metrics": {}}

    ingest_cmd(
        manifest_path=None,
        dry_run=False,
        verbose=False,
        validate_only=False,
        yes=False,
        priority=None,
        auto_phase_transitions=True,
        defaults=False,
        non_interactive=True,
        bridge=bridge,
    )

    bridge.ask_question.assert_not_called()
    bridge.confirm_choice.assert_not_called()
    assert os.environ.get("DEVSYNTH_NONINTERACTIVE") == "1"
    assert os.environ.get("DEVSYNTH_AUTO_CONFIRM") == "1"


@pytest.mark.medium
@patch("devsynth.application.cli.ingest_cmd.validate_manifest")
@patch("devsynth.application.cli.ingest_cmd.Ingestion")
def test_ingest_cmd_defaults_enable_non_interactive(
    mock_ingestion,
    _mock_validate_manifest,
    monkeypatch,
):
    """``--defaults`` implies ``--non-interactive`` and skips prompts."""

    monkeypatch.delenv("DEVSYNTH_NONINTERACTIVE", raising=False)
    monkeypatch.delenv("DEVSYNTH_AUTO_CONFIRM", raising=False)

    bridge = CLIUXBridge()
    bridge.ask_question = MagicMock()
    bridge.confirm_choice = MagicMock()

    mock_instance = mock_ingestion.return_value
    mock_instance.run_ingestion.return_value = {"success": True, "metrics": {}}

    ingest_cmd(
        manifest_path=None,
        dry_run=False,
        verbose=False,
        validate_only=False,
        yes=False,
        priority=None,
        auto_phase_transitions=True,
        defaults=True,
        non_interactive=False,
        bridge=bridge,
    )

    bridge.ask_question.assert_not_called()
    bridge.confirm_choice.assert_not_called()
    assert os.environ.get("DEVSYNTH_NONINTERACTIVE") == "1"
    assert os.environ.get("DEVSYNTH_AUTO_CONFIRM") == "1"
