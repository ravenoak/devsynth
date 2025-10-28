#!/usr/bin/env python3
"""
Script to find Markdown files with outdated "last_reviewed" dates.

This script scans all Markdown files in the docs directory and identifies files
with "last_reviewed" dates that are older than the current date.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Current date for comparison (August 2, 2025)
CURRENT_DATE = datetime(2025, 8, 2)

# Regular expression to match "last_reviewed" dates in frontmatter
LAST_REVIEWED_PATTERN = re.compile(r"last_reviewed:\s*(\d{4}-\d{2}-\d{2})")


def parse_date(date_str):
    """Parse a date string in the format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def is_outdated(date_str):
    """Check if a date string is outdated compared to the current date."""
    date = parse_date(date_str)
    if date is None:
        return False
    return date < CURRENT_DATE


def scan_markdown_file(file_path):
    """Scan a Markdown file for outdated "last_reviewed" dates."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        match = LAST_REVIEWED_PATTERN.search(content)
        if match:
            date_str = match.group(1)
            if is_outdated(date_str):
                return date_str
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return None


def find_outdated_files(root_dir):
    """Find all Markdown files with outdated "last_reviewed" dates."""
    outdated_files = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                outdated_date = scan_markdown_file(file_path)
                if outdated_date:
                    outdated_files.append((file_path, outdated_date))

    return outdated_files


def main():
    """Main function."""
    docs_dir = Path(__file__).parent.parent / "docs"

    print(f"Scanning Markdown files in {docs_dir}...")
    outdated_files = find_outdated_files(docs_dir)

    if not outdated_files:
        print("No Markdown files with outdated 'last_reviewed' dates found.")
        return

    print(
        f"Found {len(outdated_files)} Markdown files with outdated 'last_reviewed' dates:"
    )
    for file_path, date in outdated_files:
        rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
        print(f"- {rel_path} (last_reviewed: {date})")


if __name__ == "__main__":
    main()
