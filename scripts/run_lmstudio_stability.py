#!/usr/bin/env python3
"""
Run the LM Studio-enabled subset 3 times and capture standardized diagnostics.

This helper supports docs/tasks.md Task 3.5 (Validate enabled stability) by
executing a targeted subset three consecutive times with --no-parallel and
--maxfail=1, writing outputs under diagnostics/.

Usage (example):
  poetry run python scripts/run_lmstudio_stability.py \
    --marker "requires_resource('lmstudio') and not slow" \
    --target integration-tests --speed fast --no-parallel --maxfail 1

Environment (per docs/tasks.md §3.4):
  - poetry install --with dev --extras "tests llm"
  - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  - export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10
  - export DEVSYNTH_LMSTUDIO_RETRIES=1

This script does not modify environment flags; it relies on the caller to set them.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def build_command(args: argparse.Namespace) -> list[str]:
    cmd: list[str] = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--target",
        args.target,
    ]
    # --speed can be repeatable; accept multiple values via nargs
    for sp in args.speed:
        cmd.extend(["--speed", sp])
    if args.no_parallel:
        cmd.append("--no-parallel")
    if args.smoke:
        cmd.append("--smoke")
    if args.maxfail is not None:
        cmd.extend(["--maxfail", str(args.maxfail)])
    if args.segment:
        cmd.append("--segment")
        if args.segment_size:
            cmd.extend(["--segment-size", str(args.segment_size)])
    # Pass marker expression at the end (pytest -m)
    if args.marker:
        cmd.extend(["-m", args.marker])
    return cmd


def run_once(i: int, base_cmd: list[str], diagnostics_dir: Path) -> int:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_file = diagnostics_dir / f"lmstudio_stability_run{i}_{ts}.txt"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    # Stream output to both console and file (tee-like behavior)
    with out_file.open("w", encoding="utf-8") as f:
        f.write("Command: " + " ".join(base_cmd) + "\n\n")
        f.flush()
        proc = subprocess.Popen(
            base_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            f.write(line)
        proc.wait()
        f.write(f"\nExit code: {proc.returncode}\n")
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="LM Studio stability 3x runner")
    parser.add_argument(
        "--marker",
        default="requires_resource('lmstudio') and not slow",
        help="Pytest marker expression to select LM Studio tests.",
    )
    parser.add_argument(
        "--target",
        default="integration-tests",
        help="Target test suite as supported by devsynth run-tests.",
    )
    parser.add_argument(
        "--speed",
        default=["fast"],
        nargs="+",
        help="One or more speed categories (repeatable).",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        dest="no_parallel",
        help="Disable xdist parallelization.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Enable smoke mode to reduce plugin surface.",
    )
    parser.add_argument(
        "--maxfail",
        type=int,
        default=1,
        help="Stop after N failures (default: 1).",
    )
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Enable segmented execution.",
    )
    parser.add_argument(
        "--segment-size",
        type=int,
        default=None,
        dest="segment_size",
        help="Segment size when --segment is set.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="How many consecutive runs to execute (default: 3).",
    )
    parser.add_argument(
        "--diagnostics-dir",
        default="diagnostics",
        help="Directory to write diagnostics logs.",
    )

    args = parser.parse_args()

    diagnostics_dir = Path(args.diagnostics_dir)
    base_cmd = build_command(args)

    print("LM Studio stability runner")
    print("Diagnostics dir:", diagnostics_dir)
    print("Base command:", " ".join(base_cmd))
    print("Runs:", args.runs)

    failures = 0
    for i in range(1, args.runs + 1):
        print(f"\n=== Run {i}/{args.runs} ===")
        rc = run_once(i, base_cmd, diagnostics_dir)
        if rc != 0:
            failures += 1
            print(f"Run {i} FAILED with exit code {rc}")
        else:
            print(f"Run {i} PASSED")

    print(
        f"\nSummary: {args.runs - failures} passed / {args.runs} runs, {failures} failed"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
