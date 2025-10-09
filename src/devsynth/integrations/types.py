"""Shared typing helpers for Autoresearch integrations."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

JsonMapping = Mapping[str, object]


class HTTPClientProtocol(Protocol):
    """Protocol describing the minimal HTTP client surface used by connectors."""

    def get(
        self, url: str, *, timeout: float | None = None
    ) -> Any:  # pragma: no cover - protocol
        """Issue a GET request."""

    def post(
        self,
        url: str,
        *,
        json: JsonMapping | None = None,
        timeout: float | None = None,
    ) -> Any:  # pragma: no cover - protocol
        """Issue a POST request with a JSON payload."""

    def close(self) -> None:  # pragma: no cover - protocol
        """Close the underlying client resources."""


__all__ = ["HTTPClientProtocol", "JsonMapping"]
