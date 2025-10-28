#!/usr/bin/env python3
"""
Release Sign-off Helper

Runs a minimal set of checks to generate evidence for docs/tasks.md Section 11.
- Marker discipline report (11.2)
- Pytest collect-only to ensure import sanity
- Prints guidance for running the full matrix and LM Studio paths

Usage:
  poetry run python scripts/release_signoff_check.py

Artifacts:
  - test_reports/test_markers_report.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_REPORTS = ROOT / "test_reports"
VERIFY_SCRIPT = ROOT / "scripts" / "verify_test_markers.py"


def run(cmd: list[str], env: dict[str, str] | None = None) -> int:
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env or os.environ.copy())
    return proc.returncode


def main() -> int:
    TEST_REPORTS.mkdir(exist_ok=True)

    # 1) Marker verification with report
    report_path = TEST_REPORTS / "test_markers_report.json"
    if not VERIFY_SCRIPT.exists():
        print(
            "verify_test_markers.py not found; cannot produce marker report.",
            file=sys.stderr,
        )
        return 2
    code = run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--report",
            "--report-file",
            str(report_path),
        ]
    )
    # Acceptance for 11.2 is strictly: zero speed marker violations.
    # verify_test_markers.py returns exit 0 iff there are no speed marker violations.
    marker_ok = code == 0

    # Parse report for informational fields only (do not gate acceptance on files_with_issues)
    files_with_issues = None
    try:
        if report_path.exists():
            with open(report_path, encoding="utf-8") as f:
                data = json.load(f)
            files_with_issues = int(data.get("files_with_issues", -1))
    except Exception as e:  # best-effort; surface but don't crash
        print(
            f"Warning: failed to parse marker report {report_path}: {e}",
            file=sys.stderr,
        )

    # 2) Collect-only sanity
    code_collect = run(
        ["poetry", "run", "pytest", "--collect-only", "-q"]
    )  # relies on Poetry env
    collect_ok = code_collect == 0

    # 3) Summarize
    summary = {
        "marker_ok": marker_ok,
        "marker_report": str(report_path),
        "files_with_issues": files_with_issues,
        "collect_ok": collect_ok,
        "hints": [
            "Run fast lanes: poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel",
            "Run segmented medium/slow: poetry run devsynth run-tests --target unit-tests --speed=medium --segment --segment-size 50 --no-parallel",
            "LM Studio offline skip: poetry run pytest -q -m \"requires_resource('lmstudio') and not slow\"",
            "LM Studio enabled (after installing extras and exporting flags): poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 --marker \"requires_resource('lmstudio') and not slow\"",
        ],
    }
    print("\nSummary:")
    print(json.dumps(summary, indent=2))

    return 0 if marker_ok and collect_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
