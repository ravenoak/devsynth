#!/usr/bin/env python3
"""
Safe cleanup utility for workspace artifacts.

- Defaults to --dry-run (no deletion) unless --yes is provided.
- Only removes known artifact paths under the repository root.
- Skips files tracked by Git.

Usage:
  poetry run python scripts/clean_artifacts.py --dry-run
  poetry run python scripts/clean_artifacts.py --yes

Options:
  --keep-reports   Keep test_reports/
  --keep-coverage  Keep coverage outputs (.coverage, coverage.xml, htmlcov/)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import List
from collections.abc import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]


def is_git_tracked(paths: Iterable[Path]) -> set[Path]:
    """Return the subset of given paths that are tracked by Git.

    Uses `git ls-files` to determine tracked files under REPO_ROOT.
    """
    tracked: set[Path] = set()
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], cwd=str(REPO_ROOT), text=True
        )
    except Exception:
        # If git is unavailable, err on the side of caution: assume nothing is tracked.
        return tracked
    tracked_files = {
        REPO_ROOT / Path(line.strip()) for line in out.splitlines() if line.strip()
    }
    tracked_dirs = {p.parent for p in tracked_files}

    for p in paths:
        p = p.resolve()
        if p.is_file() and p in tracked_files:
            tracked.add(p)
        else:
            # If any tracked file lies under this directory, treat as tracked to avoid deletion
            for tf in tracked_files:
                try:
                    tf.relative_to(p)
                    tracked.add(p)
                    break
                except Exception:
                    continue
    return tracked


def collect_targets(keep_reports: bool, keep_coverage: bool) -> list[Path]:
    candidates: list[Path] = []
    # Directories
    if not keep_reports:
        candidates.append(REPO_ROOT / "test_reports")
    if not keep_coverage:
        candidates.append(REPO_ROOT / "htmlcov")
    candidates.append(REPO_ROOT / ".pytest_cache")
    candidates.append(REPO_ROOT / "build")
    candidates.append(REPO_ROOT / "dist")
    candidates.append(REPO_ROOT / "logs")  # if present and not tracked

    # Files
    if not keep_coverage:
        candidates.append(REPO_ROOT / ".coverage")
        candidates.append(REPO_ROOT / "coverage.xml")

    # Filter: only within repo root
    safe_candidates = []
    for p in candidates:
        try:
            p.resolve().relative_to(REPO_ROOT)
            safe_candidates.append(p)
        except Exception:
            # Ignore anything outside the repo
            pass
    return safe_candidates


def remove_path(p: Path, dry_run: bool) -> None:
    if not p.exists():
        return
    if dry_run:
        print(f"DRY-RUN: would remove {p}")
        return
    if p.is_dir():
        shutil.rmtree(p)
        print(f"Removed directory {p}")
    else:
        p.unlink(missing_ok=True)
        print(f"Removed file {p}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean workspace artifacts safely.")
    parser.add_argument(
        "--yes", action="store_true", help="Actually delete files (disable dry-run)"
    )
    parser.add_argument(
        "--keep-reports", action="store_true", help="Keep test_reports/"
    )
    parser.add_argument(
        "--keep-coverage", action="store_true", help="Keep coverage outputs"
    )
    args = parser.parse_args()

    dry_run = not args.yes

    targets = collect_targets(
        keep_reports=args.keep_reports, keep_coverage=args.keep_coverage
    )

    # Exclude Git-tracked paths for safety
    tracked = is_git_tracked(targets)
    safe_targets = [p for p in targets if p not in tracked]

    if not safe_targets:
        print("Nothing to clean.")
        return 0

    print(f"Repository root: {REPO_ROOT}")
    print("Planned removals:")
    for p in safe_targets:
        print(f" - {p}")

    for p in safe_targets:
        remove_path(p, dry_run=dry_run)

    if dry_run:
        print("Dry-run complete. Re-run with --yes to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
