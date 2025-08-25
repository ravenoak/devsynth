#!/usr/bin/env python3
"""
Run mypy type checking against src/devsynth with project settings.

Usage:
  poetry run python scripts/run_mypy_baseline.py [--strict-report]

Behavior:
- Executes: poetry run mypy src/devsynth (via python -m mypy)
- Prints a short summary and returns mypy's exit code.
- If --strict-report is provided, prints guidance to reduce overrides and
  reminds to address TODOs in modules listed in pyproject.toml [tool.mypy.overrides].

This supports docs/tasks.md item 4.1 (run mypy) and 4.2 (follow-up TODOs).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    strict_report = "--strict-report" in sys.argv
    cmd = [sys.executable, "-m", "mypy", "src/devsynth"]
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=ROOT)
    code = res.returncode
    if code == 0:
        print("mypy: no issues found.")
    else:
        print(f"mypy exited with code {code}.")
    if strict_report:
        print("\n[Strictness Guidance]")
        print(
            "- Review pyproject.toml [tool.mypy.overrides] and reduce relaxed settings as modules stabilize."
        )
        print(
            "- Address TODOs inside modules with relaxed strictness to restore disallow_untyped_defs/check_untyped_defs."
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
