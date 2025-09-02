#!/usr/bin/env python3
"""
Run repository guardrails and emit an evidence summary.

Checks:
- Black --check .
- Isort --check-only .
- Flake8 src/ tests/
- Mypy src/devsynth (uses strict config with overrides from pyproject)
- Bandit -r src/devsynth -x tests
- Safety check --full-report (expects safety.json present or network access)

Artifacts:
- diagnostics/guardrails_<timestamp>/summary.json
- Diagnostics stdout/stderr are printed live; summary contains exit codes.

Usage:
  poetry run python scripts/run_guardrails.py

Exit codes:
  0 if all checks returned exit code 0
  1 otherwise
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG_DIR = ROOT / "diagnostics"


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = DIAG_DIR / f"guardrails_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, int] = {}

    # Formatters
    results["black"] = run(["poetry", "run", "black", "--check", "."])
    results["isort"] = run(["poetry", "run", "isort", "--check-only", "."])

    # Linters / typing
    results["flake8"] = run(["poetry", "run", "flake8", "src/", "tests/"])
    results["mypy"] = run(["poetry", "run", "mypy", "src/devsynth"])

    # Security
    results["bandit"] = run(["poetry", "run", "bandit", "-r", "src/devsynth", "-x", "tests"])

    # Safety: prefer offline DB if safety.json exists; otherwise run online check
    safety_db = ROOT / "safety.json"
    if safety_db.exists():
        results["safety"] = run(["poetry", "run", "safety", "check", "--full-report", "--db", str(safety_db)])
    else:
        results["safety"] = run(["poetry", "run", "safety", "check", "--full-report"])

    summary = {
        "timestamp": ts,
        "results": results,
        "all_passed": all(code == 0 for code in results.values()),
        "hints": [
            "You can relax strict typing temporarily via [tool.mypy.overrides] in pyproject.toml (document TODOs).",
            "Use poetry install --with dev to ensure all tools are available.",
        ],
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nGuardrails summary:\n" + json.dumps(summary, indent=2))

    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
