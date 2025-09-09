from unittest.mock import MagicMock, patch

import pytest

import tests.behavior.steps.test_analyze_commands_steps as steps


@pytest.mark.fast
def test_run_command_inspect_code(monkeypatch):
    mock_manager = MagicMock()
    monkeypatch.setattr(steps, "inspect_code_cmd", lambda path: print("Architecture"))
    command_context = {}
    with (
        patch(
            "devsynth.application.orchestration.workflow.workflow_manager", mock_manager
        ),
        patch("devsynth.core.workflow_manager", mock_manager),
    ):
        steps.run_command(
            "devsynth inspect-code --path /tmp",
            monkeypatch,
            mock_manager,
            command_context,
        )
    mock_manager.execute_command.assert_called_with("inspect-code", {"path": "/tmp"})
    assert "Architecture" in command_context.get("output", "")


@pytest.mark.fast
def test_run_command_inspect_config_update(monkeypatch):
    mock_manager = MagicMock()
    monkeypatch.setattr(
        steps,
        "inspect_config_cmd",
        lambda path, upd, prn: print("Configuration updated successfully"),
    )
    command_context = {}
    with (
        patch(
            "devsynth.application.orchestration.workflow.workflow_manager", mock_manager
        ),
        patch("devsynth.core.workflow_manager", mock_manager),
    ):
        steps.run_command(
            "devsynth inspect-config --path proj --update",
            monkeypatch,
            mock_manager,
            command_context,
        )
    mock_manager.execute_command.assert_called_with(
        "inspect-config", {"path": "proj", "update": True, "prune": False}
    )
    assert "Configuration updated successfully" in command_context.get("output", "")
