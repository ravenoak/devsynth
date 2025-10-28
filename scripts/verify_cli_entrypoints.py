#!/usr/bin/env python3
"""
Verify CLI entry points for DevSynth.

- Ensures that `devsynth --help` and `devsynth help` return exit code 0.
- Prints captured outputs on failure for diagnostics.

Intended to satisfy docs/tasks.md item 3.4.
"""
from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence


def run_cmd(cmd: Sequence[str]) -> int:
    proc = subprocess.run(
        cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def main() -> int:
    failures = 0
    for cmd in (["devsynth", "--help"], ["devsynth", "help"]):
        code = run_cmd(cmd)
        if code != 0:
            print(
                f"[verify_cli_entrypoints] Command failed: {' '.join(cmd)}",
                file=sys.stderr,
            )
            failures += 1
    if failures:
        return 1
    print("[verify_cli_entrypoints] CLI entry points verified: --help and help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
