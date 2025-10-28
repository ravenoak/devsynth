#!/usr/bin/env python3
"""
check_env_and_collection.py

Purpose: Provide a quick, automated verification of the local development
environment and baseline test collection as outlined in docs/tasks.md tasks 1 and 2.

It checks:
- Python version is 3.12.x (>=3.12,<3.13)
- Poetry is available
- Optional: verifies Poetry can see the project and that dependencies are installed
- Runs baseline test collection via pytest and devsynth run-tests

Exit codes:
- 0 on success
- non-zero on failures; prints actionable guidance

Run with Poetry to ensure the right environment:
  poetry run python scripts/diagnostics/check_env_and_collection.py
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import List


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return 127


def check_python_version() -> bool:
    ver = sys.version_info
    ok = ver.major == 3 and ver.minor == 12
    if not ok:
        print(
            f"Python version requirement not met: found {platform.python_version()}, "
            "expected 3.12.x (>=3.12,<3.13).\n"
            "Tip: use pyenv or asdf to install Python 3.12 and configure Poetry to use it."
        )
    else:
        print(f"Python version OK: {platform.python_version()}")
    return ok


def check_poetry_available() -> bool:
    poetry = shutil.which("poetry")
    if not poetry:
        print(
            "Poetry is not available on PATH. Install from https://python-poetry.org/ and retry."
        )
        return False
    print(f"Poetry found: {poetry}")
    return True


def verify_install_hint() -> None:
    # Provide a gentle hint; this script does not install dependencies by itself.
    print(
        "If dependencies are not installed yet, run one of:\n"
        '  poetry install --with dev --extras "tests retrieval chromadb api"\n'
        "  poetry install --with dev --extras minimal\n"
        "  poetry install --with dev,docs --all-extras\n"
    )


def baseline_collection() -> int:
    exit_code = 0
    # 1) pytest collection
    exit_code |= run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    )  # assumes poetry run context

    # 2) devsynth run-tests unit fast, no-parallel, maxfail=1
    # Ensure PYTEST_DISABLE_PLUGIN_AUTOLOAD is not forced here to mimic normal baseline.
    env = os.environ.copy()
    cmd = [
        "devsynth",
        "run-tests",
        "--target",
        "unit-tests",
        "--speed=fast",
        "--no-parallel",
        "--maxfail=1",
    ]
    print("$", "poetry run", " ".join(cmd))
    # When executed under `poetry run python`, 'devsynth' should be visible.
    exit_code |= subprocess.call(cmd, env=env)
    return exit_code


def main() -> int:
    overall_ok = True

    ok_py = check_python_version()
    overall_ok &= ok_py

    ok_poetry = check_poetry_available()
    overall_ok &= ok_poetry

    verify_install_hint()

    if not overall_ok:
        return 2

    # Attempt baseline collection; if it fails, provide a remediation hint.
    code = baseline_collection()
    if code != 0:
        print(
            "Baseline collection reported errors.\n"
            "Try running installs per the hints above, then re-run this script.\n"
            "If plugins cause hangs, try smoke mode:\n"
            "  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1\n"
        )
        return code or 1

    print("Environment and baseline collection checks completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
