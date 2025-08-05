#!/usr/bin/env python3
"""Verify MVUU affected files cover changed files.

Deprecated: core MVUU helpers live in ``devsynth.core.mvu``; this script is a
thin wrapper kept for backward compatibility.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Iterable, List

from devsynth.core.mvu import validate_commit_message, validate_affected_files


def verify_mvuu_affected_files(message: str, changed_files: Iterable[str]) -> List[str]:
    """Return discrepancies between MVUU metadata and changed files."""
    errors: List[str] = []
    try:
        mvuu = validate_commit_message(message)
    except Exception as exc:  # pragma: no cover - surface all validation errors
        errors.append(str(exc))
    else:
        errors.extend(validate_affected_files(mvuu, changed_files))
    return errors


def _changed_files(commit_hash: str) -> List[str]:
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", f"{commit_hash}^!"], text=True
    )
    return [line for line in diff.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure MVUU references exist for changed files."
    )
    parser.add_argument(
        "rev_range",
        nargs="?",
        default="origin/main..HEAD",
        help="Git revision range to check, default origin/main..HEAD",
    )
    args = parser.parse_args()

    hashes = (
        subprocess.check_output(["git", "rev-list", args.rev_range], text=True)
        .strip()
        .splitlines()
    )
    errors: List[str] = []
    for commit_hash in reversed(hashes):
        message = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B", commit_hash], text=True
        )
        changed = _changed_files(commit_hash)
        errs = verify_mvuu_affected_files(message, changed)
        if errs:
            errors.extend(f"{commit_hash[:7]}: {e}" for e in errs)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
