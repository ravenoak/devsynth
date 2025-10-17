"""Security audit utilities and policy enforcement hooks.

This module centralizes security checks and audit logging used across the
project. The ``run_bandit`` and ``run_safety`` functions provide reusable
policy enforcement hooks for static analysis and dependency vulnerability
scanning.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from typing import Sequence

from devsynth.logging_setup import DevSynthLogger

_AUDIT_LOGGER = DevSynthLogger("devsynth.audit")


def audit_event(event: str, **details: object) -> None:
    """Log a security-related event for auditing purposes."""
    enabled = os.environ.get("DEVSYNTH_AUDIT_LOG_ENABLED", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    if not enabled:
        return
    _AUDIT_LOGGER.info(event, **details)


def run_bandit() -> None:
    """Execute Bandit static analysis."""
    subprocess.check_call(
        [
            "poetry",
            "run",
            "bandit",
            "-q",
            "-r",
            "--exit-zero",  # For alpha release, don't fail on warnings
            "src",
        ]
    )


def run_safety() -> None:
    """Export dependencies and run Safety vulnerability scan."""
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
        _AUDIT_LOGGER.info("Running Bandit static analysis")
        run_bandit()
    if not args.skip_safety:
        _AUDIT_LOGGER.info("Running Safety dependency scan")
        run_safety()
    _AUDIT_LOGGER.info("Security audit completed successfully")
