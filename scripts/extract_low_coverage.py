#!/usr/bin/env python3
"""
Extract <90% coverage modules under src/devsynth from coverage.json and append a prioritized list to docs/task_notes.md with tentative owners.

Usage:
  poetry run python scripts/extract_low_coverage.py \
    --input test_reports/coverage.json \
    --threshold 90 \
    --notes docs/task_notes.md

Behavior:
- Reads pytest coverage JSON (generated with --cov-report=json:test_reports/coverage.json).
- Filters to files under src/devsynth/ with percent_covered < threshold.
- Sorts ascending by coverage, then by missing lines desc.
- Appends a section to docs/task_notes.md with a timestamp, including a simple table and owner column.
- Owner mapping heuristic:
  * Looks for path segments under src/devsynth/<package>/ and assigns owner to that package name.
  * If no rule applies, owner = "unassigned".

Idempotence:
- Adds a new dated section each run. Keep notes under 600 lines as per repo guideline; trims oldest auto-generated sections if exceeding.

References:
- docs/plan.md Section I snippet
- docs/tasks.md Task 37
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DEFAULT_INPUT = "test_reports/coverage.json"
DEFAULT_NOTES = "docs/task_notes.md"
DEFAULT_THRESHOLD = 90.0
MAX_NOTES_LINES = 600
AUTO_SECTION_MARK = "<!-- auto:low-coverage -->"


def load_coverage(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[extract_low_coverage] coverage file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[extract_low_coverage] invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def collect_under_threshold(data: Dict[str, Any], threshold: float) -> List[Tuple[str, float, int]]:
    rows: List[Tuple[str, float, int]] = []
    for filename, metrics in data.get("files", {}).items():
        norm = filename.replace("\\", "/")
        if not norm.startswith("src/devsynth/"):
            continue
        summary = metrics.get("summary", {})
        pct = float(summary.get("percent_covered", 0.0))
        missing = int(summary.get("missing_lines", 0))
        if pct < threshold:
            rows.append((norm, pct, missing))
    rows.sort(key=lambda x: (x[1], -x[2]))
    return rows


def guess_owner(path: str) -> str:
    # src/devsynth/<pkg>/...
    parts = path.split("/")
    try:
        idx = parts.index("devsynth")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return "unassigned"


def format_table(rows: Iterable[Tuple[str, float, int]]) -> str:
    header = "Rank  %Cov   Missing  Owner         File"
    lines = [header, "-" * len(header)]
    for i, (filename, pct, missing) in enumerate(rows, start=1):
        owner = guess_owner(filename)
        lines.append(f"{i:>4}  {pct:>5.1f}   {missing:>7}  {owner:<12} {filename}")
    return "\n".join(lines) + "\n"


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def trim_notes_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    # Remove oldest auto-generated sections to fit within limit
    # Identify blocks by AUTO_SECTION_MARK lines
    blocks: List[Tuple[int, int]] = []
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == AUTO_SECTION_MARK:
            if start is None:
                start = idx
            else:
                blocks.append((start, idx))
                start = None
    # Remove from earliest blocks until under limit
    for (s, e) in blocks:
        if len(lines) <= max_lines:
            break
        del lines[s : e + 1]
    # If still too long, truncate from top cautiously
    if len(lines) > max_lines:
        keep = lines[-max_lines:]
        lines = ["# Iteration Notes (Trimmed and Current)"] + keep
    return "\n".join(lines) + "\n"


def append_to_notes(notes_path: str, table: str) -> None:
    ensure_dir(notes_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    section = (
        f"\n{AUTO_SECTION_MARK}\n"
        f"## Low Coverage Extract — {now}\n"
        f"Source: {DEFAULT_INPUT} | Threshold: {DEFAULT_THRESHOLD:.1f}%\n\n"
        f"{table}"
        f"{AUTO_SECTION_MARK}\n"
    )
    if os.path.exists(notes_path):
        current = Path(notes_path).read_text(encoding="utf-8")
    else:
        current = "# Iteration Notes (Trimmed and Current)\n\n"
    updated = current + section
    updated = trim_notes_lines(updated, MAX_NOTES_LINES)
    Path(notes_path).write_text(updated, encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract <threshold coverage from coverage.json and append to task notes")
    p.add_argument("--input", default=DEFAULT_INPUT, help="Path to coverage.json (default: test_reports/coverage.json)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Coverage threshold percent (default: 90)")
    p.add_argument("--notes", default=DEFAULT_NOTES, help="Path to docs/task_notes.md")
    args = p.parse_args(argv)

    data = load_coverage(args.input)
    rows = collect_under_threshold(data, args.threshold)
    table = format_table(rows)
    append_to_notes(args.notes, table)
    print(f"[extract_low_coverage] Appended {len(rows)} entries under {args.threshold:.1f}% to {args.notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
