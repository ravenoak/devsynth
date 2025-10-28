#!/usr/bin/env python3
r"""Conventional Commit message linter (strict by default in CI).

Supports two modes:
- commit-msg hook: pass the commit message file path as the first argument.
- range mode: use --range <A..B> to lint all commits between A and B (inclusive of B).

Rules (subset of Conventional Commits):
- Subject line must match:
  ^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+
- Subject line length <= 72 characters recommended (warn above 72, fail above 100).
- Body is optional. If present, wrap lines <= 100 characters (advisory).

Exit codes:
- 0: All commits compliant
- 1: Violations found
- 2: Usage error
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from collections.abc import Iterable

CONV_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: .+"
)
MAX_SUBJECT_HARD = 100
MAX_SUBJECT_SOFT = 72


def read_subject_from_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return text.splitlines()[0] if text else ""


def git_commit_subjects(rng: str) -> Iterable[tuple[str, str]]:
    # Returns (sha, subject)
    try:
        res = subprocess.run(
            ["git", "log", "--format=%H%x00%s", rng],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    lines = res.stdout.splitlines()
    for line in lines:
        if "\x00" in line:
            sha, subj = line.split("\x00", 1)
            yield sha, subj


def validate_subject(subject: str) -> list[str]:
    errors: list[str] = []
    if not subject.strip():
        errors.append("empty subject line")
        return errors
    if not CONV_REGEX.match(subject):
        errors.append(
            "subject must follow Conventional Commits, e.g., 'feat(scope): add thing'"
        )
    if len(subject) > MAX_SUBJECT_HARD:
        errors.append(f"subject too long ({len(subject)} > {MAX_SUBJECT_HARD})")
    elif len(subject) > MAX_SUBJECT_SOFT:
        errors.append(
            f"subject exceeds soft limit ({len(subject)} > {MAX_SUBJECT_SOFT})"
        )
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print(
            "Usage: commit_linter.py <commit-msg-file> | --range A..B", file=sys.stderr
        )
        return 2

    if argv[0] == "--range":
        if len(argv) < 2:
            print("Usage: commit_linter.py --range A..B", file=sys.stderr)
            return 2
        rng = argv[1]
        violations = 0
        for sha, subj in git_commit_subjects(rng):
            errs = validate_subject(subj)
            if errs:
                violations += 1
                print(f"✖ {sha[:12]}: {subj}")
                for e in errs:
                    print(f"  - {e}")
        if violations:
            print(f"Found {violations} commit message violation(s).", file=sys.stderr)
            return 1
        print("All commit messages compliant for range.")
        return 0

    # commit-msg hook mode
    path = Path(argv[0])
    subject = read_subject_from_file(path)
    errs = validate_subject(subject)
    if errs:
        print(f"Commit message not compliant: {subject}", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("Commit message compliant.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
