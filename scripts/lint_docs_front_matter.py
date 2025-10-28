#!/usr/bin/env python3
"""
Docs Front-Matter Linter

Purpose:
  - Ensure all Markdown docs include YAML front-matter with required keys:
      - title (str)
      - date (YYYY-MM-DD)
      - version (str)
      - status (one of: draft, active, deprecated, archived)
      - last_reviewed (YYYY-MM-DD)

Usage:
  - python scripts/lint_docs_front_matter.py [PATH ...]
    If no paths are provided, it scans under ./docs recursively for *.md files.

Exit Codes:
  - 0: all files pass
  - 1: one or more files failed validation

Notes:
  - Lightweight and dependency-free (no PyYAML) using a minimal parser.
  - Skips files that intentionally start without front-matter if they contain marker: `front_matter: skip` in the first 5 lines.
  - Designed to align with DevSynth guidelines for clarity and maintainability.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_FM_START = re.compile(r"^---\s*$")

REQUIRED_KEYS = [
    "title",
    "date",
    "version",
    "status",
    "last_reviewed",
]

ALLOWED_STATUS = {"draft", "active", "deprecated", "archived"}


def find_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(list(p.rglob("*.md")))
        elif p.suffix.lower() == ".md" and p.exists():
            files.append(p)
    return sorted({f.resolve() for f in files})


def parse_front_matter(lines: list[str]) -> tuple[dict[str, str] | None, int]:
    """Return (front_matter_dict, end_index) or (None, 0) if not present.
    end_index is the line index after the front matter block.
    """
    if not lines:
        return None, 0

    # Allow an initial UTF-8 BOM line or blank lines
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith("\ufeff")):
        i += 1

    if i >= len(lines) or not RE_FM_START.match(lines[i]):
        return None, 0

    i += 1
    fm: dict[str, str] = {}
    while i < len(lines) and not RE_FM_START.match(lines[i]):
        line = lines[i].rstrip("\n")
        if line.strip():
            if ":" not in line:
                # tolerate invalid line but record as empty key to fail later
                fm[line.strip()] = ""
            else:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        i += 1

    if i >= len(lines) or not RE_FM_START.match(lines[i]):
        # missing closing ---
        return None, 0

    return fm, i + 1


def validate_front_matter(fm: dict[str, str]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_KEYS:
        if key not in fm or not fm[key]:
            errors.append(f"missing key: {key}")

    # Semantic validation
    date = fm.get("date")
    last = fm.get("last_reviewed")
    status = fm.get("status")

    if date and not RE_DATE.match(date):
        errors.append("date must be YYYY-MM-DD")
    if last and not RE_DATE.match(last):
        errors.append("last_reviewed must be YYYY-MM-DD")
    if status and status not in ALLOWED_STATUS:
        errors.append(f"status must be one of: {', '.join(sorted(ALLOWED_STATUS))}")

    return errors


def should_skip(lines: list[str]) -> bool:
    head = "\n".join(lines[:5]).lower()
    return "front_matter: skip" in head


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args:
        paths = [Path(a) for a in args]
    else:
        paths = [Path("docs")]

    files = find_markdown_files(paths)

    had_errors = False
    for file in files:
        text = file.read_text(encoding="utf-8")
        lines = text.splitlines()

        if should_skip(lines):
            continue

        fm, _ = parse_front_matter(lines)
        if fm is None:
            print(
                f"[FAIL] {file}: missing or malformed YAML front-matter (---) at top",
                file=sys.stderr,
            )
            had_errors = True
            continue

        errors = validate_front_matter(fm)
        if errors:
            print(f"[FAIL] {file}: " + "; ".join(errors), file=sys.stderr)
            had_errors = True
        else:
            print(f"[OK]   {file}")

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
