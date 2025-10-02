"""A2A integration contracts for external research providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class A2AConnector(Protocol):
    """Protocol describing Autoresearch A2A handshake hooks."""

    def prepare_channel(self, session_id: str) -> None:
        """Prepare an A2A channel for the provided session identifier."""

    def close(self) -> None:
        """Close the A2A channel."""


@dataclass(slots=True)
class StubA2AConnector:
    """Placeholder connector until the Autoresearch A2A bridge ships."""

    service_name: str = "Autoresearch A2A"

    def prepare_channel(self, session_id: str) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "channel negotiation flow in a future milestone."
        )

    def close(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "channel negotiation flow in a future milestone."
        )


__all__ = ["A2AConnector", "StubA2AConnector"]
