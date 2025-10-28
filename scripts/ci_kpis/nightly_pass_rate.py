#!/usr/bin/env python3
"""
Compute rolling pass rate for nightly provider CI workflows over the last N runs.

This script does not require network access during tests unless env var CI_KPI_ENABLE_NETWORK=true.
When network is disabled, it writes a placeholder JSON with instructions.

Outputs:
- test_reports/nightly_pass_rate.json

Env:
- GITHUB_REPOSITORY: owner/repo (optional; defaults to repo slug from git remotes if available)
- GITHUB_TOKEN: token with public_repo access (optional for public repos; needed for higher rate limits)
- WORKFLOW_NAME: name filter for nightly workflow (default: "ci_nightly_providers")
- ROLLING_N: integer number of runs to consider (default: 20)
- CI_KPI_ENABLE_NETWORK: set to "true" to enable GitHub API calls
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Dict

OUTPUT = pathlib.Path("test_reports/nightly_pass_rate.json")


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_placeholder(reason: str) -> None:
    ensure_parent(OUTPUT)
    data: dict[str, Any] = {
        "workflow": os.getenv("WORKFLOW_NAME", "ci_nightly_providers"),
        "rolling_n": int(os.getenv("ROLLING_N", "20")),
        "pass_rate": None,
        "total_runs": 0,
        "passed": 0,
        "failed": 0,
        "note": "placeholder; enable CI_KPI_ENABLE_NETWORK=true in CI to compute",
        "reason": reason,
    }
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(json.dumps(data, indent=2))


def main() -> None:
    if os.getenv("CI_KPI_ENABLE_NETWORK", "false").lower() != "true":
        write_placeholder("network disabled")
        return
    try:
        import httpx  # type: ignore
    except Exception:
        write_placeholder("httpx not available")
        return

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        write_placeholder("GITHUB_REPOSITORY not set")
        return

    workflow_name = os.getenv("WORKFLOW_NAME", "ci_nightly_providers")
    rolling_n = int(os.getenv("ROLLING_N", "20"))

    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_name}.yml/runs?per_page={rolling_n}"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        write_placeholder(f"fetch error: {e}")
        return

    runs = data.get("workflow_runs", [])[:rolling_n]
    total = len(runs)
    passed = sum(1 for r in runs if r.get("conclusion") == "success")
    failed = sum(
        1 for r in runs if r.get("conclusion") in {"failure", "timed_out", "cancelled"}
    )
    pass_rate = (passed / total) * 100.0 if total else None

    ensure_parent(OUTPUT)
    out = {
        "workflow": workflow_name,
        "rolling_n": rolling_n,
        "pass_rate": pass_rate,
        "total_runs": total,
        "passed": passed,
        "failed": failed,
    }
    OUTPUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
