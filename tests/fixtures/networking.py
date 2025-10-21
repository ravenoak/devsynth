"""
Networking-related test fixtures.

These fixtures help ensure test hermeticity by preventing unintended
network egress. They are imported by tests/conftest.py.
"""

from __future__ import annotations

import os
import socket
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def disable_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable network access during tests.

    Patches low-level sockets and common HTTP client methods (when available)
    to raise a RuntimeError on any network attempt.

    Notes:
    - We block sockets at the lowest level as a universal safety net.
    - We also block httpx and (optionally) requests for earlier, clearer failures.
    - To allow requests patching to be disabled (e.g., when using 'responses'), set
      DEVSYNTH_TEST_ALLOW_REQUESTS=true in the environment.
    """

    def guard_connect(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access disabled during tests")

    # Block low-level sockets
    monkeypatch.setattr(socket.socket, "connect", guard_connect)

    # Patch urllib if importable
    try:  # pragma: no cover - optional dependency
        import urllib.request as _urllib_request  # type: ignore

        def _guard_urlopen(*args: Any, **kwargs: Any) -> None:  # type: ignore
            raise RuntimeError("Network access disabled during tests (urllib)")

        monkeypatch.setattr(_urllib_request, "urlopen", _guard_urlopen, raising=False)
    except Exception:
        pass

    # Optionally patch requests for clearer errors in environments not using 'responses'
    try:  # pragma: no cover - optional dependency
        import sys

        import requests  # type: ignore

        # If the 'responses' library is available (commonly used to stub requests),
        # do not patch requests so tests decorated with @responses.activate work.
        responses_active = "responses" in sys.modules

        allow_requests = responses_active or (
            os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS", "false").lower()
            in {"1", "true", "yes"}
        )
        if not allow_requests:

            def _guard_requests_request(*args: Any, **kwargs: Any) -> None:  # type: ignore
                raise RuntimeError("Network access disabled during tests (requests)")

            # Patch both the top-level and session-level request entrypoints
            monkeypatch.setattr(requests, "request", _guard_requests_request, raising=False)  # type: ignore
            try:
                from requests.sessions import Session  # type: ignore

                monkeypatch.setattr(Session, "request", _guard_requests_request, raising=False)  # type: ignore
            except Exception:
                pass
    except Exception:
        pass

    # Patch httpx if importable
    try:  # pragma: no cover - optional dependency
        import httpx  # type: ignore

        # Preserve original methods so we can delegate for allowed in-memory calls
        _orig_client_request = httpx.Client.request  # type: ignore[attr-defined]
        _orig_async_request = httpx.AsyncClient.request  # type: ignore[attr-defined]

        def guard_httpx_request(self, method: str, url, *args: Any, **kwargs: Any):  # type: ignore[no-redef]
            # Allow in-memory TestClient requests against the ASGI test server
            try:
                host = getattr(url, "host", None) or getattr(url, "netloc", None)
                if isinstance(host, bytes):
                    host = host.decode("utf-8", "ignore")
                host_str = str(host or "")
                if host_str.split(":")[0] == "testserver":
                    return _orig_client_request(self, method, url, *args, **kwargs)
            except Exception:
                host_str = str(url)
                if host_str.startswith("http://testserver") or host_str.startswith(
                    "https://testserver"
                ):
                    return _orig_client_request(self, method, url, *args, **kwargs)
            raise RuntimeError("Network access disabled during tests (httpx)")

        async def guard_httpx_async_request(self, method: str, url, *args: Any, **kwargs: Any):  # type: ignore[no-redef]
            try:
                host = getattr(url, "host", None) or getattr(url, "netloc", None)
                if isinstance(host, bytes):
                    host = host.decode("utf-8", "ignore")
                host_str = str(host or "")
                if host_str.split(":")[0] == "testserver":
                    return await _orig_async_request(self, method, url, *args, **kwargs)
            except Exception:
                host_str = str(url)
                if host_str.startswith("http://testserver") or host_str.startswith(
                    "https://testserver"
                ):
                    return await _orig_async_request(self, method, url, *args, **kwargs)
            raise RuntimeError("Network access disabled during tests (httpx)")

        monkeypatch.setattr(httpx.Client, "request", guard_httpx_request, raising=False)  # type: ignore
        monkeypatch.setattr(httpx.AsyncClient, "request", guard_httpx_async_request, raising=False)  # type: ignore
    except Exception:
        pass
