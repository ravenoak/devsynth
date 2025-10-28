#!/usr/bin/env python3
"""
Summarize coverage.json into a ranked table by lowest coverage first.

Usage:
  poetry run python scripts/summarize_coverage.py [--input test_reports/coverage.json] [--limit 50] [--output diagnostics/coverage_summary.txt]

Behavior:
- Reads coverage JSON created by pytest --cov-report=json:<path>.
- Filters to files under src/devsynth/.
- Prints a simple text table: rank, percent, missing lines count, file path.
- Optionally writes the same table to an output file.

This helper is referenced by docs/tasks.md (task 91) and docs/plan.md Section I.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

DEFAULT_INPUT = "test_reports/coverage.json"
DEFAULT_OUTPUT = "diagnostics/coverage_summary.txt"


def load_coverage(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[summarize_coverage] coverage file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[summarize_coverage] invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def collect_files(data: dict[str, Any]) -> list[tuple[str, float, int]]:
    files = []
    for filename, metrics in data.get("files", {}).items():
        # Only consider project source files
        if not filename.replace("\\", "/").startswith("src/devsynth/"):
            continue
        summary = metrics.get("summary", {})
        pct = float(summary.get("percent_covered", 0.0))
        missing = int(summary.get("missing_lines", 0))
        files.append((filename, pct, missing))
    # Rank by ascending coverage, then descending missing lines
    files.sort(key=lambda x: (x[1], -x[2]))
    return files


def format_table(rows: list[tuple[str, float, int]], limit: int | None = None) -> str:
    header = "Rank  %Cov   Missing  File"
    lines = [header, "-" * len(header)]
    take = rows if limit is None else rows[:limit]
    for idx, (filename, pct, missing) in enumerate(take, start=1):
        lines.append(f"{idx:>4}  {pct:>5.1f}   {missing:>7}  {filename}")
    return "\n".join(lines) + "\n"


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize coverage.json into a ranked table"
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Path to coverage.json (default: test_reports/coverage.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max rows to display (default: 50; 0 = unlimited)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Optional path to write the summary table",
    )
    args = parser.parse_args(argv)

    data = load_coverage(args.input)
    rows = collect_files(data)

    limit = None if args.limit == 0 else args.limit
    table = format_table(rows, limit)

    # Print to stdout for immediate visibility
    print(table, end="")

    # Also write to output file for diagnostics
    if args.output:
        ensure_dir(args.output)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(table)
        print(f"[summarize_coverage] wrote summary to {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
