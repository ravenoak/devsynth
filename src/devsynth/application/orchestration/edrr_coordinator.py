"""EDRR coordinator with dialectical reasoning integration."""

from typing import Any, Callable, Dict, List, Optional

from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.dialectical_reasoning import reasoning_loop

logger = DevSynthLogger(__name__)


class EDRRCoordinator:
    """Coordinate EDRR cycles with dialectical reasoning helpers."""

    def __init__(self, wsde_team: Any, memory_manager: Optional[Any] = None) -> None:
        self.wsde_team = wsde_team
        self.memory_manager = memory_manager
        self._sync_hooks: List[Callable[[Optional[Any]], None]] = []
        if self.memory_manager is not None:
            try:
                self.memory_manager.register_sync_hook(self._invoke_sync_hooks)
            except Exception:
                logger.debug("Could not register memory sync hook", exc_info=True)

    def register_sync_hook(self, hook: Callable[[Optional[Any]], None]) -> None:
        """Register a callback invoked after memory synchronization."""

        self._sync_hooks.append(hook)

    def _invoke_sync_hooks(self, item: Optional[Any]) -> None:
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
        try:
            self.memory_manager.flush_updates()
        except Exception:
            logger.debug("Memory flush failed", exc_info=True)
            # On failure, still notify hooks so callers are not left waiting
            # for a sync event that never occurs.
            self._invoke_sync_hooks(None)

    def apply_dialectical_reasoning(
        self,
        task: Dict[str, Any],
        critic_agent: Any,
        memory_integration: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Delegate dialectical reasoning to WSDE helpers.

        Args:
            task: Task containing a proposed solution.
            critic_agent: Agent providing critiques.
            memory_integration: Optional memory component.

        Returns:
            Result from :func:`apply_dialectical_reasoning`.
        """
        logger.info("EDRRCoordinator invoking dialectical reasoning")
        results = reasoning_loop(self.wsde_team, task, critic_agent, memory_integration)
        self._sync_memory()
        return results[-1] if results else {}
