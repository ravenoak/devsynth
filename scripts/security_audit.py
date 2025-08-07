"""Run static and dependency security checks."""

from __future__ import annotations

import subprocess
import sys

from devsynth.logger import setup_logging
from devsynth.security.audit import main as audit_main

logger = setup_logging(__name__)


if __name__ == "__main__":
    try:
        audit_main()
    except subprocess.CalledProcessError as exc:
        logger.exception("Security audit failed with code %s", exc.returncode)
        sys.exit(exc.returncode)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during security audit")
        sys.exit(1)
