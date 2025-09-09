#!/usr/bin/env python3
"""
Compare two coverage.json files and exit with non-zero status if coverage drops
by more than an allowed threshold.

Usage:
  poetry run python scripts/compare_coverage.py \
    --base path/to/base/coverage.json \
    --pr path/to/pr/coverage.json [--allow-drop 1.0]

- The script reads total coverage percentage from the "totals" block if present,
  preferring keys: "percent_covered", "percent_covered_display", or computed as
  covered / num_statements when available.
- Default allowed drop is 1.0 percentage point.
- On error (missing files, unreadable JSON, missing totals), exits with code 2.
- On drop > allowed threshold, prints a clear message and exits with code 3.
- Otherwise prints a success message and exits 0.

Aligns with docs/tasks.md §6.3 and docs/plan.md Phase 4 (coverage regression guard).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _extract_percent(totals: dict[str, Any]) -> float | None:
    # Common coverage.py JSON formats
    if "percent_covered" in totals and isinstance(
        totals["percent_covered"], (int, float)
    ):
        return float(totals["percent_covered"])
    if "percent_covered_display" in totals:
        try:
            return float(str(totals["percent_covered_display"]).strip("%"))
        except Exception:
            pass
    # Compute if possible
    covered = totals.get("covered_lines") or totals.get("covered")
    num = (
        totals.get("num_statements")
        or totals.get("num_lines")
        or totals.get("num_statements")
    )
    if isinstance(covered, (int, float)) and isinstance(num, (int, float)) and num:
        return 100.0 * float(covered) / float(num)
    return None


def _read_total_coverage(path: Path) -> tuple[float, dict[str, Any]]:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"error: failed to read JSON from {path}: {e}", file=sys.stderr)
        sys.exit(2)

    totals = data.get("totals") or data.get("summary") or {}
    percent = _extract_percent(totals)
    if percent is None:
        print(
            f"error: could not determine total coverage percent from {path}",
            file=sys.stderr,
        )
        sys.exit(2)
    return percent, totals


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compare total coverage between base and PR runs."
    )
    p.add_argument("--base", required=True, help="Path to base (main) coverage.json")
    p.add_argument("--pr", required=True, help="Path to PR coverage.json")
    p.add_argument(
        "--allow-drop",
        type=float,
        default=1.0,
        help="Allowed percentage drop before failing (default: 1.0)",
    )
    args = p.parse_args(argv)

    base_path = Path(args.base)
    pr_path = Path(args.pr)

    if not base_path.exists():
        print(f"error: base coverage file not found: {base_path}", file=sys.stderr)
        return 2
    if not pr_path.exists():
        print(f"error: PR coverage file not found: {pr_path}", file=sys.stderr)
        return 2

    base_pct, base_totals = _read_total_coverage(base_path)
    pr_pct, pr_totals = _read_total_coverage(pr_path)

    drop = base_pct - pr_pct
    print(
        f"base={base_pct:.2f}% pr={pr_pct:.2f}% "
        f"drop={drop:.2f}pp allow={args.allow_drop:.2f}pp"
    )

    if drop > args.allow_drop:
        print(
            "failure: coverage regression exceeds allowed drop threshold "
            f"({drop:.2f}pp > {args.allow_drop:.2f}pp)",
            file=sys.stderr,
        )
        return 3

    print("success: coverage within allowed threshold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
