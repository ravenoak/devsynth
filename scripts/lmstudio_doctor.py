#!/usr/bin/env python3
"""
LM Studio readiness doctor.

Goals:
- Succeeds quickly when LM Studio resource is disabled (default path).
- When explicitly enabled, verifies endpoint URL, connectivity, and basic /health or /v1/models request with timeout.
- Honors env vars used by DevSynth:
  - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE ("true" to enable checks)
  - LM_STUDIO_ENDPOINT (default http://127.0.0.1:1234)
  - DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS (default 5.0 for this script)

Exit codes:
 0 = OK (either disabled or checks pass)
 1 = Misconfiguration (bad URL, etc.)
 2 = Connectivity/timeout/refused

This is a lightweight, no-deps script to help maintainers validate the local LM Studio path end-to-end.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Tuple
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _timeout_env(name: str, default: float) -> float:
    val = os.environ.get(name)
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _validate_url(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False, f"Unsupported scheme in LM_STUDIO_ENDPOINT: {parsed.scheme!r}"
        if not parsed.netloc and not parsed.path:
            return False, "LM_STUDIO_ENDPOINT missing host"
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"Invalid LM_STUDIO_ENDPOINT: {e}"


def main() -> int:
    enabled = _bool_env("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", default=False)
    endpoint = os.environ.get("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
    timeout = _timeout_env("DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS", 5.0)

    if not enabled:
        print(
            "[lmstudio-doctor] Resource disabled (DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false). OK."
        )
        return 0

    ok, reason = _validate_url(endpoint)
    if not ok:
        print(f"[lmstudio-doctor] Misconfiguration: {reason}", file=sys.stderr)
        return 1

    # Prefer an inexpensive models listing if available; otherwise try root.
    # We avoid importing any lmstudio SDK; use plain HTTP.
    paths = ["/v1/models", "/health", "/"]
    for path in paths:
        url = endpoint.rstrip("/") + path
        try:
            start = time.time()
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as resp:  # nosec B310 (local endpoint)
                status = resp.getcode()
                content_type = resp.headers.get("Content-Type", "")
                body = resp.read(1024)
            dur = (time.time() - start) * 1000
            print(
                f"[lmstudio-doctor] GET {url} -> {status} in {dur:.1f}ms; content-type={content_type}"
            )
            if 200 <= status < 500:
                # Consider 2xx/3xx/4xx as reachable; try to parse JSON if looks like it
                if b"{" in body[:1]:
                    try:
                        _ = json.loads(body.decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
                print("[lmstudio-doctor] Endpoint reachable. OK.")
                return 0
        except URLError as e:
            last_err = e
        except Exception as e:  # noqa: BLE001
            last_err = e
    print(
        f"[lmstudio-doctor] Connectivity error to {endpoint}: {last_err}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
