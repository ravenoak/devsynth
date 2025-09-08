#!/usr/bin/env python3
"""
Run style checks for the DevSynth repository using Black and isort.

This helper mirrors the commands referenced in docs/tasks.md and project guidelines
so contributors can quickly validate formatting locally via Poetry.

Behavior:
- If run with --fix, it will apply Black and isort formatting in place.
- Otherwise, it runs in check-only mode and exits non-zero on violations.

Examples:
    poetry run python scripts/run_style_checks.py          # check only
    poetry run python scripts/run_style_checks.py --fix    # auto-fix

Exit codes:
- 0 on success (no issues, or successfully fixed when --fix)
- Non-zero if check fails (and --fix not provided) or if an unexpected error occurs.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List


def run(cmd: list[str]) -> int:
    """Run a subprocess command returning its exit code, printing the command for clarity."""
    print("$", " ".join(cmd))
    try:
        return subprocess.run(cmd, check=False).returncode
    except FileNotFoundError as e:
        print(
            f"Error: command not found: {cmd[0]}. Ensure dependencies are installed via Poetry.\n{e}"
        )
        return 127


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DevSynth style checks: Black and isort"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes instead of running in check-only mode",
    )
    args = parser.parse_args(argv)

    # Scope: run against project root
    # Black
    if args.fix:
        black_cmd = ["poetry", "run", "black", "."]
        isort_cmd = ["poetry", "run", "isort", "."]
    else:
        black_cmd = ["poetry", "run", "black", "--check", "."]
        isort_cmd = ["poetry", "run", "isort", "--check-only", "."]

    rc_black = run(black_cmd)
    rc_isort = run(isort_cmd)

    # Aggregate exit code
    if rc_black == 0 and rc_isort == 0:
        print("Style checks passed")
        return 0

    if args.fix:
        # If fixing, still return non-zero if one of the tools failed to run
        return 0 if (rc_black in (0,) and rc_isort in (0,)) else 1

    print(
        "Style checks failed. Run `poetry run python scripts/run_style_checks.py --fix` to auto-format."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
