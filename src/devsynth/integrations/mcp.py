"""MCP integration contracts and concrete connector for Autoresearch."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from collections.abc import Mapping
from urllib.parse import urljoin

import httpx

from devsynth.logger import DevSynthLogger, get_logger

from .types import HTTPClientProtocol, JsonMapping

AUTORESEARCH_API_BASE_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_API_BASE"
DEFAULT_TIMEOUT = 5.0
HTTP_ERROR = getattr(httpx, "HTTPError", Exception)


@runtime_checkable
class MCPConnector(Protocol):
    """Protocol describing the minimum MCP connector hooks."""

    def check_health(self) -> Mapping[str, object]:
        """Return Autoresearch health metadata if available."""

    def ensure_session(self, session_id: str) -> Mapping[str, object]:
        """Prepare an MCP session for the provided identifier."""

    def fetch_capabilities(self) -> Mapping[str, object]:
        """Return advertised MCP capabilities when available."""

    def close(self) -> None:
        """Close any underlying MCP connections."""


@dataclass(slots=True)
class StubMCPConnector:
    """Placeholder connector until the Autoresearch MCP bridge ships."""

    service_name: str = "Autoresearch MCP"

    def check_health(self) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "health endpoint in a future milestone."
        )

    def ensure_session(
        self, session_id: str
    ) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "session negotiation flow in a future milestone."
        )

    def fetch_capabilities(self) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "capabilities endpoint in a future milestone."
        )

    def close(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "MCP integration is not yet available. Autoresearch will expose the "
            "session negotiation flow in a future milestone."
        )


@dataclass(slots=True)
class AutoresearchMCPConnector:
    """HTTP-backed MCP connector that gracefully degrades when unavailable."""

    base_url: str | None = None
    http_client: HTTPClientProtocol | None = None
    timeout: float = DEFAULT_TIMEOUT
    logger: DevSynthLogger = field(default_factory=lambda: get_logger(__name__))

    _owns_client: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        if not self.base_url:
            self.base_url = os.getenv(AUTORESEARCH_API_BASE_ENV)
        if self.base_url:
            self.base_url = self.base_url.rstrip("/") + "/"
        if self.base_url and self.http_client is None:
            self.http_client = httpx.Client(
                base_url=self.base_url, timeout=self.timeout
            )
            self._owns_client = True

    def check_health(self) -> Mapping[str, object]:
        """Return Autoresearch health metadata if reachable."""

        return self._get("health", log_hint="health")

    def ensure_session(self, session_id: str) -> Mapping[str, object]:
        """Attempt to initialise an Autoresearch MCP session."""

        payload = {"session_id": session_id}
        response = self._post("mcp", payload, log_hint="session")
        if response:
            result = dict(response)
            result.setdefault("session_id", session_id)
            return result
        return {}

    def fetch_capabilities(self) -> Mapping[str, object]:
        """Return Autoresearch MCP capability metadata when available."""

        return self._get("capabilities", log_hint="capabilities")

    def close(self) -> None:
        """Dispose of any owned HTTP clients."""

        if self._owns_client and self.http_client is not None:
            with contextlib.suppress(Exception):
                self.http_client.close()

    # Internal helpers -------------------------------------------------

    def _get(self, path: str, *, log_hint: str) -> Mapping[str, object]:
        return self._request("GET", path, log_hint=log_hint)

    def _post(
        self, path: str, payload: JsonMapping, *, log_hint: str
    ) -> Mapping[str, object]:
        return self._request("POST", path, payload=payload, log_hint=log_hint)

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: JsonMapping | None = None,
        log_hint: str,
    ) -> Mapping[str, object]:
        if not self.base_url or not self.http_client:
            self.logger.info(
                "Autoresearch MCP connector disabled; base URL not configured.",
                extra={"endpoint": path, "connector": "mcp"},
            )
            return {}

        url = urljoin(self.base_url, path)
        try:
            if method == "GET":
                response = self.http_client.get(url, timeout=self.timeout)
            else:
                response = self.http_client.post(
                    url, json=payload, timeout=self.timeout
                )
        except HTTP_ERROR as exc:
            self.logger.warning(
                "Autoresearch MCP %s request failed; falling back to fixtures.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "mcp"},
            )
            return {}
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Autoresearch MCP %s request raised unexpected error; using fallback.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "mcp"},
            )
            return {}

        status_code = getattr(response, "status_code", 200)
        if status_code and status_code >= 400:
            self.logger.warning(
                "Autoresearch MCP %s request returned HTTP %s; falling back to fixtures.",
                log_hint,
                status_code,
                extra={"endpoint": path, "connector": "mcp"},
            )
            return {}

        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            try:
                raise_for_status()
            except HTTP_ERROR as exc:  # pragma: no cover - httpx guard
                self.logger.warning(
                    "Autoresearch MCP %s request raised status error; using fallback.",
                    log_hint,
                    exc_info=exc,
                    extra={"endpoint": path, "connector": "mcp"},
                )
                return {}

        try:
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "Autoresearch MCP %s response was not JSON; falling back to fixtures.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "mcp"},
            )
            return {}

        if isinstance(data, Mapping):
            return dict(data)
        return {"data": data}


__all__ = [
    "AUTORESEARCH_API_BASE_ENV",
    "AutoresearchMCPConnector",
    "DEFAULT_TIMEOUT",
    "MCPConnector",
    "StubMCPConnector",
]
