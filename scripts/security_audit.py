"""Run static and dependency security checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from typing import Sequence

from devsynth.logger import setup_logging

logger = setup_logging(__name__)


def run_bandit() -> None:
    """Execute Bandit static analysis."""
    subprocess.check_call(
        [
            "poetry",
            "run",
            "bandit",
            "-q",
            "-r",
            "src",
        ]
    )


def run_safety() -> None:
    """Export dependencies and run Safety vulnerability scan."""
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


def main(argv: Sequence[str] | None = None) -> None:
    """Run Bandit and Safety unless explicitly skipped."""

    parser = argparse.ArgumentParser(
        description="Run Bandit static analysis and Safety dependency scan.",
    )
    parser.add_argument(
        "--skip-bandit",
        "--skip-static",
        action="store_true",
        help="Skip running Bandit static analysis",
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="Skip dependency vulnerability scan using Safety",
    )
    args = parser.parse_args(argv)

    if not args.skip_bandit:
        logger.info("Running Bandit static analysis")
        run_bandit()
    if not args.skip_safety:
        logger.info("Running Safety dependency scan")
        run_safety()
    logger.info("Security audit completed successfully")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        logger.exception("Security audit failed with code %s", exc.returncode)
        sys.exit(exc.returncode)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during security audit")
        sys.exit(1)
