"""CLI command to run DevSynth security audits.

Wraps dependency vulnerability scanning and optional static code
analysis. This command mirrors the behaviour of ``scripts/security_audit.py``
so that the audit can be executed via the ``devsynth`` CLI.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()

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


def security_audit_cmd(
    skip_static: bool = False, *, bridge: Optional[UXBridge] = None
) -> None:
    """Execute security audits and monitoring checks.

    Example:
        ``devsynth security-audit --skip-static``

    Args:
        skip_static: Skip running Bandit static analysis when ``True``.
        bridge: Optional UX bridge for user feedback.
    """
    bridge = bridge or globals()["bridge"]

    bridge.display_result("[blue]Running security audit checks...[/blue]")
    check_required_env()
    run_safety()
    if not skip_static:
        run_bandit()
    bridge.display_result("[green]Security audit completed successfully.[/green]")
