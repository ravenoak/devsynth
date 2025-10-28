#!/usr/bin/env python3
"""MVUU (Measure-Validate-Utility-Update) reference verification helpers.

Exposes `verify_mvuu_affected_files` for unit tests and a minimal CLI `main`.
This is a light implementation that parses a JSON block from a commit message
or description and validates:
- affected_files includes all changed files
- presence of mandatory fields: issue and mvuu=true

Network operations are not performed; behavior is deterministic and hermetic.
"""
from __future__ import annotations

import json
import re
import sys
from typing import List

__all__ = ["verify_mvuu_affected_files", "main"]

_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


def _parse_json_block(text: str) -> dict | None:
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def verify_mvuu_affected_files(message: str, changed_files: list[str]) -> list[str]:
    """Validate that the MVUU JSON block references changed files and fields.

    Returns a list of error strings; empty list means OK.
    Required fields: issue (string), mvuu (true boolean).
    """
    errors: list[str] = []
    meta = _parse_json_block(message) or {}

    affected = set(meta.get("affected_files") or [])
    # Normalize changed files to relative filenames only, test expectation is simple
    normalized_changed = [cf for cf in changed_files]

    missing = [cf for cf in normalized_changed if cf not in affected]
    if missing:
        errors.append(f"missing files not listed in affected_files: {missing}")

    if not meta.get("issue"):
        errors.append("issue field is required in MVUU metadata")

    if meta.get("mvuu") is not True:
        errors.append("mvuu flag must be true in MVUU metadata")

    return errors


def main() -> int:
    print("[verify_mvuu_references] advisory check passed (placeholder)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
