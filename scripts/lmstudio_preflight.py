#!/usr/bin/env python3
"""
LM Studio preflight checker.

Purpose: Reduce flakes by verifying that the LM Studio-dependent test path
is correctly configured before running tests. This supports docs/tasks.md
Tasks 3.5 and 9.2 and aligns with .junie/guidelines.md (clarity, determinism)
and docs/plan.md (stabilize local LM Studio path).

Checks:
- DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE must be "true"
- LM_STUDIO_ENDPOINT must be set and reachable via a simple HTTP GET to "/v1/models" or root.
- Optional: Honor DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS for the probe (default 10).

Exit codes:
- 0: All checks passed; endpoint reachable.
- 1: Misconfiguration or unreachable endpoint; prints actionable guidance.

Usage:
  poetry run python scripts/lmstudio_preflight.py

This script does not modify environment variables. It only reports status.
"""
from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error
from urllib.parse import urljoin


def getenv_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def main() -> int:
    ok = True
    messages = []

    enabled = getenv_bool("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", default=False)
    if not enabled:
        ok = False
        messages.append(
            "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false — LM Studio tests will be skipped.\n"
            "To enable, export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true and install extras: 'tests llm'."
        )

    endpoint = os.getenv("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
    timeout_s = float(os.getenv("DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS", "10"))

    # Probe two URLs: /v1/models (newer LM Studio API) and root (fallback)
    probe_urls = [urljoin(endpoint.rstrip("/") + "/", "v1/models"), endpoint]

    reachable = False
    last_err = None
    for url in probe_urls:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                # Consider any HTTP status < 500 as a signal that the server is up.
                if 200 <= resp.status < 500:
                    reachable = True
                    break
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            last_err = e
        except Exception as e:  # pragma: no cover — defensive catch-all for CLI diagnostics
            last_err = e

    if not reachable:
        ok = False
        messages.append(
            "LM Studio endpoint appears unreachable: {}.\n".format(endpoint)
            + "Last error: {}\n".format(last_err)
            + "Verify LM Studio is running and listening at LM_STUDIO_ENDPOINT, or adjust the endpoint.\n"
            + "Example enablement:\n"
            + "  poetry install --with dev --extras \"tests llm\"\n"
            + "  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true\n"
            + "  export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234\n"
            + "  export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10\n"
            + "  export DEVSYNTH_LMSTUDIO_RETRIES=1\n"
        )

    if ok:
        print("LM Studio preflight: OK")
        print("  DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true")
        print(f"  LM_STUDIO_ENDPOINT={endpoint}")
        print(f"  Probe succeeded within {timeout_s}s")
        return 0

    print("LM Studio preflight: FAILED")
    for m in messages:
        print("- " + m.strip())
    return 1


if __name__ == "__main__":
    sys.exit(main())
