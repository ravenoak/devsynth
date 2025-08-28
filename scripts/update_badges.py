#!/usr/bin/env python3
"""
Update README badges (currently coverage) based on coverage.xml.

- Parses coverage.xml overall line-rate and updates the README coverage badge URL.
- Supports --check to only verify badge matches current coverage rounded down to nearest 5% bucket.

Usage:
  poetry run python scripts/update_badges.py [--readme README.md] [--coverage coverage.xml] [--check]

Notes:
- This is a minimal helper; CI can invoke it after running coverage.
- Color mapping is simple: <50 red, <70 yellow, otherwise green.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BADGE_PATTERN = re.compile(
    r"!\[Coverage\]\(https://img.shields.io/badge/coverage-[^\)]*\)"
)


def compute_overall_coverage(xml_path: Path) -> float:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # cobertura XML root has attribute 'line-rate' sometimes; otherwise aggregate from packages
    rate_attr = root.attrib.get("line-rate")
    if rate_attr is not None:
        try:
            return float(rate_attr) * 100.0
        except Exception:
            pass
    total_lines = 0
    covered_lines = 0
    for pkg in root.findall("./packages/package"):
        for cls in pkg.findall("./classes/class"):
            lines = cls.findall("./lines/line")
            for ln in lines:
                total_lines += 1
                if ln.attrib.get("hits") not in {None, "0"}:
                    covered_lines += 1
    if total_lines == 0:
        return 0.0
    return (covered_lines / total_lines) * 100.0


def bucket_percent(pct: float) -> int:
    # Round to nearest 5% bucket downwards (e.g., 83.2 -> 80)
    return int(pct // 5 * 5)


def color_for(pct: int) -> str:
    if pct < 50:
        return "red"
    if pct < 70:
        return "yellow"
    return "green"


def format_badge(pct_bucket: int) -> str:
    label = f"{pct_bucket}%25" if pct_bucket != 100 else "100%25"
    color = color_for(pct_bucket)
    return f"![Coverage](https://img.shields.io/badge/coverage-{label}-{color}.svg)"


def update_readme(readme_path: Path, new_badge: str, check_only: bool) -> int:
    text = readme_path.read_text(encoding="utf-8")
    m = BADGE_PATTERN.search(text)
    if not m:
        print("update_badges: coverage badge not found in README", file=sys.stderr)
        return 2
    current = m.group(0)
    if current == new_badge:
        print("update_badges: badge is up-to-date")
        return 0
    if check_only:
        print("update_badges: badge out-of-date", file=sys.stderr)
        return 3
    updated = BADGE_PATTERN.sub(new_badge, text, count=1)
    readme_path.write_text(updated, encoding="utf-8")
    print("update_badges: README badge updated")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--readme", default="README.md")
    p.add_argument("--coverage", default="coverage.xml")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)

    readme_path = Path(args.readme)
    cov_path = Path(args.coverage)
    if not cov_path.exists():
        print(f"update_badges: coverage report not found: {cov_path}", file=sys.stderr)
        return 1
    if not readme_path.exists():
        print(f"update_badges: README not found: {readme_path}", file=sys.stderr)
        return 1

    pct = compute_overall_coverage(cov_path)
    bucket = bucket_percent(pct)
    new_badge = format_badge(bucket)
    return update_readme(readme_path, new_badge, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
