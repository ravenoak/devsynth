#!/usr/bin/env python3
"""Append MVUU metadata to ``traceability.json``.

Deprecated: parsing and validation now live in ``devsynth.core.mvu``; this
script remains as a thin wrapper and will be removed in a future release.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Dict

from devsynth.core.mvu import parse_commit_message, MVUU


def build_entry(mvuu: MVUU) -> Dict[str, object]:
    """Build a traceability entry from MVUU metadata."""
    return {
        "features": [mvuu.utility_statement],
        "files": mvuu.affected_files,
        "tests": mvuu.tests,
        "issue": mvuu.issue,
        "mvuu": mvuu.mvuu,
        "notes": mvuu.notes,
    }


def update_traceability(trace_file: pathlib.Path, commit: str) -> None:
    """Append a traceability entry for ``commit`` if needed."""
    commit_msg = subprocess.run(
        ["git", "log", "-1", "--pretty=%B", commit],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    mvuu = parse_commit_message(commit_msg)
    trace_id = mvuu.TraceID
    entry = build_entry(mvuu)
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
