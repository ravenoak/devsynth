#!/usr/bin/env python3
"""Lint commit messages for MVUU compliance."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs/specifications/mvuuschema.json"

CONVENTIONAL_RE = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([\w\-]+\))?: .+"
)


def _load_schema() -> dict:
    """Return the MVUU JSON schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


SCHEMA = _load_schema()


def _extract_mvuu_json(message: str) -> dict:
    """Extract the MVUU JSON block from a commit message."""
    pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    match = pattern.search(message)
    if not match:
        raise ValueError("Missing MVUU JSON block fenced with ```json … ```")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"MVUU JSON is not valid JSON: {exc.msg}") from exc


def lint_commit_message(message: str) -> List[str]:
    """Validate a commit message against conventional and MVUU rules."""
    errors: List[str] = []
    header = message.splitlines()[0]
    if not CONVENTIONAL_RE.match(header):
        errors.append(
            "Commit message header must follow Conventional Commits, e.g. 'feat: …'"
        )
    try:
        mvuu = _extract_mvuu_json(message)
        jsonschema.validate(mvuu, SCHEMA)
        trace_id = str(mvuu.get("TraceID", ""))
        if not trace_id.startswith("MVUU-"):
            errors.append("TraceID must start with 'MVUU-'")
    except ValueError as exc:
        errors.append(str(exc))
    except jsonschema.ValidationError as exc:  # pragma: no cover - passthrough
        errors.append(f"MVUU JSON invalid: {exc.message}")
    return errors


def lint_range(rev_range: str) -> List[str]:
    """Lint all commit messages within a git revision range."""
    errors: List[str] = []
    hashes = (
        subprocess.check_output(["git", "rev-list", rev_range], text=True)
        .strip()
        .splitlines()
    )
    for commit_hash in reversed(hashes):
        message = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B", commit_hash], text=True
        )
        commit_errors = lint_commit_message(message)
        if commit_errors:
            errors.append(f"{commit_hash[:7]}:\n" + "\n".join(commit_errors))
    return errors


def main() -> int:
    """Command-line entry point for commit message linting."""
    parser = argparse.ArgumentParser(
        description="Lint commit messages using MVUU schema."
    )
    parser.add_argument("message_file", nargs="?", help="Path to commit message file.")
    parser.add_argument(
        "--range",
        dest="rev_range",
        help="Git revision range to lint, e.g. origin/main..HEAD.",
    )
    args = parser.parse_args()

    if args.rev_range:
        errors = lint_range(args.rev_range)
        if errors:
            print("\n\n".join(errors), file=sys.stderr)
            return 1
        return 0

    if not args.message_file:
        parser.error("provide a commit message file or --range")
    message = Path(args.message_file).read_text(encoding="utf-8")
    errors = lint_commit_message(message)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
