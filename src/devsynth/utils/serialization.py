from __future__ import annotations

"""Deterministic JSON serialization utilities.

Goals:
- Deterministic output across platforms/runs (sorted keys, compact separators).
- UTF-8 text with a trailing newline for file outputs.
- Minimal footprint; no heavy dependencies.

These helpers are intended for cross-process exchange and caching where
stable byte representations reduce cache misses and ease diffs.

Aligned with docs/plan.md (determinism) and .junie/guidelines.md.
"""

import json
from typing import Any


def dumps_deterministic(obj: Any) -> str:
    """Serialize to a deterministic JSON string.

    - sort_keys=True ensures key order stability
    - separators=(",", ":") avoids spaces (compact, stable)
    - ensure_ascii=False preserves Unicode
    - Append a single trailing newline for text-file friendliness
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # Ensure exactly one trailing newline for deterministic text files
    if not s.endswith("\n"):
        s = s + "\n"
    return s


def loads(s: str) -> Any:
    """Parse JSON content produced by dumps_deterministic.

    Accepts strings with or without a trailing newline.
    """
    # Strip only the final newline if present to be tolerant of file reads
    if s.endswith("\n"):
        s = s[:-1]
    return json.loads(s)


def dump_to_file(path: str, obj: Any) -> None:
    """Write deterministic JSON to a file path in UTF-8, with trailing newline."""
    data = dumps_deterministic(obj)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)


def load_from_file(path: str) -> Any:
    """Read JSON from a file written by dump_to_file (UTF-8)."""
    with open(path, "r", encoding="utf-8") as f:
        return loads(f.read())
