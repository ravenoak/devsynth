#!/usr/bin/env python3
"""Append MVUU metadata to ``traceability.json``.

The script parses an MVUU JSON block from the commit message and appends a
new entry to ``traceability.json`` including the commit hash and timestamp.
Existing TraceIDs are left unchanged.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Dict

MVUU_BLOCK_RE = re.compile(r"```json\n(?P<json>{.*?})\n```", re.DOTALL)
ISSUE_RE = re.compile(r"#(?P<id>\d+)$")


def extract_mvuu(commit_msg: str) -> Dict[str, Any]:
    """Return the parsed MVUU metadata from ``commit_msg``."""
    match = MVUU_BLOCK_RE.search(commit_msg)
    if not match:
        raise ValueError("Missing MVUU JSON block fenced with ```json ... ```")
    return json.loads(match.group("json"))


def build_entry(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Build a traceability entry from MVUU metadata."""
    return {
        "features": [metadata.get("utility_statement", "")],
        "files": metadata.get("affected_files", []),
        "tests": metadata.get("tests", []),
        "issue": metadata.get("issue", ""),
        "mvuu": metadata.get("mvuu", False),
        "notes": metadata.get("notes"),
    }


def _validate_issue(issue: str, root: pathlib.Path) -> None:
    """Ensure ``issue`` references an existing ticket."""
    match = ISSUE_RE.fullmatch(issue)
    if not match:
        raise ValueError("Issue must reference a ticket like '#123'")
    ticket = root / "issues" / f"{match.group('id')}.md"
    if not ticket.exists():
        raise ValueError(f"Issue {issue} not found in 'issues' directory")


def update_traceability(trace_file: pathlib.Path, commit: str) -> None:
    """Append a traceability entry for ``commit`` if needed."""
    commit_msg = subprocess.run(
        ["git", "log", "-1", "--pretty=%B", commit],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    metadata = extract_mvuu(commit_msg)
    _validate_issue(metadata.get("issue", ""), trace_file.parent)
    trace_id = metadata["TraceID"]
    entry = build_entry(metadata)
    commit_hash = subprocess.run(
        ["git", "rev-parse", commit],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    timestamp = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commit_hash],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    entry.update({"commit": commit_hash, "timestamp": timestamp})
    data = json.loads(trace_file.read_text()) if trace_file.exists() else {}
    if trace_id not in data:
        data[trace_id] = entry
        trace_file.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update traceability.json from MVUU metadata"
    )
    parser.add_argument(
        "--trace-file",
        type=pathlib.Path,
        default=pathlib.Path("traceability.json"),
        help="Path to traceability.json",
    )
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit to read MVUU metadata from",
    )
    args = parser.parse_args()
    try:
        update_traceability(args.trace_file, args.commit)
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
