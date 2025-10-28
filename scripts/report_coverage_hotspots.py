#!/usr/bin/env python3
"""
Report low-coverage hotspots from coverage.xml.

- Parses coverage.xml produced by pytest --cov to identify modules with coverage
  below a configurable threshold (default 75%).
- Outputs a sorted list (ascending by coverage %) highlighting worst offenders.
- Exits with code 0 always (advisory), unless --strict is provided, in which case
  it exits non-zero if any file is below the threshold.

Usage:
  poetry run python scripts/report_coverage_hotspots.py [--coverage-file path] [--threshold 75] [--limit 25] [--strict]

This script is part of the stabilization tasks (docs/tasks.md #4) to help
identify low-coverage hotspots.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Report low-coverage hotspots from coverage.xml"
    )
    p.add_argument(
        "--coverage-file",
        default="coverage.xml",
        help="Path to coverage.xml (default: coverage.xml)",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=75.0,
        help="Minimum acceptable coverage percentage per file (default: 75.0)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Max number of files to display (default: 25)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any file is below the threshold",
    )
    return p.parse_args()


def load_coverage(file_path: Path) -> list[tuple[str, float]]:
    if not file_path.exists():
        raise FileNotFoundError(f"Coverage file not found: {file_path}")

    tree = ET.parse(str(file_path))
    root = tree.getroot()

    # Coverage XML schema: <coverage> -> <packages> -> <package> -> <classes> -> <class>
    # Each class has attributes: filename, line-rate (0..1), branch-rate
    results: list[tuple[str, float]] = []
    for clazz in root.findall(".//class"):
        filename = clazz.get("filename")
        line_rate = clazz.get("line-rate")
        if filename is None or line_rate is None:
            continue
        try:
            pct = float(line_rate) * 100.0
        except Exception:
            continue
        results.append((filename, pct))
    return results


def filter_and_sort(
    entries: list[tuple[str, float]], threshold: float, limit: int
) -> list[tuple[str, float]]:
    # Focus on our codebase
    filtered = [(f, c) for (f, c) in entries if f.startswith("src/")]
    # Sort by ascending coverage, then by path
    filtered.sort(key=lambda t: (t[1], t[0]))
    if limit > 0:
        return filtered[:limit]
    return filtered


def main() -> int:
    args = parse_args()
    path = Path(args.coverage_file)

    try:
        entries = load_coverage(path)
    except FileNotFoundError as e:
        print(
            f"[report_coverage_hotspots] {e}\nHint: run 'poetry run pytest --cov --cov-report=xml:coverage.xml' first."
        )
        return 0  # Advisory; don't fail pipelines by default
    except ET.ParseError as e:
        print(f"[report_coverage_hotspots] Failed to parse {path}: {e}")
        return 1

    hotspots = filter_and_sort(entries, args.threshold, args.limit)

    if not hotspots:
        print("[report_coverage_hotspots] No coverage entries found under src/.")
        return 0

    print("Low-coverage hotspots (ascending by coverage):")
    print("Coverage%\tFile")
    below = 0
    for filename, pct in hotspots:
        mark = "" if pct >= args.threshold else " <- below threshold"
        if pct < args.threshold:
            below += 1
        print(f"{pct:6.2f}\t{filename}{mark}")

    if args.strict and below > 0:
        print(
            f"[report_coverage_hotspots] {below} file(s) below threshold {args.threshold}%"
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
