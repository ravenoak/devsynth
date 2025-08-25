"""Tests for the edrr_cycle_cmd CLI command."""

from unittest.mock import ANY, MagicMock, patch

import pytest

from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.methodology.base import Phase


@pytest.fixture
def mock_bridge():
    with patch("devsynth.application.cli.commands.edrr_cycle_cmd.bridge") as mock:
        yield mock


@pytest.fixture
def mock_tqdm():
    with patch("devsynth.application.cli.commands.edrr_cycle_cmd.tqdm") as mock:
        mock_progress = MagicMock()
        mock.return_value.__enter__.return_value = mock_progress
        yield mock, mock_progress


@pytest.fixture
def mock_components():
    with (
        patch(
            "devsynth.application.cli.commands.edrr_cycle_cmd.EnhancedEDRRCoordinator"
        ) as coord_cls,
        patch(
            "devsynth.application.cli.commands.edrr_cycle_cmd.MemoryManager"
        ) as manager_cls,
        patch(
            "devsynth.application.cli.commands.edrr_cycle_cmd.run_pipeline"
        ) as run_pipeline_mock,
    ):
        coordinator = MagicMock(spec=EnhancedEDRRCoordinator)
        coordinator.generate_report.return_value = {
            "ok": True,
            "insights": ["Insight 1", "Insight 2"],
            "next_steps": ["Step 1", "Step 2"],
        }
        coordinator.cycle_id = "cid"
        coordinator.phase_metrics = MagicMock()
        coordinator.phase_metrics.get_all_metrics.return_value = {
            "EXPAND": {"quality": 0.8},
            "DIFFERENTIATE": {"quality": 0.85},
            "REFINE": {"quality": 0.9},
            "RETROSPECT": {"quality": 0.95},
        }
        coord_cls.return_value = coordinator
        memory_manager = MagicMock()
        memory_manager.store_with_edrr_phase.return_value = "rid"
        manager_cls.return_value = memory_manager
        yield coordinator, memory_manager, coord_cls, run_pipeline_mock


@pytest.fixture
def mock_config():
    """Patch config loader to return an empty config."""
    cfg = MagicMock()
    cfg.as_dict.return_value = {}
    with patch(
        "devsynth.config.unified_loader.UnifiedConfigLoader.load", return_value=cfg
    ) as mock_loader:
        yield mock_loader


def test_edrr_cycle_cmd_no_input_raises_error(mock_bridge, mock_config):
    """Test that an error is shown when neither manifest nor prompt is provided.

    ReqID: N/A"""
    edrr_cycle_cmd()
    mock_bridge.print.assert_called_with(
        "[red]Error:[/red] Either manifest or prompt must be provided"
    )


def test_edrr_cycle_cmd_manifest_missing_raises_error(
    tmp_path, mock_bridge, mock_config
):
    """Test that an error is shown when the manifest file doesn't exist.

    ReqID: N/A"""
    missing = tmp_path / "manifest.yaml"
    edrr_cycle_cmd(manifest=str(missing))
    mock_bridge.print.assert_called_with(
        f"[red]Manifest file not found:[/red] {missing}"
    )


def test_edrr_cycle_cmd_manifest_success_succeeds(
    tmp_path, mock_bridge, mock_components, mock_config, mock_tqdm
):
    """Test successful execution with a manifest file.

    ReqID: N/A"""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("project: test")
    coordinator, memory_manager, coord_cls, run_pipeline_mock = mock_components
    _, mock_progress = mock_tqdm
    edrr_cycle_cmd(manifest=str(manifest))
    coord_cls.assert_called_once()
    assert (
        coord_cls.call_args.kwargs["config"]["edrr"]["phase_transition"]["auto"] is True
    )
    coordinator.start_cycle_from_manifest.assert_called_once_with(
        manifest, is_file=True
    )
    assert coordinator.progress_to_phase.call_count == 4
    memory_manager.store_with_edrr_phase.assert_called_once_with(
        coordinator.generate_report.return_value,
        "EDRR_CYCLE_RESULTS",
        Phase.RETROSPECT.value,
        {"cycle_id": coordinator.cycle_id},
    )
    run_pipeline_mock.assert_called_once_with(
        report=coordinator.generate_report.return_value
    )
    assert mock_progress.update.call_count == 4
    assert any(
        "Key Insights" in call.args[0] for call in mock_bridge.print.call_args_list
    )
    assert any(
        "Recommended Next Steps" in call.args[0]
        for call in mock_bridge.print.call_args_list
    )


def test_edrr_cycle_cmd_prompt_success_succeeds(
    mock_bridge, mock_components, mock_config, mock_tqdm
):
    """Test successful execution with a prompt.

    ReqID: N/A"""
    coordinator, memory_manager, coord_cls, run_pipeline_mock = mock_components
    _, mock_progress = mock_tqdm
    edrr_cycle_cmd(
        prompt="Improve error handling",
        context="In the API endpoints",
        max_iterations=5,
    )
    coord_cls.assert_called_once()
    assert (
        coord_cls.call_args.kwargs["config"]["edrr"]["phase_transition"]["auto"] is True
    )
    coordinator.start_cycle.assert_called_once()
    task = coordinator.start_cycle.call_args.args[0]
    assert task["description"] == "Improve error handling"
    assert task["context"] == "In the API endpoints"
    assert task["max_iterations"] == 5
    assert "created_at" in task
    assert coordinator.progress_to_phase.call_count == 4
    assert mock_progress.update.call_count == 4
    memory_manager.store_with_edrr_phase.assert_called_once_with(
        coordinator.generate_report.return_value,
        "EDRR_CYCLE_RESULTS",
        Phase.RETROSPECT.value,
        {"cycle_id": coordinator.cycle_id},
    )


def test_edrr_cycle_cmd_manual_succeeds(
    tmp_path, mock_bridge, mock_components, mock_config
):
    """Ensure manual mode passes auto flag through config and calls phases sequentially.

    ReqID: N/A"""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("project: test")
    coordinator, _, coord_cls, _ = mock_components
    edrr_cycle_cmd(manifest=str(manifest), auto=False)
    assert (
        coord_cls.call_args.kwargs["config"]["edrr"]["phase_transition"]["auto"]
        is False
    )
    expected = [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]
    assert [c.args[0] for c in coordinator.progress_to_phase.call_args_list] == expected


def test_edrr_cycle_cmd_custom_bridge_has_expected(mock_components, mock_config):
    """Test that a custom bridge is used when provided.

    ReqID: N/A"""
    custom_bridge = MagicMock()
    coordinator, _, _, _ = mock_components
    edrr_cycle_cmd(prompt="Test prompt", bridge=custom_bridge)
    custom_bridge.print.assert_called()
    coordinator.start_cycle.assert_called_once()
    coordinator.progress_to_phase.assert_called()


def test_edrr_cycle_cmd_error_handling_raises_error(
    mock_bridge, mock_components, mock_config
):
    """Test that errors are properly handled and reported.

    ReqID: N/A"""
    coordinator, _, _, _ = mock_components
    coordinator.start_cycle.side_effect = ValueError("Test error")
    edrr_cycle_cmd(prompt="Test prompt")
    mock_bridge.print.assert_any_call("[red]Unexpected error:[/red] Test error")
