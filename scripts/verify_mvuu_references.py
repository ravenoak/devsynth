#!/usr/bin/env python3
"""Verify MVUU affected files cover changed files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Iterable, List

from devsynth.core.feature_flags import mvuu_enforcement_enabled


def _extract_mvuu_json(message: str) -> dict:
    pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    match = pattern.search(message)
    if not match:
        raise ValueError("Missing MVUU JSON block fenced with ```json … ```")
    return json.loads(match.group(1))


def verify_mvuu_affected_files(message: str, changed_files: Iterable[str]) -> List[str]:
    """Return errors if changed files lack MVUU references."""
    mvuu = _extract_mvuu_json(message)
    errors: List[str] = []
    if mvuu.get("mvuu") is not True:
        errors.append("'mvuu' must be true")
    if "issue" not in mvuu:
        errors.append("Missing required field 'issue'")
    affected = set(mvuu.get("affected_files", []))
    changed = set(changed_files)
    missing = changed - affected
    if missing:
        errors.append(
            "MVUU affected_files missing entries for: " + ", ".join(sorted(missing))
        )
    return errors


def _changed_files(commit_hash: str) -> List[str]:
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", f"{commit_hash}^!"], text=True
    )
    return [line for line in diff.splitlines() if line]


def main() -> int:
    if not mvuu_enforcement_enabled():
        return 0

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
