"""Deprecated wrapper for the security audit command.

This script is retained for backward compatibility and simply invokes
``devsynth security-audit``. It will be removed in a future release.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Sequence

from devsynth.logger import setup_logging

logger = setup_logging(__name__)


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and invoke ``devsynth security-audit``."""
    parser = argparse.ArgumentParser(
        description="Deprecated wrapper for `devsynth security-audit`.",
    )
    parser.add_argument(
        "--skip-bandit",
        action="store_true",
        help="Skip running Bandit static analysis",
    )
    parser.add_argument(
        "--skip-static",
        action="store_true",
        help="Alias for --skip-bandit",
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="Skip dependency vulnerability scan using safety",
    )
    parser.add_argument(
        "--skip-secrets",
        action="store_true",
        help="Skip secrets scanning",
    )
    parser.add_argument(
        "--skip-owasp",
        action="store_true",
        help="Skip OWASP Dependency Check",
    )
    args = parser.parse_args(argv)

    cmd = ["devsynth", "security-audit"]
    if args.skip_bandit or args.skip_static:
        cmd.append("--skip-static")
    if args.skip_safety:
        cmd.append("--skip-safety")
    if args.skip_secrets:
        cmd.append("--skip-secrets")
    if args.skip_owasp:
        cmd.append("--skip-owasp")

    logger.info("Invoking devsynth security-audit")
    subprocess.run(cmd, check=True)
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

