#!/usr/bin/env python3
"""
Repository hygiene checker for DevSynth.

Purpose:
- Support Task 2 in docs/tasks.md: ensure repo is clean of untracked build artifacts and temp files.
- Intended for local use and CI as a preflight step.

Behavior:
- Runs `git status --porcelain` to list untracked files.
- Flags files/directories matching known transient patterns.
- Exits with non-zero code if such files are detected, printing actionable guidance.

Note:
- This script does not modify the working tree.
- Keep patterns in sync with .gitignore to avoid churn.

Usage:
- python scripts/repo_hygiene_check.py
- or add to pre-commit as an optional local hook.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Transient patterns we consider hygiene violations if untracked.
TRANSIENT_PATTERNS = [
    r"^logs(/|$)",
    r"^\.devsynth(/|$)",
    r"^dist(/|$)",
    r"^build(/|$)",
    r"^\.pytest_cache(/|$)",
    r"^test_reports(/|$)",
    r"^coverage_html(/|$)",
    r"^htmlcov(/|$)",
    r"^\.mypy_cache(/|$)",
    r"^\.ruff_cache(/|$)",
    r"^\.coverage$",
]

TRANSIENT_REGEXES = [re.compile(p) for p in TRANSIENT_PATTERNS]


def _git_status_porcelain(repo_root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, text=True
        )
    except Exception as e:  # pragma: no cover - environment dependent
        print(f"[repo_hygiene_check] Warning: unable to run git status: {e}")
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _extract_untracked_paths(status_lines: list[str]) -> list[str]:
    # Porcelain format: lines starting with ?? are untracked
    untracked = []
    for line in status_lines:
        if line.startswith("?? "):
            untracked.append(line[3:])
    return untracked


def _is_transient(path: str) -> bool:
    return any(r.match(path) for r in TRANSIENT_REGEXES)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    status = _git_status_porcelain(repo_root)
    untracked = _extract_untracked_paths(status)

    offenders = sorted(p for p in untracked if _is_transient(p))
    if not offenders:
        print("Repo hygiene check: OK (no untracked transient artifacts detected).")
        return 0

    print("Repo hygiene check: FAIL\n")
    print("The following untracked transient artifacts were found:")
    for p in offenders:
        print(f"  - {p}")
    print(
        "\nAction: Add these to .gitignore (if missing) or remove them before committing.\n"
        "Reference: docs/tasks.md Task 2 (Baseline repo hygiene)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
