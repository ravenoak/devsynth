#!/usr/bin/env python3
"""
Identify potentially flaky tests by running the fast test suite twice under
stable conditions and comparing failures.

Usage:
  poetry run python scripts/identify_flaky_tests.py

Behavior:
- Forces conservative environment for smoke-like runs (no third-party plugin
  autoload, no parallel, offline/stub providers, short timeouts).
- Runs tests with speed=fast twice via devsynth.testing.run_tests.
- Parses pytest output to find failed test nodes, compares runs, and outputs a
  JSON report under test_reports/flaky_report.json.

Notes:
- Parsing of failures is heuristic (looks for lines starting with "FAILED ")
  and may miss edge cases, but is sufficient for quick flakiness detection.
- This script does not modify tests; it only reports.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple

from devsynth.testing.run_tests import run_tests


def _stable_env() -> None:
    # Minimize plugin surface and side effects
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    # Ensure offline/stub defaults for providers
    os.environ.setdefault("DEVSYNTH_PROVIDER", "stub")
    os.environ.setdefault("DEVSYNTH_OFFLINE", "true")
    # Reasonable timeout to catch hangs but avoid flakiness
    os.environ.setdefault("DEVSYNTH_TEST_TIMEOUT_SECONDS", "10")


def _parse_failed_tests(output: str) -> set[str]:
    failed: set[str] = set()
    # Common patterns include lines like:
    #   FAILED tests/unit/foo/test_bar.py::test_baz - AssertionError: ...
    #   === 1 failed, 2 passed in 0.12s ===
    # We'll capture nodeids following "FAILED ".
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("FAILED "):
            # Extract the token after FAILED
            rest = line[len("FAILED ") :].strip()
            # Node id ends before first space (usually), but may have a dash
            # after node id. Split on space to be safe.
            nodeid = rest.split(" ", 1)[0]
            # Basic sanity: must look like a test path
            if nodeid.startswith("tests/"):
                failed.add(nodeid)
    return failed


def _run_fast_suite() -> tuple[bool, str, set[str]]:
    success, output = run_tests(
        target="all-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,  # no xdist for stability
        segment=False,
        segment_size=50,
        maxfail=None,
    )
    failed = _parse_failed_tests(output)
    return success, output, failed


def main() -> int:
    _stable_env()

    print("[identify_flaky_tests] Running fast suite pass #1...")
    s1, out1, f1 = _run_fast_suite()
    print(f"[identify_flaky_tests] Pass #1 success={s1}, failures={len(f1)}")

    print("[identify_flaky_tests] Running fast suite pass #2...")
    s2, out2, f2 = _run_fast_suite()
    print(f"[identify_flaky_tests] Pass #2 success={s2}, failures={len(f2)}")

    # Flaky candidates are tests that failed in only one of the runs
    flaky = sorted(list(f1 ^ f2))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "flaky_report.json"

    report = {
        "timestamp": timestamp,
        "run1": {"success": s1, "failed": sorted(list(f1))},
        "run2": {"success": s2, "failed": sorted(list(f2))},
        "flaky_candidates": flaky,
        "notes": "Heuristic detection via double run under stable conditions.",
    }
    report_path.write_text(json.dumps(report, indent=2))

    print(f"[identify_flaky_tests] Report written to {report_path}")
    if flaky:
        print("[identify_flaky_tests] Potentially flaky tests detected:")
        for node in flaky:
            print(f"  - {node}")
    else:
        print("[identify_flaky_tests] No flaky candidates detected.")

    # Non-zero exit if flaky tests were found, to be CI-consumable.
    return 1 if flaky else 0


if __name__ == "__main__":
    raise SystemExit(main())
