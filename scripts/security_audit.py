"""Run Bandit static analysis and Safety dependency checks.

Ensures required pre-deployment policy gates have been approved before
executing the audits.
"""

from __future__ import annotations

import subprocess
import sys

from devsynth.logger import setup_logging
from devsynth.security import audit
from devsynth.security.validation import require_pre_deploy_checks

logger = setup_logging(__name__)


def run() -> None:
    """Execute Bandit and Safety security checks."""
    require_pre_deploy_checks()
    audit.run_bandit()
    audit.run_safety()


if __name__ == "__main__":
    try:
        run()
    except subprocess.CalledProcessError as exc:
        logger.exception("Security audit failed with code %s", exc.returncode)
        sys.exit(exc.returncode)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during security audit")
        sys.exit(1)
