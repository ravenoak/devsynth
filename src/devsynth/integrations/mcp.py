"""MCP integration contracts for external research providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class MCPConnector(Protocol):
    """Protocol describing the minimum MCP connector hooks."""

    def ensure_session(self, session_id: str) -> None:
        """Prepare an MCP session for the provided identifier."""

    def close(self) -> None:
        """Close any underlying MCP connections."""


@dataclass(slots=True)
class StubMCPConnector:
    """Placeholder connector until the Autoresearch MCP bridge ships."""

    service_name: str = "Autoresearch MCP"

    def ensure_session(self, session_id: str) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "session negotiation flow in a future milestone."
        )

    def close(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "session negotiation flow in a future milestone."
        )


__all__ = ["MCPConnector", "StubMCPConnector"]
