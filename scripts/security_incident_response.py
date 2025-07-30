#!/usr/bin/env python3
"""Security incident response helper."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LOG_DIR = Path("logs")


def collect_logs(output: Path) -> None:
    """Archive logs directory to the given output path."""
    if not LOG_DIR.exists():
        print(f"No logs directory found at {LOG_DIR}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(output.with_suffix("")), "zip", LOG_DIR)


def run_audit() -> None:
    """Run the existing security audit script."""
    subprocess.check_call(["python", "scripts/security_audit.py"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect logs and run security audit for incident response."
    )
    parser.add_argument(
        "--collect-logs",
        action="store_true",
        help="Archive logs directory into INCIDENT.zip",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run scripts/security_audit.py as part of the response",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("incident"),
        help="Base name for the archived logs",
    )
    args = parser.parse_args()

    if args.collect_logs:
        collect_logs(args.output)

    if args.audit:
        run_audit()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - script entry
        print(f"Incident response script failed: {exc}")
        sys.exit(1)
