"""WSDE team proxy for consensus failure handling and structured logging."""

from typing import Any
from collections.abc import Callable

from devsynth.exceptions import ConsensusError
from devsynth.logging_setup import DevSynthLogger


class WSDETeamProxy:
    """Proxy that wraps WSDE team methods to handle consensus failures.

    The proxy intercepts calls to the underlying WSDE team and captures
    :class:`ConsensusError` exceptions. When a consensus error occurs the
    proxy emits a structured log entry and records the failure in the provided
    metrics dictionary. The wrapped call returns ``None`` allowing callers to
    branch on failure conditions.
    """

    def __init__(
        self,
        team: Any,
        logger: DevSynthLogger,
        metrics: dict,
        cycle_id_getter: Callable[[], str],
    ) -> None:
        self._team = team
        self._logger = logger
        self._metrics = metrics
        self._get_cycle_id = cycle_id_getter

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - thin wrapper
        attr = getattr(self._team, name)
        if not callable(attr):
            return attr

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                return attr(*args, **kwargs)
            except ConsensusError as exc:
                cycle_id = self._get_cycle_id()
                self._logger.error(
                    f"Consensus failure in WSDE method {name}: {exc}",
                    extra={"method": name, "cycle_id": cycle_id},
                )
                self._metrics.setdefault("consensus_failures", []).append(
                    {"method": name, "error": str(exc), "cycle_id": cycle_id}
                )
                return None

        return wrapped
