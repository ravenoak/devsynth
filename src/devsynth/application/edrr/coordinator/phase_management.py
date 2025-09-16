"""Phase transition helpers for the EDRR coordinator."""

from __future__ import annotations

import copy
from datetime import datetime

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.application.edrr.manifest_parser import ManifestParseError
from devsynth.domain.models.memory import MemoryType
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)


class PhaseManagementMixin:
    """Provide reusable phase transition logic for coordinator implementations."""

    def progress_to_phase(self, phase: Phase) -> None:
        """Progress to the specified phase."""

        from .core import EDRRCoordinatorError  # Late import to avoid cycles

        try:
            if self.manifest is not None and self.manifest_parser:
                if not self.manifest_parser.check_phase_dependencies(phase):
                    error_msg = (
                        f"Cannot progress to {phase.value} phase: dependencies not met"
                    )
                    logger.error(error_msg)
                    raise EDRRCoordinatorError(error_msg)

                self.manifest_parser.start_phase(phase)

            try:
                flush_memory_queue(self.memory_manager)
            except Exception as flush_error:  # pragma: no cover - defensive
                logger.debug(
                    "Failed to flush memory updates before phase transition: %s",
                    flush_error,
                )
                self._invoke_sync_hooks(None)
            else:
                if self.memory_manager is None:
                    self._invoke_sync_hooks(None)

            previous_phase = self.current_phase
            if previous_phase is not None:
                self.wsde_team.rotate_primus()

            if previous_phase and previous_phase.name in self.results:
                self._preserved_context = getattr(self, "_preserved_context", {})
                self._preserved_context[previous_phase.name] = copy.deepcopy(
                    self.results[previous_phase.name]
                )
                stored_ctx = self._safe_retrieve_with_edrr_phase(
                    "CONTEXT_SNAPSHOT", previous_phase.value
                )
                if isinstance(stored_ctx, dict):
                    self._preserved_context.update(stored_ctx)

            if hasattr(self.wsde_team, "progress_roles"):
                self.wsde_team.progress_roles(phase, self.memory_manager)
            else:
                self.wsde_team.assign_roles_for_phase(phase, self.task)
            role_metadata = {"cycle_id": self.cycle_id, "type": "ROLE_ASSIGNMENT"}
            self._safe_store_with_edrr_phase(
                self.wsde_team.get_role_map(),
                MemoryType.TEAM_STATE,
                phase.value,
                role_metadata,
            )

            phase_metadata = {
                "cycle_id": self.cycle_id,
                "type": "PHASE_TRANSITION",
            }
            if previous_phase and previous_phase.name in self.results:
                prev_results = self.results[previous_phase.name]
                if "quality_score" in prev_results:
                    phase_metadata["quality_metrics"] = {
                        "quality_score": prev_results["quality_score"],
                    }
            if self._historical_data:
                phase_metadata["historical_data_references"] = [
                    {"cycle_id": data.get("cycle_id")}
                    for data in self._historical_data
                    if isinstance(data, dict) and data.get("cycle_id")
                ]
            self._safe_store_with_edrr_phase(
                {
                    "from": previous_phase.value if previous_phase else None,
                    "to": phase.value,
                },
                MemoryType.EPISODIC,
                phase.value,
                phase_metadata,
            )

            self.current_phase = phase

            start_time = datetime.now()
            self._phase_start_times[phase] = start_time
            if self._enable_enhanced_logging:
                self._execution_history.append(
                    {
                        "timestamp": start_time.isoformat(),
                        "phase": phase.value,
                        "action": "start",
                        "details": {},
                    }
                )

            logger.info(
                "Transitioned to %s phase for task: %s",
                phase.value,
                self.task.get("description", "Unknown"),
            )

            self._persist_context_snapshot(phase)
            self._maybe_auto_progress()
        except ManifestParseError as error:
            logger.error("Failed to progress to phase %s: %s", phase.value, error)
            raise EDRRCoordinatorError(
                f"Failed to progress to phase {phase.value}: {error}"
            )

    def progress_to_next_phase(self) -> None:
        """Progress to the next phase in the standard EDRR sequence."""

        from .core import EDRRCoordinatorError  # Late import to avoid cycles

        if self.current_phase is None:
            raise EDRRCoordinatorError("No current phase set")

        phase_order = [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]
        try:
            idx = phase_order.index(self.current_phase)
        except ValueError as exc:
            raise EDRRCoordinatorError("Unknown current phase") from exc

        if idx >= len(phase_order) - 1:
            raise EDRRCoordinatorError("Already at final phase")

        next_phase = phase_order[idx + 1]
        self.progress_to_phase(next_phase)

    def _decide_next_phase(self) -> Phase | None:
        """Determine if the coordinator should automatically move to the next phase."""

        if self.manual_next_phase is not None:
            phase = self.manual_next_phase
            self.manual_next_phase = None
            return phase

        if not self.auto_phase_transitions:
            return None

        if self.current_phase == Phase.RETROSPECT:
            return None

        phase_order = [
            Phase.EXPAND,
            Phase.DIFFERENTIATE,
            Phase.REFINE,
            Phase.RETROSPECT,
        ]
        idx = phase_order.index(self.current_phase)
        next_phase = phase_order[idx + 1]

        phase_results = self.results.get(self.current_phase.name, {})
        q_threshold = self._get_phase_quality_threshold(self.current_phase)
        if (
            q_threshold is not None
            and phase_results.get("quality_score", 1.0) < q_threshold
        ):
            phase_results.setdefault("quality_issues", []).append(
                {
                    "threshold": q_threshold,
                    "score": phase_results.get("quality_score", 0.0),
                }
            )
            phase_results["additional_processing"] = True
            return None
        if phase_results.get("phase_complete", False) is True:
            return next_phase

        start_time = self._phase_start_times.get(self.current_phase)
        if (
            start_time
            and (datetime.now() - start_time).total_seconds()
            >= self.phase_transition_timeout
        ):
            return next_phase

        return None

    def _maybe_auto_progress(self) -> None:
        """Trigger automatic phase transition when conditions are met."""

        if not self.auto_phase_transitions or not hasattr(
            self.wsde_team, "elaborate_details"
        ):
            return
        for _ in range(10):  # safety bound against infinite loops
            next_phase = self._decide_next_phase()
            if not next_phase:
                break
            self.progress_to_phase(next_phase)


__all__ = ["PhaseManagementMixin"]
