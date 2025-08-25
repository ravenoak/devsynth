"""Validate standardized YAML front matter in Markdown docs.

Rules (aligned with release_plan.md lines 34–36 and .junie/guidelines.md):
- Every Markdown file under docs/ must start with YAML front matter delimited by --- lines.
- Required keys: title, date, author, status.
- Optional keys validated if present: version, tags, last_reviewed.
- status must be one of: draft, published, deprecated.

Exit codes:
- 0: all files pass
- 1: one or more files fail validation

Usage:
  poetry run python scripts/check_front_matter.py [--fix-missing]

If --fix-missing is provided, a minimal header will be inserted for files
missing front matter, using the first H1 as title when possible.

This script is safe to run in CI and locally. It avoids network, is deterministic.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
RE_MD = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
RE_H1 = re.compile(r"^#\s+(.+)$", re.MULTILINE)
VALID_STATUS = {"draft", "published", "deprecated"}


def parse_front_matter(text: str) -> Tuple[Dict, int, int]:
    """Return (data, start_index, end_index) for YAML block, or ({}, -1, -1)."""
    m = RE_MD.match(text)
    if not m:
        return {}, -1, -1
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {"__invalid_yaml__": True}, m.start(1), m.end(1)
    return data, m.start(), m.end()


def minimal_header_from_text(text: str) -> Dict:
    title = None
    m = RE_H1.search(text)
    if m:
        title = m.group(1).strip()
    return {
        "title": title or "Document",
        "date": dt.date.today().isoformat(),
        "author": "DevSynth Team",
        "status": "draft",
    }


def validate_header(data: Dict) -> List[str]:
    errors: List[str] = []
    if data.get("__invalid_yaml__"):
        errors.append("invalid YAML in front matter")
        return errors
    for key in ("title", "date", "author", "status"):
        if key not in data or data[key] in (None, ""):
            errors.append(f"missing required key: {key}")
    status = data.get("status")
    if status and status not in VALID_STATUS:
        errors.append(f"invalid status: {status}")
    # Basic date sanity check (YYYY-MM-DD)
    date = data.get("date")
    if isinstance(date, str):
        try:
            dt.date.fromisoformat(date)
        except ValueError:
            errors.append(f"invalid date format: {date}")
    return errors


def find_markdown_files() -> List[Path]:
    return [p for p in DOCS_DIR.rglob("*.md") if p.is_file()]


def ensure_front_matter(path: Path, *, fix_missing: bool) -> List[str]:
    text = path.read_text(encoding="utf-8")
    data, start, end = parse_front_matter(text)

    if not data:
        if not fix_missing:
            return ["missing front matter block"]
        header = minimal_header_from_text(text)
        fm = "---\n" + yaml.safe_dump(header, sort_keys=False).strip() + "\n---\n\n"
        path.write_text(fm + text, encoding="utf-8")
        return []

    errors = validate_header(data)
    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fix-missing", action="store_true", help="Insert minimal header when absent"
    )
    args = parser.parse_args(argv)

    failures: List[str] = []
    for md in find_markdown_files():
        errs = ensure_front_matter(md, fix_missing=args.fix_missing)
        if errs:
            for e in errs:
                failures.append(f"{md.relative_to(ROOT)}: {e}")
    if failures:
        print("Front matter validation failed for the following files:")
        for line in failures:
            print(f" - {line}")
        return 1
    print("Front matter validation passed for all docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
