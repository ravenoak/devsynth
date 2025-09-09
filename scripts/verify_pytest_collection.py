#!/usr/bin/env python3
"""
Verify pytest can collect tests without executing them.

Usage:
  poetry run python scripts/verify_pytest_collection.py [--verbose]

Behavior:
- Runs `pytest --collect-only -q` in repo root.
- Prints a short summary and exits with pytest's return code.
- No network; safe for local and CI usage.

This script follows project guidelines (clarity, determinism) and supports docs/tasks.md item 6.1.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    verbose = "--verbose" in sys.argv
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=not verbose)
    if verbose:
        # When verbose, rerun without capture to stream output
        subprocess.run(cmd, cwd=ROOT)
    else:
        out = (res.stdout or "").strip()
        if out:
            # Print last lines to avoid overwhelming logs
            lines = out.splitlines()
            tail = "\n".join(lines[-20:])
            print(tail)
    if res.returncode == 0:
        print("Pytest collection succeeded.")
    else:
        print(f"Pytest collection failed with code {res.returncode}.")
        if not verbose and res.stderr:
            print(res.stderr)
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
