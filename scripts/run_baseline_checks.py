#!/usr/bin/env python3
"""
Run baseline lint/typing/security checks for DevSynth, aligned with project guidelines
and docs/tasks.md §0.7. This wrapper centralizes commands and provides
concise, deterministic output suitable for notes and CI logs.

Checks included:
- Black (check)
- isort (check-only)
- Flake8 (src/ and tests/)
- mypy (src/devsynth)
- Bandit (exclude tests)
- Safety (full report)

Usage:
    poetry run python scripts/run_baseline_checks.py          # run all checks
    poetry run python scripts/run_baseline_checks.py --fail-fast

Exit codes:
- 0 if all checks pass
- Non-zero if any check fails; prints a summary table at the end
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    try:
        return subprocess.run(cmd, check=False).returncode
    except FileNotFoundError as e:
        print(
            "Error: command not found: "
            f"{cmd[0]} — ensure Poetry extras are installed.\n{e}"
        )
        return 127


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DevSynth baseline checks runner")
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )
    args = parser.parse_args(argv)

    checks: list[tuple[str, list[str]]] = [
        ("black", ["poetry", "run", "black", "--check", "."]),
        ("isort", ["poetry", "run", "isort", "--check-only", "."]),
        ("flake8", ["poetry", "run", "flake8", "src/", "tests/"]),
        ("mypy", ["poetry", "run", "mypy", "src/devsynth"]),
        ("bandit", ["poetry", "run", "bandit", "-r", "src/devsynth", "-x", "tests"]),
        ("safety", ["poetry", "run", "safety", "check", "--full-report"]),
    ]

    failures: list[str] = []

    for name, cmd in checks:
        rc = run(cmd)
        if rc != 0:
            print(f"[FAIL] {name} exited with {rc}")
            failures.append(name)
            if args.fail_fast:
                break
        else:
            print(f"[OK]   {name}")

    if failures:
        print("\nSummary: some checks failed →", ", ".join(failures))
        return 1

    print("\nSummary: all baseline checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
