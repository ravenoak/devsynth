"""Security audit and monitoring automation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

REQUIRED_ENV_VARS = ["DEVSYNTH_ACCESS_TOKEN"]


def run_safety() -> None:
    """Run dependency vulnerability scan using safety."""
    subprocess.check_call(["python", "scripts/dependency_safety_check.py"])


def run_bandit() -> None:
    """Run Bandit static analysis over the src directory."""
    subprocess.check_call(["bandit", "-r", "src", "-ll"])


def check_required_env() -> None:
    """Ensure required security environment variables are set."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute security audits and monitoring checks.",
    )
    parser.add_argument(
        "--skip-static",
        action="store_true",
        help="Skip running Bandit static analysis",
    )
    args = parser.parse_args()

    from devsynth.application.cli.commands.security_audit_cmd import security_audit_cmd

    security_audit_cmd(skip_static=args.skip_static)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Security audit failed with code {exc.returncode}")
        sys.exit(exc.returncode)
