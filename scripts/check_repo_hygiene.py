#!/usr/bin/env python3
"""
Check repository hygiene for DevSynth.
- Verifies git working tree is clean (no unstaged or uncommitted changes)
- Flags common unwanted artifacts if present (logs/, .devsynth/, dist/, build/, test_reports/, .pytest_cache, .coverage*)

Exit codes:
  0 - Clean
  1 - Issues detected

This script is non-destructive and intended for local and CI checks. It aligns with docs/tasks.md section 2 (Baseline repo hygiene).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ARTIFACT_DIRS = [
    "logs",
    ".devsynth",
    "dist",
    "build",
    "test_reports",
    ".pytest_cache",
]
ARTIFACT_FILES_PREFIX = [
    ".coverage",
]


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_root() -> Path:
    code, out, _ = run(["git", "rev-parse", "--show-toplevel"])
    if code != 0:
        return Path.cwd()
    return Path(out)


def main() -> int:
    root = git_root()
    os.chdir(root)

    code, out, err = run(["git", "status", "--porcelain"])
    dirty = False
    if code != 0:
        print("git status failed:", err or out, file=sys.stderr)
        dirty = True
    else:
        if out:
            print("Working tree not clean. Uncommitted changes detected:")
            print(out)
            dirty = True

    # Check for artifacts
    artifact_issues = []
    for d in ARTIFACT_DIRS:
        p = root / d
        if p.exists():
            artifact_issues.append(str(p))
    for prefix in ARTIFACT_FILES_PREFIX:
        for p in root.glob(prefix + "*"):
            artifact_issues.append(str(p))

    if artifact_issues:
        print(
            "\nPotentially unwanted artifacts found (should be gitignored and absent):"
        )
        for item in artifact_issues:
            print(f" - {item}")
        dirty = True

    if dirty:
        print("\nRepo hygiene check FAILED. See items above.")
        return 1

    print(
        "Repo hygiene check OK: working tree clean and no unwanted artifacts present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
