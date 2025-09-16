from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.edrr.coordinator import (
    EDRRCoordinatorError,
    PersistenceMixin,
    PhaseManagementMixin,
)
from devsynth.methodology.base import Phase

pytestmark = pytest.mark.fast


class StubCoordinator(PersistenceMixin, PhaseManagementMixin):
    """Minimal coordinator for exercising the phase management mixin."""

    def __init__(self) -> None:
        self.memory_manager = MagicMock()
        self.wsde_team = MagicMock()
        self.wsde_team.get_role_map.return_value = {"primus": "alpha"}
        self.wsde_team.rotate_primus = MagicMock()
        self.wsde_team.progress_roles = MagicMock()
        self.manifest = object()
        self.manifest_parser = MagicMock()
        self.manifest_parser.check_phase_dependencies.return_value = True
        self.manifest_parser.start_phase = MagicMock()
        self.task = {"description": "Unit test"}
        self.results = {}
        self._preserved_context: dict[str, dict] = {}
        self._historical_data: list[dict] = []
        self._phase_start_times: dict[Phase, datetime] = {}
        self._enable_enhanced_logging = True
        self._execution_history: list[dict] = []
        self.performance_metrics: dict[str, list] = {}
        self.cycle_id = "cycle"
        self.auto_phase_transitions = False
        self.manual_next_phase: Phase | None = None
        self.phase_transition_timeout = 5
        self.current_phase: Phase | None = None
        self._quality_thresholds: dict[Phase, float | None] = {}
        self._invoke_sync_hooks = MagicMock()
        self._persist_context_snapshot = MagicMock()
        self._maybe_auto_progress = MagicMock()
        self._safe_store_with_edrr_phase = MagicMock()
        self._safe_retrieve_with_edrr_phase = MagicMock(return_value={})

    def _get_phase_quality_threshold(self, phase: Phase) -> float | None:
        return self._quality_thresholds.get(phase)


@pytest.fixture
def coordinator() -> StubCoordinator:
    coord = StubCoordinator()
    coord.memory_manager.flush_updates = MagicMock()
    return coord


def test_progress_to_phase_enforces_dependencies(coordinator: StubCoordinator) -> None:
    """ReqID: N/A"""

    coordinator.manifest_parser.check_phase_dependencies.return_value = False
    with pytest.raises(EDRRCoordinatorError):
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)


def test_progress_to_phase_updates_state(coordinator: StubCoordinator) -> None:
    """ReqID: N/A"""

    coordinator.current_phase = Phase.EXPAND
    coordinator.results = {"EXPAND": {"quality_score": 0.95}}
    coordinator._historical_data = [{"cycle_id": "ancestor"}]

    with patch(
        "devsynth.application.edrr.coordinator.phase_management.flush_memory_queue",
        return_value=None,
    ):
        coordinator.progress_to_phase(Phase.DIFFERENTIATE)

    assert coordinator.current_phase == Phase.DIFFERENTIATE
    assert coordinator.manifest_parser.start_phase.called
    coordinator.wsde_team.rotate_primus.assert_called_once()
    coordinator.wsde_team.progress_roles.assert_called_once_with(
        Phase.DIFFERENTIATE, coordinator.memory_manager
    )
    coordinator._safe_store_with_edrr_phase.assert_called()
    coordinator._persist_context_snapshot.assert_called_once_with(Phase.DIFFERENTIATE)
    coordinator._maybe_auto_progress.assert_called_once()
    assert coordinator._execution_history


def test_decide_next_phase_respects_quality_threshold(
    coordinator: StubCoordinator,
) -> None:
    """ReqID: N/A"""

    coordinator.current_phase = Phase.EXPAND
    coordinator.results = {"EXPAND": {"quality_score": 0.2}}
    coordinator._quality_thresholds = {Phase.EXPAND: 0.5}
    assert coordinator._decide_next_phase() is None

    coordinator.results["EXPAND"]["quality_score"] = 0.8
    coordinator._phase_start_times[Phase.EXPAND] = datetime.now() - timedelta(
        seconds=10
    )
    coordinator.phase_transition_timeout = 1
    assert coordinator._decide_next_phase() == Phase.DIFFERENTIATE


def test_maybe_auto_progress_invokes_progression(coordinator: StubCoordinator) -> None:
    """ReqID: N/A"""

    coordinator.auto_phase_transitions = True
    coordinator.wsde_team.elaborate_details = MagicMock()
    coordinator._decide_next_phase = MagicMock(side_effect=[Phase.REFINE, None])
    coordinator.progress_to_phase = MagicMock()

    coordinator._maybe_auto_progress()

    coordinator.progress_to_phase.assert_called_once_with(Phase.REFINE)


def test_decide_next_phase_consumes_manual_override(
    coordinator: StubCoordinator,
) -> None:
    """ReqID: N/A"""

    coordinator.manual_next_phase = Phase.REFINE
    coordinator.auto_phase_transitions = False
    coordinator.current_phase = Phase.DIFFERENTIATE

    assert coordinator._decide_next_phase() == Phase.REFINE
    assert coordinator.manual_next_phase is None


def test_decide_next_phase_requires_auto_transitions(
    coordinator: StubCoordinator,
) -> None:
    """ReqID: N/A"""

    coordinator.auto_phase_transitions = False
    coordinator.current_phase = Phase.EXPAND
    coordinator.results = {"EXPAND": {"phase_complete": True}}

    assert coordinator._decide_next_phase() is None


def test_decide_next_phase_returns_none_for_final_phase(
    coordinator: StubCoordinator,
) -> None:
    """ReqID: N/A"""

    coordinator.auto_phase_transitions = True
    coordinator.current_phase = Phase.RETROSPECT

    assert coordinator._decide_next_phase() is None


def test_progress_to_next_phase_rejects_final_phase(
    coordinator: StubCoordinator,
) -> None:
    """ReqID: N/A"""

    coordinator.current_phase = Phase.RETROSPECT

    with pytest.raises(EDRRCoordinatorError):
        coordinator.progress_to_next_phase()
