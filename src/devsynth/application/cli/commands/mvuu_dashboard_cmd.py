"""[experimental] CLI command to launch the MVUU dashboard.

This command is intentionally lightweight so it can be safely imported and used
in smoke tests. It supports a --no-run mode to validate wiring without starting
external processes. It also supports --help via argparse.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def mvuu_dashboard_cmd(argv: list[str] | None = None) -> int:
    """Launch the MVUU traceability dashboard.

    Args:
        argv: Optional list of CLI arguments (used for testing). Defaults to
            None to read from sys.argv.

    Returns:
        Process exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="mvuu-dashboard", description="Launch the MVUU traceability dashboard"
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Validate wiring only; do not execute external subprocesses.",
    )
    args = parser.parse_args(argv)

    if args.no_run:
        return 0

    repo_root = Path(__file__).resolve().parents[3]
    trace_path = repo_root / "traceability.json"
    subprocess.run(
        ["devsynth", "mvu", "report", "--output", str(trace_path)],
        check=False,
    )
    script_path = repo_root / "interface" / "mvuu_dashboard.py"
    subprocess.run(["streamlit", "run", str(script_path)], check=False)
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    sys.exit(mvuu_dashboard_cmd())
