"""Tests for the edrr_cycle_cmd CLI command."""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
from devsynth.methodology.base import Phase


@pytest.fixture
def mock_bridge():
    with patch("devsynth.application.cli.commands.edrr_cycle_cmd.bridge") as mock:
        yield mock


@pytest.fixture
def mock_components():
    with patch(
        "devsynth.application.cli.commands.edrr_cycle_cmd.EDRRCoordinator"
    ) as coord_cls, patch(
        "devsynth.application.cli.commands.edrr_cycle_cmd.MemoryManager"
    ) as manager_cls, patch(
        "devsynth.application.cli.commands.edrr_cycle_cmd.run_pipeline"
    ) as run_pipeline_mock:
        coordinator = MagicMock()
        coordinator.generate_report.return_value = {"ok": True}
        coordinator.cycle_id = "cid"
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
        "devsynth.config.unified_loader.UnifiedConfigLoader.load",
        return_value=cfg,
    ) as mock_loader:
        yield mock_loader


def test_edrr_cycle_cmd_manifest_missing(tmp_path, mock_bridge, mock_config):
    missing = tmp_path / "manifest.yaml"
    edrr_cycle_cmd(str(missing))
    mock_bridge.print.assert_called_once_with(
        f"[red]Manifest file not found:[/red] {missing}"
    )


def test_edrr_cycle_cmd_success(tmp_path, mock_bridge, mock_components, mock_config):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("project: test")

    coordinator, memory_manager, coord_cls, run_pipeline_mock = mock_components

    edrr_cycle_cmd(str(manifest))

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
    run_pipeline_mock.assert_called_once_with(report=coordinator.generate_report.return_value)
    assert any(
        "EDRR cycle completed" in call.args[0]
        for call in mock_bridge.print.call_args_list
    )


def test_edrr_cycle_cmd_manual(tmp_path, mock_bridge, mock_components, mock_config):
    """Ensure manual mode passes auto flag through config and calls phases sequentially."""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("project: test")

    coordinator, _, coord_cls, _ = mock_components

    edrr_cycle_cmd(str(manifest), auto=False)

    assert coord_cls.call_args.kwargs["config"]["edrr"]["phase_transition"]["auto"] is False
    expected = [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]
    assert [c.args[0] for c in coordinator.progress_to_phase.call_args_list] == expected
