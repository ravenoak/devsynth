#!/usr/bin/env python3
"""
Run live resource-gated fast subsets for OpenAI or LM Studio and capture artifacts under diagnostics/.
This is a thin orchestrator to aid docs/tasks.md Task 10 evidence capture.

Usage:
  python scripts/run_live_subsets.py --openai
  python scripts/run_live_subsets.py --lmstudio

Notes:
- Requires appropriate DEVSYNTH_RESOURCE_*_AVAILABLE=true and provider env vars to be set in the shell.
- Writes stdout to diagnostics/<provider>_fast_subset.txt and appends a summary to diagnostics/exec_log.txt
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def run_and_capture(cmd: list[str], outfile: Path) -> int:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with outfile.open("w", encoding="utf-8") as f:
        f.write(f"# Command: {' '.join(cmd)}\n# Started: {datetime.now(timezone.utc).isoformat()}\n\n")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            f.write(line)
        proc.wait()
        f.write(f"\n# Exit: {proc.returncode}\n")
        return proc.returncode


def append_exec_log(command: str, exit_code: int, artifacts: list[str], notes: str) -> None:
    try:
        subprocess.run([
            "poetry", "run", "python", "scripts/append_exec_log.py",
            "--command", command,
            "--exit-code", str(exit_code),
            "--artifacts", ",".join(artifacts),
            "--notes", notes,
        ], check=False)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--openai", action="store_true", help="Run OpenAI fast subset")
    group.add_argument("--lmstudio", action="store_true", help="Run LM Studio fast subset")
    args = parser.parse_args()

    diagnostics = Path("diagnostics")

    if args.openai:
        cmd = [
            "poetry", "run", "devsynth", "run-tests",
            "--target", "integration-tests",
            "--speed=fast",
            "-m", "requires_resource('openai')",
            "--no-parallel",
            "--maxfail=1",
        ]
        outfile = diagnostics / "openai_fast_subset.txt"
        notes = "live OpenAI fast subset"
    else:
        cmd = [
            "poetry", "run", "devsynth", "run-tests",
            "--target", "integration-tests",
            "--speed=fast",
            "-m", "requires_resource('lmstudio')",
            "--no-parallel",
            "--maxfail=1",
        ]
        outfile = diagnostics / "lmstudio_fast_subset.txt"
        notes = "live LM Studio fast subset"

    rc = run_and_capture(cmd, outfile)
    append_exec_log(" ".join(cmd), rc, [str(outfile)], notes)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
