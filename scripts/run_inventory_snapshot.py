#!/usr/bin/env python3
"""
Run a lightweight inventory of tests via devsynth's run-tests command and save the
output to diagnostics/devsynth_inventory_<timestamp>.txt.

Usage:
  poetry run python scripts/run_inventory_snapshot.py [--target unit-tests] [--speed fast] [--smoke]

Notes:
- Uses only the Python standard library; avoids optional dependencies.
- --smoke sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 to reduce plugin surface area.
- Aligns with docs/plan.md and docs/tasks.md §8.1 inventory guidance.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIAG_DIR = REPO_ROOT / "diagnostics"


def timestamp() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture devsynth test inventory output"
    )
    parser.add_argument(
        "--target",
        default="unit-tests",
        choices=["all-tests", "unit-tests", "integration-tests", "behavior-tests"],
        help="Test target for inventory (default: unit-tests)",
    )
    parser.add_argument(
        "--speed",
        default="fast",
        choices=["fast", "medium", "slow"],
        help="Speed marker to inventory (default: fast)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run in smoke mode (disable 3rd-party plugins)",
    )
    args = parser.parse_args(argv)

    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DIAG_DIR / f"devsynth_inventory_{timestamp()}.txt"

    env = os.environ.copy()
    # devsynth docs recommend stub provider/offline by default during tests
    env.setdefault("DEVSYNTH_PROVIDER", "stub")
    env.setdefault("DEVSYNTH_OFFLINE", "true")
    if args.smoke:
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "devsynth",
        "run-tests",
        "--inventory",
        "--target",
        args.target,
        "--speed",
        args.speed,
    ]
    if args.smoke:
        cmd.append("--smoke")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        out_path.write_text(proc.stdout)
        print(str(out_path))
        return proc.returncode
    except FileNotFoundError as e:
        # devsynth may not be importable; provide helpful guidance
        sys.stderr.write(
            f"Error: failed to run inventory. Ensure dev environment is set up via Poetry. Details: {e}\n"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
