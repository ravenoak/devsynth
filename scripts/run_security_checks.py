#!/usr/bin/env python3
"""
run_security_checks.py

Run flake8, bandit, and safety across the repository. Provides clear messages
and non-zero exits on findings. Designed to be CI-friendly and local-friendly.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import List


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    exit_code = 0

    flake8 = shutil.which("flake8")
    bandit = shutil.which("bandit")
    safety = shutil.which("safety") or shutil.which("safety4")  # some envs use safety4

    if not flake8:
        print("flake8 not found. Install dev deps: poetry install --with dev")
        exit_code |= 2
    else:
        exit_code |= run([flake8, "src/", "tests/"])

    if not bandit:
        print("bandit not found. Install dev deps: poetry install --with dev")
        exit_code |= 2
    else:
        # Exclude tests to focus on app code as per tasks.md guidance
        exit_code |= run([bandit, "-r", "src/devsynth", "-x", "tests"])

    if not safety:
        print("safety not found. Install dev deps: poetry install --with dev")
        exit_code |= 2
    else:
        # Full report provides clearer context; allow exit code on vulns
        exit_code |= run([safety, "check", "--full-report"])

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
