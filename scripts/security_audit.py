"""Security audit and monitoring automation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_safety() -> None:
    """Run dependency vulnerability scan using safety."""
    subprocess.check_call(["python", "scripts/dependency_safety_check.py"])


def run_bandit() -> None:
    """Run Bandit static analysis over the src directory."""
    subprocess.check_call(["bandit", "-r", "src", "-ll"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute security audits and monitoring checks."
    )
    parser.add_argument(
        "--skip-static",
        action="store_true",
        help="Skip running Bandit static analysis",
    )
    args = parser.parse_args()

    run_safety()
    if not args.skip_static:
        run_bandit()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Security audit failed with code {exc.returncode}")
        sys.exit(exc.returncode)
