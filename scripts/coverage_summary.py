#!/usr/bin/env python3
"""
Quick helper to print overall coverage percent from coverage.json if present.
Generates coverage.json via pytest if missing.
Usage:
  poetry run python scripts/coverage_summary.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    cov_json = repo / "coverage.json"
    if not cov_json.exists():
        # Generate minimal coverage json without html to save time
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--maxfail=1",
            "--disable-warnings",
            "--cov=src/devsynth",
            "--cov-report=json:coverage.json",
        ]
        print("[info] Generating coverage.json via:", " ".join(cmd))
        try:
            subprocess.run(cmd, cwd=repo, check=False)
        except Exception as e:
            print("[warn] pytest run raised:", e)
    if not cov_json.exists():
        print("[error] coverage.json not found; unable to summarize.")
        return 2
    data = json.loads(cov_json.read_text())
    totals = data.get("totals") or {}
    percent = totals.get("percent_covered")
    if percent is None:
        print("[error] totals.percent_covered not found in coverage.json")
        return 3
    print(f"overall_coverage_percent={percent:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
