from __future__ import annotations

"""Agent coordinating WSDE team retrospective reviews."""

from typing import Any, Callable, Dict, List, Optional

from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class WSDETeamCoordinatorAgent:
    """Coordinate WSDE team retrospective reviews."""

    def __init__(self, team: Any) -> None:
        """Initialize the coordinator with a team object."""
        self._team = team
        self._sync_hooks: List[Callable[[Optional[Any]], None]] = []
        memory_manager = getattr(self._team, "memory_manager", None)
        if memory_manager is not None:
            try:
                memory_manager.register_sync_hook(self._invoke_sync_hooks)
            except Exception:  # pragma: no cover - defensive
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

    def run_retrospective(
        self, notes: List[Dict[str, Any]], sprint: int
    ) -> Dict[str, Any]:
        """Aggregate notes and record a retrospective summary.

        Args:
            notes: List of retrospective notes from team members.
            sprint: Current sprint number.

        Returns:
            Summary dictionary produced by
            :func:`map_retrospective_to_summary`.
        """

        aggregated: Dict[str, Any] = {
            "positives": [],
            "improvements": [],
            "action_items": [],
        }
        for item in notes:
            aggregated["positives"].extend(item.get("positives", []))
            aggregated["improvements"].extend(item.get("improvements", []))
            aggregated["action_items"].extend(item.get("action_items", []))

        summary = map_retrospective_to_summary(aggregated, sprint)

        if hasattr(self._team, "record_retrospective"):
            self._team.record_retrospective(summary)
        else:  # pragma: no cover - defensive
            logger.debug("Team object lacks 'record_retrospective' method")

        memory_manager = getattr(self._team, "memory_manager", None)
        if memory_manager and hasattr(memory_manager, "flush_updates"):
            try:
                memory_manager.flush_updates()
                wait = getattr(memory_manager, "wait_for_sync", None)
                if callable(wait):
                    import asyncio
                    import inspect

                    result = wait()
                    if inspect.isawaitable(result):  # pragma: no cover - requires loop
                        asyncio.run(result)
            except (RuntimeError, OSError):  # pragma: no cover - defensive
                logger.debug(
                    "Memory synchronization failed during retrospective",
                    exc_info=True,
                )
                self._invoke_sync_hooks(None)
        else:
            self._invoke_sync_hooks(None)
        return summary
