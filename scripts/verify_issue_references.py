#!/usr/bin/env python3
"""Verify and optionally update issue references.

This script scans ``issues/*.md`` for ``Specification`` and ``BDD Feature``
references. It verifies that referenced files exist and, when run with
``--fix``, updates tickets with invalid references by:

* removing invalid reference lines,
* appending missing paths to the ``Dependencies`` field,
* lowering ``Priority`` to ``low`` when any reference is missing, and
* inserting ``- None`` under ``## References`` if no valid references remain.
"""
from __future__ import annotations

import argparse
import pathlib
import re
from typing import List

ISSUES_DIR = pathlib.Path("issues")
REFERENCE_RE = re.compile(r"- (Specification|BDD Feature): (?P<path>.+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="update issues with missing references")
    return parser.parse_args()


def load_issue(path: pathlib.Path) -> List[str]:
    return path.read_text().splitlines(keepends=True)


def save_issue(path: pathlib.Path, lines: List[str]) -> None:
    path.write_text("".join(lines))


def update_issue(path: pathlib.Path, lines: List[str], missing_paths: List[str]) -> List[str]:
    """Apply updates for missing reference paths."""
    priority_re = re.compile(r"^Priority: ")
    deps_re = re.compile(r"^Dependencies: ")

    # adjust priority
    for i, line in enumerate(lines):
        if priority_re.match(line):
            if "low" not in line:
                lines[i] = "Priority: low\n"
            break

    # adjust dependencies
    for i, line in enumerate(lines):
        if deps_re.match(line):
            existing = [d.strip() for d in line.split(":", 1)[1].split(",") if d.strip() and d.strip().lower() != "none"]
            for mp in missing_paths:
                if mp not in existing:
                    existing.append(mp)
            if existing:
                lines[i] = f"Dependencies: {', '.join(existing)}\n"
            else:
                lines[i] = "Dependencies: None\n"
            break

    # adjust references section
    ref_header_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## References":
            ref_header_idx = i
            break

    if ref_header_idx is not None:
        # gather reference lines following header
        j = ref_header_idx + 1
        while j < len(lines) and lines[j].startswith("-"):
            if REFERENCE_RE.match(lines[j]):
                # only keep lines with valid references (should already be handled)
                pass
            j += 1
        # after removing invalid lines, ensure at least '- None'
        has_ref = any(REFERENCE_RE.match(lines[k]) for k in range(ref_header_idx + 1, j))
        if not has_ref:
            lines = lines[:ref_header_idx + 1] + ["- None\n"] + lines[j:]
    return lines


def process_issue(path: pathlib.Path, fix: bool) -> bool:
    lines = load_issue(path)
    missing_paths: List[str] = []
    new_lines: List[str] = []
    in_refs = False
    for line in lines:
        m = REFERENCE_RE.match(line)
        if m:
            ref_path = m.group("path").strip()
            if pathlib.Path(ref_path).exists():
                new_lines.append(line)
            else:
                missing_paths.append(ref_path)
                # skip line
        else:
            new_lines.append(line)
    updated = False
    if missing_paths and fix:
        updated = True
        new_lines = update_issue(path, new_lines, missing_paths)
        save_issue(path, new_lines)
    return missing_paths and not fix, updated


def main() -> int:
    args = parse_args()
    issues = [p for p in ISSUES_DIR.glob("*.md") if p.name not in {"README.md", "TEMPLATE.md"}]
    problems = []
    for issue in issues:
        missing_only, updated = process_issue(issue, args.fix)
        if missing_only:
            problems.append(issue)
    if problems:
        print("Issues with invalid references:")
        for p in problems:
            print(f"- {p}")
        return 1 if not args.fix else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
