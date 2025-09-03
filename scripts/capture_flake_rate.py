#!/usr/bin/env python3
"""
Lightweight flake-rate capture for LM Studio or any focused subset.
- Runs a given devsynth run-tests command N times (default 3) with the same filters.
- Captures pass/fail for each run and computes a naive flake rate.
- Writes diagnostics/flake_rate.json and a human-readable diagnostics/flake_rate.txt.

Usage examples:
  poetry run python scripts/capture_flake_rate.py \
    --target integration-tests --speed fast \
    --markers "requires_resource('lmstudio') and not slow" \
    --runs 3

Notes:
- Keeps things hermetic and bounded; does not alter environment.
- Designed to be called from Taskfile as diagnostics:flake-rate.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_cmd(cmd: list[str]) -> int:
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return proc.returncode
    except FileNotFoundError:
        return 127


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture flake rate over multiple identical runs"
    )
    parser.add_argument("--target", default="integration-tests")
    parser.add_argument("--speed", default="fast")
    parser.add_argument(
        "--markers", default="requires_resource('lmstudio') and not slow"
    )
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--no-parallel", action="store_true", default=True)
    parser.add_argument("--maxfail", type=int, default=1)
    args = parser.parse_args()

    diagnostics = Path("diagnostics")
    diagnostics.mkdir(parents=True, exist_ok=True)

    base_cmd = [
        sys.executable,
        "-m",
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--target",
        args.target,
        "--speed",
        args.speed,
        "--no-parallel",
        "--maxfail",
        str(args.maxfail),
        "-m",
        args.markers,
    ]

    runs: list[dict] = []
    for i in range(1, args.runs + 1):
        rc = run_cmd(base_cmd)
        runs.append({"index": i, "return_code": rc, "passed": rc == 0})

    total = len(runs)
    failures = sum(1 for r in runs if not r["passed"])
    flake_rate = failures / total if total else 0.0

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": shlex.join(base_cmd),
        "runs": runs,
        "summary": {
            "total_runs": total,
            "failures": failures,
            "flake_rate": flake_rate,
        },
    }

    (diagnostics / "flake_rate.json").write_text(json.dumps(payload, indent=2))

    lines = [
        f"Flake rate summary @ {payload['timestamp']}",
        f"Command: {payload['command']}",
        f"Total runs: {total}",
        f"Failures: {failures}",
        f"Flake rate: {flake_rate:.3f}",
        "Runs:",
    ]
    for r in runs:
        lines.append(
            f"  - Run {r['index']}: rc={r['return_code']} passed={r['passed']}"
        )
    (diagnostics / "flake_rate.txt").write_text("\n".join(lines) + "\n")

    # Append exec log
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "poetry",
                "run",
                "python",
                "scripts/append_exec_log.py",
                "--command",
                "capture_flake_rate",
                "--exit-code",
                str(0 if failures == 0 else 1),
                "--artifacts",
                "diagnostics/flake_rate.json,diagnostics/flake_rate.txt",
                "--notes",
                f"flake_rate={flake_rate:.3f}",
            ],
            check=False,
        )
    except Exception:
        pass

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
