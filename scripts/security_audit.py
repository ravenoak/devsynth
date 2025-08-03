"""Security audit and monitoring automation."""

from __future__ import annotations

import argparse
import os
import re
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


def run_secrets_scan() -> None:
    """Detect potential API keys or secrets in the repository."""
    logger.info("Running secrets scan for potential API keys")
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
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    for lineno, line in enumerate(handle, start=1):
                        if pattern.search(line):
                            findings.append(f"{path}:{lineno}")
            except OSError:
                continue
    if findings:
        raise RuntimeError("Potential secrets detected:\n" + "\n".join(findings))


def run_owasp_dependency_check() -> None:
    """Run OWASP Dependency Check if available."""
    logger.info("Running OWASP Dependency Check")
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
        raise ConfigurationError(
            message=f"Missing required environment variables: {', '.join(missing)}"
        )
    logger.debug("All required security environment variables are set")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute security audits and monitoring checks.",
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
    args = parser.parse_args()

    check_required_env()
    logger.info("Starting security audit")

    from devsynth.application.cli.commands.security_audit_cmd import security_audit_cmd

    security_audit_cmd(
        skip_static=args.skip_bandit or args.skip_static,
        skip_safety=args.skip_safety,
        skip_secrets=args.skip_secrets,
        skip_owasp=args.skip_owasp,
    )
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
