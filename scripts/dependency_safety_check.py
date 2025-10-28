#!/usr/bin/env python3
"""Run static analysis and dependency safety checks.

This script exports project dependencies and executes a vulnerability scan
using ``safety`` and runs ``bandit`` for static analysis. Optionally, it can
run ``poetry update`` before checking and supports skipping individual tools.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence


def run_bandit() -> None:
    """Execute Bandit static analysis."""
    subprocess.check_call(["poetry", "run", "bandit", "-q", "-r", "src"])


def run_safety() -> None:
    """Export dependencies and execute ``safety``."""
    req_file = tempfile.NamedTemporaryFile("w+", delete=False)
    try:
        subprocess.check_call(
            [
                "poetry",
                "export",
                "--without-hashes",
                "-f",
                "requirements.txt",
                "--output",
                req_file.name,
            ]
        )
        subprocess.check_call(
            [
                "poetry",
                "run",
                "safety",
                "check",
                "--file",
                req_file.name,
                "--full-report",
            ]
        )
    finally:
        req_file.close()
        os.unlink(req_file.name)


def run_update() -> None:
    """Update project dependencies using ``poetry``."""
    subprocess.check_call(["poetry", "update"])


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and run the desired commands."""
    parser = argparse.ArgumentParser(
        description="Run dependency safety checks or update dependencies.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run 'poetry update' before running checks.",
    )
    parser.add_argument(
        "--skip-bandit",
        action="store_true",
        help="Skip Bandit static analysis.",
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="Skip Safety dependency vulnerability scan.",
    )
    args = parser.parse_args(argv)

    if args.update:
        run_update()
    if not args.skip_bandit:
        run_bandit()
    if not args.skip_safety:
        run_safety()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with code {exc.returncode}")
        sys.exit(exc.returncode)
