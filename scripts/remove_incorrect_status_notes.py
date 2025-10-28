#!/usr/bin/env python3
"""
Script to remove incorrect "Implementation Status" notes from Markdown files.

This script scans all Markdown files in the docs directory and removes notes
stating "This feature is in progress and not yet implemented" which may
contradict the rest of the document.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Regular expressions to match incorrect implementation status notes
STATUS_PATTERNS = [
    re.compile(r"This feature is \*\*in progress\*\* and not yet implemented"),
    re.compile(r"This feature is in progress and not yet implemented"),
    re.compile(r"Implementation Status:?\s*\*\*in progress\*\*"),
]

# Regular expression to match "last_reviewed" dates in frontmatter
LAST_REVIEWED_PATTERN = re.compile(r"(last_reviewed:\s*)(\d{4}-\d{2}-\d{2})")

# Current date for updating "last_reviewed" dates
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")


def update_markdown_file(file_path):
    """
    Update a Markdown file by:
    1. Removing incorrect implementation status notes
    2. Updating the "last_reviewed" date to the current date

    Returns True if any changes were made, False otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Make a copy of the original content for comparison
        original_content = content

        # Remove incorrect implementation status notes
        for pattern in STATUS_PATTERNS:
            content = pattern.sub("", content)

        # Update "last_reviewed" date if present
        content = LAST_REVIEWED_PATTERN.sub(f"\\1{CURRENT_DATE}", content)

        # Check if any changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error updating {file_path}: {e}", file=sys.stderr)
        return False


def update_files_in_directory(root_dir):
    """
    Update all Markdown files in the given directory and its subdirectories.

    Returns a tuple of (updated_files, error_files).
    """
    updated_files = []
    error_files = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    if update_markdown_file(file_path):
                        updated_files.append(file_path)
                except Exception as e:
                    print(f"Error updating {file_path}: {e}", file=sys.stderr)
                    error_files.append(file_path)

    return updated_files, error_files


def main():
    """Main function."""
    docs_dir = Path(__file__).parent.parent / "docs"

    print(f"Updating Markdown files in {docs_dir}...")
    updated_files, error_files = update_files_in_directory(docs_dir)

    if not updated_files and not error_files:
        print("No Markdown files were updated.")
        return

    if updated_files:
        print(f"Updated {len(updated_files)} Markdown files:")
        for file_path in updated_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")

    if error_files:
        print(f"Failed to update {len(error_files)} Markdown files:")
        for file_path in error_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")


if __name__ == "__main__":
    main()
