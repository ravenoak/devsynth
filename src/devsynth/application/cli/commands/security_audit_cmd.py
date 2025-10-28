"""CLI command to run DevSynth security audits.

Wraps dependency vulnerability scanning and optional static code
analysis. This command mirrors the behaviour of ``scripts/security_audit.py``
so that the audit can be executed via the ``devsynth`` CLI.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Optional

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.security import audit

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()

REQUIRED_ENV_VARS = ["DEVSYNTH_ACCESS_TOKEN"]


def run_secrets_scan() -> None:
    """Detect potential API keys or secrets in the repository."""
    pattern = re.compile(
        r"(?:api_key|token|secret)[\'\"]?\s*[:=]\s*[\'\"][A-Za-z0-9-_]{16,}[\'\"]",
        re.IGNORECASE,
    )
    findings: list[str] = []
    for root, _dirs, files in os.walk("."):
        for name in files:
            if not name.endswith(
                (".py", ".env", ".txt", ".md", ".cfg", ".ini", ".yaml", ".yml", ".json")
            ):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    for lineno, line in enumerate(handle, start=1):
                        if pattern.search(line):
                            findings.append(f"{path}:{lineno}")
            except OSError:
                continue
    if findings:
        raise RuntimeError("Potential secrets detected:\n" + "\n".join(findings))


def run_owasp_dependency_check() -> None:
    """Run OWASP Dependency Check if available."""
    try:
        subprocess.check_call(
            [
                "dependency-check",
                "--project",
                "DevSynth",
                "--format",
                "JSON",
                "--out",
                "owasp_report",
            ]
        )
    except FileNotFoundError as exc:  # pragma: no cover - external tool
        raise RuntimeError("dependency-check executable not found") from exc


def check_required_env() -> None:
    """Ensure required security environment variables are set."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def security_audit_cmd(
    skip_static: bool = False,
    skip_safety: bool = False,
    skip_secrets: bool = False,
    skip_owasp: bool = False,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Execute security audits and monitoring checks.

    Example:
        ``devsynth security-audit --skip-owasp``

    Args:
        skip_static: Skip running Bandit static analysis when ``True``.
        skip_safety: Skip dependency vulnerability scan when ``True``.
        skip_secrets: Skip secrets scanning when ``True``.
        skip_owasp: Skip OWASP Dependency Check when ``True``.
        bridge: Optional UX bridge for user feedback.
    """
    bridge = bridge or globals()["bridge"]

    bridge.display_result("[blue]Running security audit checks...[/blue]")
    check_required_env()
    if not skip_safety:
        audit.run_safety()
    if not skip_static:
        audit.run_bandit()
    if not skip_secrets:
        run_secrets_scan()
    if not skip_owasp:
        run_owasp_dependency_check()
    bridge.display_result("[green]Security audit completed successfully.[/green]")
