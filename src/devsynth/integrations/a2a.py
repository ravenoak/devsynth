"""A2A integration contracts and concrete connector for Autoresearch."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable
from urllib.parse import urljoin

import httpx

from devsynth.logger import DevSynthLogger, get_logger

from .mcp import AUTORESEARCH_API_BASE_ENV, DEFAULT_TIMEOUT
from .types import HTTPClientProtocol, JsonMapping

HTTP_ERROR = getattr(httpx, "HTTPError", Exception)


@runtime_checkable
class A2AConnector(Protocol):
    """Protocol describing Autoresearch A2A handshake hooks."""

    def prepare_channel(self, session_id: str) -> Mapping[str, object]:
        """Prepare an A2A channel for the provided session identifier."""

    def execute_query(self, session_id: str, sparql_query: str) -> Mapping[str, object]:
        """Run a SPARQL query through the Autoresearch bridge."""

    def fetch_metrics(self) -> Mapping[str, object]:
        """Return Autoresearch A2A metrics when available."""

    def close(self) -> None:
        """Close the A2A channel."""


@dataclass(slots=True)
class StubA2AConnector:
    """Placeholder connector until the Autoresearch A2A bridge ships."""

    service_name: str = "Autoresearch A2A"

    def prepare_channel(
        self, session_id: str
    ) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "channel negotiation flow in a future milestone."
        )

    def execute_query(
        self, session_id: str, sparql_query: str
    ) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "query orchestration flow in a future milestone."
        )

    def fetch_metrics(self) -> Mapping[str, object]:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "metrics endpoint in a future milestone."
        )

    def close(self) -> None:  # pragma: no cover - stub
        raise NotImplementedError(
            "A2A integration is not yet available. Autoresearch will expose the "
            "channel negotiation flow in a future milestone."
        )


@dataclass(slots=True)
class AutoresearchA2AConnector:
    """HTTP-backed A2A connector with graceful failure handling."""

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

    def prepare_channel(self, session_id: str) -> Mapping[str, object]:
        """Confirm A2A availability and capture baseline metrics."""

        if not self.base_url or not self.http_client:
            self.logger.info(
                "Autoresearch A2A connector disabled; base URL not configured.",
                extra={"endpoint": "health", "connector": "a2a"},
            )
            return {}

        health = self._get("health", log_hint="health")
        if not health:
            return {}
        metrics = self.fetch_metrics()
        result: dict[str, object] = {
            "session_id": session_id,
            "health": health,
        }
        if metrics:
            result["metrics"] = metrics
        return result

    def execute_query(self, session_id: str, sparql_query: str) -> Mapping[str, object]:
        """Execute a SPARQL query via Autoresearch if reachable."""

        payload: JsonMapping = {"session_id": session_id, "query": sparql_query}
        response = self._post("query", payload, log_hint="query")
        if response:
            result = dict(response)
            result.setdefault("session_id", session_id)
            return result
        return {}

    def fetch_metrics(self) -> Mapping[str, object]:
        """Return Autoresearch A2A metrics when available."""

        return self._get("metrics", log_hint="metrics")

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
                "Autoresearch A2A connector disabled; base URL not configured.",
                extra={"endpoint": path, "connector": "a2a"},
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
                "Autoresearch A2A %s request failed; falling back to fixtures.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "a2a"},
            )
            return {}
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Autoresearch A2A %s request raised unexpected error; using fallback.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "a2a"},
            )
            return {}

        status_code = getattr(response, "status_code", 200)
        if status_code and status_code >= 400:
            self.logger.warning(
                "Autoresearch A2A %s request returned HTTP %s; falling back to fixtures.",
                log_hint,
                status_code,
                extra={"endpoint": path, "connector": "a2a"},
            )
            return {}

        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            try:
                raise_for_status()
            except HTTP_ERROR as exc:  # pragma: no cover - httpx guard
                self.logger.warning(
                    "Autoresearch A2A %s request raised status error; using fallback.",
                    log_hint,
                    exc_info=exc,
                    extra={"endpoint": path, "connector": "a2a"},
                )
                return {}

        try:
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "Autoresearch A2A %s response was not JSON; falling back to fixtures.",
                log_hint,
                exc_info=exc,
                extra={"endpoint": path, "connector": "a2a"},
            )
            return {}

        if isinstance(data, Mapping):
            return dict(data)
        return {"data": data}


__all__ = ["A2AConnector", "AutoresearchA2AConnector", "StubA2AConnector"]
