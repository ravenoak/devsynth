"""Autoresearch MCP/A2A client orchestration with graceful fallbacks."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from collections.abc import Mapping

from devsynth.logger import DevSynthLogger, get_logger

from .a2a import A2AConnector
from .mcp import MCPConnector

CONNECTORS_ENABLED_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_CONNECTORS"


@dataclass(slots=True)
class AutoresearchClient:
    """Coordinate MCP and A2A connectors for Autoresearch telemetry."""

    mcp_connector: MCPConnector
    a2a_connector: A2AConnector
    enabled: bool | None = None
    logger: DevSynthLogger = field(default_factory=lambda: get_logger(__name__))

    _active_session_id: str | None = field(init=False, default=None)
    _handshake_cache: Mapping[str, object] | None = field(init=False, default=None)
    _enabled: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        if self.enabled is None:
            env_value = os.getenv(CONNECTORS_ENABLED_ENV, "").strip().lower()
            self._enabled = env_value in {"1", "true", "yes"}
        else:
            self._enabled = self.enabled

    def handshake(self, session_id: str) -> Mapping[str, object]:
        """Perform the staged MCP → A2A handshake for a session."""

        if not self._enabled:
            self.logger.info(
                "Autoresearch connectors disabled; using fixture-backed telemetry.",
                extra={"session_id": session_id},
            )
            self._active_session_id = None
            self._handshake_cache = None
            return {}

        health = self.mcp_connector.check_health()
        if not health:
            self.logger.info(
                "Autoresearch health check failed; falling back to fixture telemetry.",
                extra={"session_id": session_id},
            )
            self._active_session_id = None
            self._handshake_cache = None
            return {}

        session = self.mcp_connector.ensure_session(session_id)
        if not session:
            self.logger.info(
                "Autoresearch MCP session setup failed; using fixture telemetry.",
                extra={"session_id": session_id},
            )
            self._active_session_id = None
            self._handshake_cache = None
            return {}

        capabilities = self.mcp_connector.fetch_capabilities()
        if not capabilities:
            self.logger.info(
                "Autoresearch MCP capabilities unavailable; using fixture telemetry.",
                extra={"session_id": session_id},
            )
            self._active_session_id = None
            self._handshake_cache = None
            return {}

        channel = self.a2a_connector.prepare_channel(session_id)
        if not channel:
            self.logger.info(
                "Autoresearch A2A channel unavailable; using fixture telemetry.",
                extra={"session_id": session_id},
            )
            self._active_session_id = None
            self._handshake_cache = None
            return {}

        handshake_data: dict[str, object] = {
            "health": health,
            "session": session,
            "capabilities": capabilities,
            "channel": channel,
        }

        self._active_session_id = session_id
        self._handshake_cache = handshake_data
        return handshake_data

    def fetch_trace_updates(
        self, sparql_query: str, session_id: str | None = None
    ) -> Mapping[str, object]:
        """Execute the SPARQL query via the Autoresearch stack."""

        if not self._enabled:
            self.logger.info(
                "Autoresearch connectors disabled; skipping external query.",
                extra={"query": sparql_query},
            )
            return {}

        active_session = session_id or self._active_session_id
        if not active_session:
            self.logger.info(
                "Autoresearch session unavailable; skipping external query.",
                extra={"query": sparql_query},
            )
            return {}

        query_result = self.a2a_connector.execute_query(active_session, sparql_query)
        if not query_result:
            self.logger.info(
                "Autoresearch query failed; returning fixture telemetry.",
                extra={"session_id": active_session, "query": sparql_query},
            )
            return {}

        metrics = self.a2a_connector.fetch_metrics()
        payload: dict[str, object] = {"results": query_result}
        if metrics:
            payload["metrics"] = metrics
        return payload


__all__ = ["AutoresearchClient", "CONNECTORS_ENABLED_ENV"]
