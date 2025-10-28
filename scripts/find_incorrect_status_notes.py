#!/usr/bin/env python3
"""
Script to find Markdown files with incorrect "Implementation Status" notes.

This script scans all Markdown files in the docs directory and identifies files
with notes stating "This feature is in progress and not yet implemented" which
may contradict the rest of the document.
"""

import os
import re
import sys
from pathlib import Path

# Regular expressions to match incorrect implementation status notes
STATUS_PATTERNS = [
    re.compile(r"This feature is \*\*in progress\*\* and not yet implemented"),
    re.compile(r"This feature is in progress and not yet implemented"),
    re.compile(r"Implementation Status:?\s*\*\*in progress\*\*"),
]


def scan_markdown_file(file_path):
    """Scan a Markdown file for incorrect implementation status notes."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        for pattern in STATUS_PATTERNS:
            if pattern.search(content):
                return True
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return False


def find_files_with_incorrect_status(root_dir):
    """Find all Markdown files with incorrect implementation status notes."""
    incorrect_files = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                if scan_markdown_file(file_path):
                    incorrect_files.append(file_path)

    return incorrect_files


def main():
    """Main function."""
    docs_dir = Path(__file__).parent.parent / "docs"

    print(f"Scanning Markdown files in {docs_dir}...")
    incorrect_files = find_files_with_incorrect_status(docs_dir)

    if not incorrect_files:
        print("No Markdown files with incorrect implementation status notes found.")
        return

    print(
        f"Found {len(incorrect_files)} Markdown files with incorrect implementation status notes:"
    )
    for file_path in incorrect_files:
        rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
        print(f"- {rel_path}")


if __name__ == "__main__":
    main()
