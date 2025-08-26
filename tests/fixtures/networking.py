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
        import requests  # type: ignore

        allow_requests = os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS", "false").lower() in {"1", "true", "yes"}
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

        def guard_httpx_request(*args: Any, **kwargs: Any) -> None:  # type: ignore
            raise RuntimeError("Network access disabled during tests (httpx)")

        monkeypatch.setattr(httpx.Client, "request", guard_httpx_request, raising=False)  # type: ignore
        monkeypatch.setattr(
            httpx.AsyncClient, "request", guard_httpx_request, raising=False
        )  # type: ignore
    except Exception:
        pass
