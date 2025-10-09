"""Tests for the Autoresearch MCP/A2A client orchestration."""

from __future__ import annotations

from collections import defaultdict

import httpx
import pytest

from devsynth.integrations.a2a import AutoresearchA2AConnector
from devsynth.integrations.autoresearch_client import (
    CONNECTORS_ENABLED_ENV,
    AutoresearchClient,
)
from devsynth.integrations.mcp import AutoresearchMCPConnector

pytestmark = pytest.mark.fast


class FakeResponse:
    """Simple response wrapper mimicking httpx's JSON behaviour."""

    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://autoresearch.invalid/raise")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)


class FakeHTTPClient:
    """HTTP client stub allowing sequential responses per endpoint."""

    def __init__(self, responses: dict[tuple[str, str], list[object] | object]) -> None:
        self._responses: dict[tuple[str, str], list[object]] = defaultdict(list)
        for key, value in responses.items():
            if isinstance(value, list):
                self._responses[key] = value.copy()
            else:
                self._responses[key] = [value]
        self.calls: list[tuple[str, str]] = []

    def _pop(self, method: str, url: str) -> object:
        queue = self._responses.get((method, url))
        if not queue:
            raise AssertionError(f"No response configured for {(method, url)!r}")
        return queue.pop(0)

    def get(self, url: str, *, timeout: float | None = None) -> object:
        self.calls.append(("GET", url))
        result = self._pop("GET", url)
        if isinstance(result, Exception):
            raise result
        return result

    def post(
        self,
        url: str,
        *,
        json: dict[str, object] | None = None,
        timeout: float | None = None,
    ) -> object:
        self.calls.append(("POST", url))
        result = self._pop("POST", url)
        if isinstance(result, Exception):
            raise result
        return result

    def close(self) -> None:  # pragma: no cover - not exercised
        self.calls.append(("CLOSE", ""))


def _base_url() -> str:
    return "https://api.autoresearch.local/"


def test_handshake_and_query_success() -> None:
    """AutoresearchClient orchestrates the full MCP → A2A → SPARQL flow."""

    base = _base_url()
    mcp_responses = {
        ("GET", f"{base}health"): [FakeResponse({"status": "ok"})],
        ("POST", f"{base}mcp"): [FakeResponse({"session_token": "abc123"})],
        ("GET", f"{base}capabilities"): [FakeResponse({"tools": ["sparql"]})],
    }
    a2a_responses = {
        ("GET", f"{base}health"): [FakeResponse({"status": "ok"})],
        ("GET", f"{base}metrics"): [
            FakeResponse({"pending": 0}),
            FakeResponse({"pending": 1}),
        ],
        ("POST", f"{base}query"): [FakeResponse({"records": [{"trace_id": "t-1"}]})],
    }
    mcp_client = FakeHTTPClient(mcp_responses)
    a2a_client = FakeHTTPClient(a2a_responses)
    mcp_connector = AutoresearchMCPConnector(base_url=base, http_client=mcp_client)
    a2a_connector = AutoresearchA2AConnector(base_url=base, http_client=a2a_client)
    client = AutoresearchClient(mcp_connector, a2a_connector, enabled=True)

    handshake = client.handshake("session-123")

    assert handshake["session"]["session_id"] == "session-123"
    assert handshake["health"]["status"] == "ok"
    assert handshake["capabilities"]["tools"] == ["sparql"]
    assert handshake["channel"]["metrics"]["pending"] == 0

    updates = client.fetch_trace_updates("SELECT * WHERE { ?s ?p ?o } LIMIT 1")

    assert updates["results"]["session_id"] == "session-123"
    assert updates["results"]["records"] == [{"trace_id": "t-1"}]
    assert updates["metrics"]["pending"] == 1

    assert ("GET", f"{base}health") in mcp_client.calls
    assert ("POST", f"{base}query") in a2a_client.calls


def test_handshake_disabled_by_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """When connectors are disabled the client never calls the network."""

    base = _base_url()
    mcp_client = FakeHTTPClient(
        {("GET", f"{base}health"): [FakeResponse({"status": "ok"})]}
    )
    a2a_client = FakeHTTPClient(
        {("GET", f"{base}health"): [FakeResponse({"status": "ok"})]}
    )
    monkeypatch.delenv(CONNECTORS_ENABLED_ENV, raising=False)
    client = AutoresearchClient(
        AutoresearchMCPConnector(base_url=base, http_client=mcp_client),
        AutoresearchA2AConnector(base_url=base, http_client=a2a_client),
        enabled=False,
    )

    result = client.handshake("disabled-session")

    assert result == {}
    assert mcp_client.calls == []
    assert a2a_client.calls == []


def test_query_failure_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    """Network errors during query execution fall back to fixtures."""

    base = _base_url()
    mcp_client = FakeHTTPClient(
        {
            ("GET", f"{base}health"): [FakeResponse({"status": "ok"})],
            ("POST", f"{base}mcp"): [FakeResponse({"session_token": "abc"})],
            ("GET", f"{base}capabilities"): [FakeResponse({"tools": ["sparql"]})],
        }
    )
    query_error = RuntimeError("boom")
    a2a_client = FakeHTTPClient(
        {
            ("GET", f"{base}health"): [FakeResponse({"status": "ok"})],
            ("GET", f"{base}metrics"): [
                FakeResponse({"pending": 0}),
                FakeResponse({"pending": 0}),
            ],
            ("POST", f"{base}query"): [query_error],
        }
    )

    client = AutoresearchClient(
        AutoresearchMCPConnector(base_url=base, http_client=mcp_client),
        AutoresearchA2AConnector(base_url=base, http_client=a2a_client),
        enabled=True,
    )

    assert client.handshake("session-err")

    caplog.set_level("INFO")
    updates = client.fetch_trace_updates(
        "SELECT * WHERE { ?s ?p ?o }", session_id="session-err"
    )

    assert updates == {}
    assert any(
        "Autoresearch query failed" in record.message for record in caplog.records
    )
