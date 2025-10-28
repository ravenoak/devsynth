#!/usr/bin/env python3
"""
Create issue stubs for <90% coverage modules based on test_reports/coverage.json and append a summary to docs/task_notes.md.

This fulfills docs/tasks.md Task 75 by generating per-package owner issue lines that can be pasted into the issue tracker,
and by recording a concise checklist in docs/task_notes.md. It does not require network or GitHub tokens.

Usage:
  poetry run python scripts/create_coverage_issues.py \
    --input test_reports/coverage.json \
    --threshold 90 \
    --notes docs/task_notes.md \
    --dry-run

Behavior:
- Reads coverage JSON; filters src/devsynth/* files with percent_covered < threshold.
- Groups by owner (src/devsynth/<owner>/...) using the same heuristic as extract_low_coverage.py.
- Emits markdown checklist lines per file with a suggested issue title and owner.
- Appends a short section to docs/task_notes.md with the generated list and a reminder to create issues per package owner.
- If --dry-run is set, prints to stdout and still appends to notes for traceability.

Constraints:
- Keeps docs/task_notes.md under 600 lines by trimming oldest auto sections.

See also: scripts/extract_low_coverage.py and docs/plan.md Section I.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_INPUT = "test_reports/coverage.json"
DEFAULT_NOTES = "docs/task_notes.md"
DEFAULT_THRESHOLD = 90.0
AUTO_SECTION_MARK = "<!-- auto:coverage-issues -->"


def load_coverage(path: str) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"[create_coverage_issues] coverage file not found: {path}")


def guess_owner(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    try:
        idx = parts.index("devsynth")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return "unassigned"


def under_threshold(data: dict[str, Any], threshold: float) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for filename, metrics in data.get("files", {}).items():
        norm = filename.replace("\\", "/")
        if not norm.startswith("src/devsynth/"):
            continue
        pct = float(metrics.get("summary", {}).get("percent_covered", 0.0))
        if pct < threshold:
            rows.append((norm, pct))
    rows.sort(key=lambda x: (x[1], x[0]))
    return rows


def generate_issue_lines(rows: list[tuple[str, float]]) -> list[str]:
    lines: list[str] = []
    for path, pct in rows:
        owner = guess_owner(path)
        title = f"Increase coverage to ≥90%: {path}"
        lines.append(f"- [ ] {title}  (owner: {owner}, current: {pct:.1f}%)")
    return lines


def trim_notes(text: str, max_lines: int = 600) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    # remove oldest auto sections
    start_idx = []
    for i, line in enumerate(lines):
        if line.strip() == AUTO_SECTION_MARK:
            start_idx.append(i)
    while len(lines) > max_lines and start_idx:
        s = start_idx.pop(0)
        # find next marker for end
        e = None
        for j in range(s + 1, len(lines)):
            if lines[j].strip() == AUTO_SECTION_MARK:
                e = j
                break
        if e is None:
            # no closing marker; drop from start
            del lines[: s + 1]
        else:
            del lines[s : e + 1]
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
        if not lines or not lines[0].startswith("# "):
            lines.insert(0, "# Iteration Notes (Trimmed and Current)")
    return "\n".join(lines) + "\n"


def append_notes(notes_path: str, lines: list[str], threshold: float) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    section = (
        f"\n{AUTO_SECTION_MARK}\n"
        f"## Coverage Issue Stubs — {now}\n"
        f"Source: {DEFAULT_INPUT} | Threshold: {threshold:.1f}%\n\n"
        + "\n".join(lines)
        + "\n\nAction: Create issues in the tracker per line, grouped by owner. Link these issues back here for traceability.\n"
        f"{AUTO_SECTION_MARK}\n"
    )
    if os.path.exists(notes_path):
        current = Path(notes_path).read_text(encoding="utf-8")
    else:
        current = "# Iteration Notes (Trimmed and Current)\n\n"
    updated = current + section
    updated = trim_notes(updated)
    Path(notes_path).write_text(updated, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Create issue stub checklist for <90% coverage files"
    )
    p.add_argument("--input", default=DEFAULT_INPUT, help="Path to coverage.json")
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Coverage threshold percent",
    )
    p.add_argument("--notes", default=DEFAULT_NOTES, help="Path to docs/task_notes.md")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout as well")
    args = p.parse_args(argv)

    data = load_coverage(args.input)
    rows = under_threshold(data, args.threshold)
    issue_lines = generate_issue_lines(rows)

    if args.dry_run:
        print("\n".join(issue_lines))
    append_notes(args.notes, issue_lines, args.threshold)
    print(
        f"[create_coverage_issues] Prepared {len(issue_lines)} issue stubs and appended to {args.notes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
