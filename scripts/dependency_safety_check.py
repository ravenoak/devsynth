#!/usr/bin/env python3
"""Run safety checks and optional dependency updates.

This script exports project dependencies and executes a vulnerability scan using
``safety``. Optionally, it can run ``poetry update`` before checking.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile


def run_safety() -> None:
    """Export dependencies and execute ``safety``."""
    with tempfile.NamedTemporaryFile("w+", delete=False) as req_file:
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
            ["safety", "check", "--file", req_file.name, "--full-report"]
        )


def run_update() -> None:
    """Update project dependencies using ``poetry``."""
    subprocess.check_call(["poetry", "update"])


def main() -> None:
    """Parse arguments and run the desired commands."""
    parser = argparse.ArgumentParser(
        description="Run dependency safety checks or update dependencies."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run 'poetry update' before the safety check.",
    )
    args = parser.parse_args()

    if args.update:
        run_update()
    run_safety()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with code {exc.returncode}")
        sys.exit(exc.returncode)
