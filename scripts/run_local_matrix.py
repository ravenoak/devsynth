#!/usr/bin/env python3
"""
Run a local subset of the Section 8 test matrix and save diagnostics.

This helper is intended for maintainers to validate fast lanes without
introducing heavy third-party plugin surface. It invokes the "devsynth run-tests"
wrapper using conservative options and stores outputs under diagnostics/.

Usage:
  poetry run python scripts/run_local_matrix.py --fast-only
  poetry run python scripts/run_local_matrix.py --all

Notes:
- Honors existing environment; does not force smoke mode unless --smoke is passed.
- Sets DEVSYNTH_INNER_TEST=1 to reduce plugin surface in inner subprocesses
  while preserving normal CLI behavior (no PYTEST_DISABLE_PLUGIN_AUTOLOAD by default).
- Returns non-zero if any lane fails.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def _run_cmd(cmd: list[str], log_path: Path) -> tuple[int, str]:
    env = os.environ.copy()
    # Hint inner subprocesses to minimize plugin surface and be deterministic
    env.setdefault("DEVSYNTH_INNER_TEST", "1")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
    )
    out, err = proc.communicate()
    payload = out + ("\nERRORS:\n" + err if err else "")
    log_path.write_text(payload)
    return proc.returncode, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all", action="store_true", help="Run fast + segmented medium/slow lanes"
    )
    parser.add_argument(
        "--fast-only",
        action="store_true",
        help="Run only fast unit/integration/behavior lanes",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run behavior fast lane in smoke mode as per docs",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Include --report to generate HTML reports where supported",
    )
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    diag_dir = Path("diagnostics") / f"local_matrix_{ts}"

    lanes: list[tuple[str, list[str]]] = []

    # Section 8.2 fast lanes
    lanes.append(
        (
            "unit_fast",
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--target",
                "unit-tests",
                "--speed",
                "fast",
                "--no-parallel",
                "--maxfail=1",
            ],
        )
    )
    lanes.append(
        (
            "integration_fast",
            [
                "poetry",
                "run",
                "devsynth",
                "run-tests",
                "--target",
                "integration-tests",
                "--speed",
                "fast",
                "--no-parallel",
                "--maxfail=1",
            ],
        )
    )
    behavior_cmd = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--target",
        "behavior-tests",
        "--speed",
        "fast",
        "--no-parallel",
        "--maxfail=1",
    ]
    if args.smoke:
        behavior_cmd.append("--smoke")
    lanes.append(("behavior_fast", behavior_cmd))

    if args.all:
        # Section 8.3 segmentation guidance for medium/slow unit-tests
        lanes.append(
            (
                "unit_medium_segmented",
                [
                    "poetry",
                    "run",
                    "devsynth",
                    "run-tests",
                    "--target",
                    "unit-tests",
                    "--speed",
                    "medium",
                    "--segment",
                    "--segment-size",
                    "50",
                    "--no-parallel",
                ]
                + (["--report"] if args.report else []),
            )
        )
        lanes.append(
            (
                "unit_slow_segmented",
                [
                    "poetry",
                    "run",
                    "devsynth",
                    "run-tests",
                    "--target",
                    "unit-tests",
                    "--speed",
                    "slow",
                    "--segment",
                    "--segment-size",
                    "50",
                    "--no-parallel",
                ]
                + (["--report"] if args.report else []),
            )
        )
        # Optionally extend to integration/behavior segmented lanes as guidance suggests (repeat as needed)

    overall_rc = 0
    summary_lines: list[str] = []
    for name, cmd in lanes:
        log_path = diag_dir / f"{name}.txt"
        rc, _ = _run_cmd(cmd, log_path)
        status = "OK" if rc in (0, 5) else f"FAIL({rc})"
        summary_lines.append(f"{name}: {status} -> {log_path}")
        if rc not in (0, 5):
            overall_rc = 1

    (diag_dir / "SUMMARY.txt").write_text("\n".join(summary_lines) + "\n")
    print("\n".join(summary_lines))
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
