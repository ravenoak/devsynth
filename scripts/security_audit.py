"""Security audit and monitoring automation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from utils.logging_setup import setup_logging

from devsynth.exceptions import ConfigurationError, DevSynthError

REQUIRED_ENV_VARS = ["DEVSYNTH_ACCESS_TOKEN"]


logger = setup_logging(__name__)


def run_safety() -> None:
    """Run dependency vulnerability scan using safety."""
    logger.info("Running dependency vulnerability scan using safety")
    subprocess.check_call(["python", "scripts/dependency_safety_check.py"])


def run_bandit() -> None:
    """Run Bandit static analysis over the src directory."""
    logger.info("Running Bandit static analysis over the src directory")
    subprocess.check_call(["bandit", "-r", "src", "-ll"])


def check_required_env() -> None:
    """Ensure required security environment variables are set."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise ConfigurationError(
            message=f"Missing required environment variables: {', '.join(missing)}"
        )
    logger.debug("All required security environment variables are set")


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

    check_required_env()
    logger.info("Starting security audit")

    from devsynth.application.cli.commands.security_audit_cmd import security_audit_cmd

    security_audit_cmd(skip_static=args.skip_static)
    logger.info("Security audit completed successfully")


if __name__ == "__main__":
    try:
        main()
    except DevSynthError:
        logger.exception("Security audit failed")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        logger.exception("Security audit failed with code %s", exc.returncode)
        sys.exit(exc.returncode)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during security audit")
        sys.exit(1)
