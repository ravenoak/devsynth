"""Tests for the edrr_cycle_cmd CLI command."""

from pathlib import Path
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
    ) as manager_cls:
        coordinator = MagicMock()
        coordinator.generate_report.return_value = {"ok": True}
        coordinator.cycle_id = "cid"
        coord_cls.return_value = coordinator

        memory_manager = MagicMock()
        memory_manager.store_with_edrr_phase.return_value = "rid"
        manager_cls.return_value = memory_manager

        yield coordinator, memory_manager, coord_cls


def test_edrr_cycle_cmd_manifest_missing(tmp_path, mock_bridge):
    missing = tmp_path / "manifest.yaml"
    edrr_cycle_cmd(str(missing))
    mock_bridge.print.assert_called_once_with(
        f"[red]Manifest file not found:[/red] {missing}"
    )


def test_edrr_cycle_cmd_success(tmp_path, mock_bridge, mock_components):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("project: test")

    coordinator, memory_manager, coord_cls = mock_components

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
    assert any(
        "EDRR cycle completed" in call.args[0]
        for call in mock_bridge.print.call_args_list
    )
