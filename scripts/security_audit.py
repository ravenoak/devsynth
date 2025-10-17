"""Run Bandit static analysis and Safety dependency checks.

Ensures required pre-deployment policy gates have been approved before
executing the audits.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import verify_security_policy

from devsynth.logger import setup_logging
from devsynth.security import audit
from devsynth.security.validation import require_pre_deploy_checks

logger = setup_logging(__name__)


def run(argv: list[str] | None = None) -> dict[str, str]:
    """Validate security flags then execute Bandit and Safety checks.

    Returns a mapping of each check to its status (`passed`, `failed`, or
    `skipped`).
    """
    parser = argparse.ArgumentParser(
        description="Run Bandit static analysis and Safety dependency scan.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write JSON report of audit results",
    )
    parser.add_argument(
        "--skip-bandit",
        action="store_true",
        help="Skip running Bandit static analysis",
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="Skip dependency vulnerability scan",
    )
    parser.add_argument(
        "--version",
        default="0.1.0a1",
        help="Version for validation (default: 0.1.0a1)",
    )
    parser.add_argument(
        "--env",
        default="alpha",
        help="Environment for validation (default: alpha)",
    )
    args = parser.parse_args(argv)

    # Ensure environment variables are available for validation
    os.environ['DEVSYNTH_VERSION'] = args.version
    os.environ['DEVSYNTH_ENV'] = args.env

    print(f"[security_audit] Environment: DEVSYNTH_VERSION={os.environ.get('DEVSYNTH_VERSION', 'NOT_SET')}, DEVSYNTH_ENV={os.environ.get('DEVSYNTH_ENV', 'NOT_SET')}")
    require_pre_deploy_checks()
    if verify_security_policy.main() != 0:
        raise subprocess.CalledProcessError(1, "verify_security_policy")

    results: dict[str, str] = {}
    try:
        if args.skip_bandit:
            results["bandit"] = "skipped"
        else:
            audit.run_bandit()
            results["bandit"] = "passed"
        if args.skip_safety:
            results["safety"] = "skipped"
        else:
            audit.run_safety()
            results["safety"] = "passed"
    except subprocess.CalledProcessError as exc:
        if "bandit" not in results:
            results["bandit"] = "failed"
            results["safety"] = "skipped"
        else:
            results["safety"] = "failed"
        raise
    finally:
        if args.report:
            args.report.write_text(json.dumps(results, indent=2))

    return results


if __name__ == "__main__":
    try:
        run()
    except subprocess.CalledProcessError as exc:
        logger.exception("Security audit failed with code %s", exc.returncode)
        sys.exit(exc.returncode)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during security audit")
        sys.exit(1)
