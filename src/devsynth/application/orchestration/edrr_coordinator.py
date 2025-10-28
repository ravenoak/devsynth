"""EDRR coordinator with dialectical reasoning integration."""

from typing import Any
from collections.abc import Mapping

from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase
from devsynth.methodology.edrr import EDRRCoordinator as MethodologyEDRRCoordinator
from devsynth.methodology.edrr import reasoning_loop
from devsynth.methodology.edrr.contracts import (
    MemoryIntegration,
    MemoryManager,
    SyncHook,
    WSDETeamProtocol,
)

logger = DevSynthLogger(__name__)


class EDRRCoordinator:
    """Coordinate EDRR cycles with dialectical reasoning helpers."""

    def __init__(
        self,
        wsde_team: WSDETeamProtocol,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self.wsde_team = wsde_team
        self.memory_manager = memory_manager
        self._sync_hooks: list[SyncHook] = []
        if self.memory_manager is not None:
            try:
                self.memory_manager.register_sync_hook(self._invoke_sync_hooks)
            except Exception:
                logger.debug("Could not register memory sync hook", exc_info=True)

    def register_sync_hook(self, hook: SyncHook) -> None:
        """Register a callback invoked after memory synchronization."""

        self._sync_hooks.append(hook)

    def _invoke_sync_hooks(self, item: Any | None) -> None:
        """Invoke registered synchronization hooks with ``item``."""

        for hook in list(self._sync_hooks):
            try:
                hook(item)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(f"Sync hook failed: {exc}")

    def _sync_memory(self) -> None:
        """Flush memory updates and notify hooks."""

        if self.memory_manager is None:
            # Even without a memory manager, downstream hooks expect a sync
            # notification so observers can advance their state.
            self._invoke_sync_hooks(None)
            return
        notified = False
        try:
            self.memory_manager.flush_updates()
            notified = True
        except Exception:
            logger.debug("Memory flush failed", exc_info=True)
        finally:
            if not notified:
                # Ensure observers are unblocked even if the flush failed.
                self._invoke_sync_hooks(None)

    def apply_dialectical_reasoning(
        self,
        task: Mapping[str, Any],
        critic_agent: object,
        memory_integration: MemoryIntegration | None = None,
    ) -> DialecticalSequence:
        """Delegate dialectical reasoning to WSDE helpers.

        Args:
            task: Task containing a proposed solution.
            critic_agent: Agent providing critiques.
            memory_integration: Optional memory component.

        Returns:
            Result from :func:`apply_dialectical_reasoning`.
        """
        logger.info("EDRRCoordinator invoking dialectical reasoning")
        coordinator = MethodologyEDRRCoordinator(self.memory_manager)
        results = reasoning_loop(
            self.wsde_team,
            task,
            critic_agent,
            memory_integration,
            phase=Phase.REFINE,
            coordinator=coordinator,
        )
        self._sync_memory()
        if not results:
            return DialecticalSequence.failed(reason="no_results")

        final_result = results[-1]
        if isinstance(final_result, DialecticalSequence):
            return final_result
        if isinstance(final_result, dict):
            return DialecticalSequence.from_dict(final_result)
        return DialecticalSequence.failed(reason="unknown_result_type")
