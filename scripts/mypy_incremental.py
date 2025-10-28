#!/usr/bin/env python3
"""
Run mypy only on files changed in the current pull request/branch.

Behavior:
- Detect changed Python files relative to a base ref (default: origin/main, falling
  back to HEAD~1 when origin/main is unavailable).
- Filter to repository-tracked *.py files within src/ and tests/ (to keep signal high).
- If no changed Python files are found, exit 0 with an informational message.
- Invoke mypy with the repository configuration; print concise diagnostics and
  return mypy's exit code.

Usage:
  poetry run python scripts/mypy_incremental.py

Notes:
- This script is designed for CI and local pre-submit checks. It complements the
  baseline generator (scripts/generate_mypy_baseline_issues.py) by preventing new
  typing regressions on touched files (Task 4.4 in docs/tasks.md).
- Messaging follows CLI clarity principles in docs/user_guides/cli_command_reference.md.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List
from collections.abc import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]


def _run(
    cmd: Sequence[str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd), cwd=str(cwd or ROOT), capture_output=True, text=True
    )


def _git_diff_names(base_ref: str) -> list[str]:
    proc = _run(["git", "diff", "--name-only", base_ref, "HEAD"])
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _fallback_base_ref() -> str:
    # Prefer origin/main; if missing (e.g., in forks), use HEAD~1
    if _run(["git", "rev-parse", "--verify", "origin/main"]).returncode == 0:
        return "origin/main"
    # Try main without remote
    if _run(["git", "rev-parse", "--verify", "main"]).returncode == 0:
        return "main"
    return "HEAD~1"


def _filter_python_paths(paths: Iterable[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        if not p.endswith(".py"):
            continue
        # Only consider files under src/ or tests/ (tracked)
        if p.startswith("src/") or p.startswith("tests/"):
            # Ensure file exists (skip deletions/renames where file no longer present)
            abs_path = ROOT / p
            if abs_path.exists():
                out.append(p)
    return sorted(set(out))


def run_mypy_incremental(files: Sequence[str]) -> int:
    if not files:
        print("[info] No changed Python files under src/ or tests/ — skipping mypy.")
        return 0
    rels = list(files)
    print(f"[info] Running mypy on {len(rels)} changed file(s):")
    for f in rels:
        print(f" - {f}")
    # Call mypy as a module to respect the Poetry env
    cmd = [sys.executable, "-m", "mypy", *rels]
    proc = _run(cmd)
    # Stream outputs for CI logs
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def main() -> int:
    base = os.environ.get("MYPY_BASE_REF") or _fallback_base_ref()
    changed = _git_diff_names(base)
    files = _filter_python_paths(changed)
    return run_mypy_incremental(files)


if __name__ == "__main__":
    raise SystemExit(main())
