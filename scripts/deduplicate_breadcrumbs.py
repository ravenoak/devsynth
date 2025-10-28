#!/usr/bin/env python3
"""
Breadcrumb Deduplication Script for DevSynth Documentation Harmonization

This script removes duplicate breadcrumb sections from documentation files,
keeping only the first occurrence in each file.
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


def find_and_remove_duplicate_breadcrumbs(
    file_path: Path, dry_run: bool = True
) -> tuple[bool, int]:
    """
    Find and remove duplicate breadcrumb sections from a file.
    Returns (changed, duplicates_removed)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False, 0

    # Find all breadcrumb sections
    breadcrumb_sections = []
    i = 0
    while i < len(lines):
        if '<div class="breadcrumbs">' in lines[i]:
            start_idx = i
            # Find the end of this breadcrumb section
            end_idx = i
            for j in range(i, min(i + 10, len(lines))):  # Look ahead max 10 lines
                if "</div>" in lines[j]:
                    end_idx = j
                    break
            breadcrumb_sections.append((start_idx, end_idx))
            i = end_idx + 1
        else:
            i += 1

    # If no duplicates, return early
    if len(breadcrumb_sections) <= 1:
        return False, 0

    duplicates_removed = len(breadcrumb_sections) - 1

    if dry_run:
        print(
            f"DRY RUN: Would remove {duplicates_removed} duplicate breadcrumb(s) from {file_path}"
        )
        return True, duplicates_removed

    # Remove duplicate sections (keep first, remove rest)
    # Work backwards to maintain line indices
    for start_idx, end_idx in reversed(breadcrumb_sections[1:]):
        # Remove the duplicate section including surrounding blank lines
        del lines[start_idx : end_idx + 1]

        # Clean up extra blank lines that might be left
        if start_idx < len(lines) and lines[start_idx].strip() == "":
            del lines[start_idx]

    # Write the modified content back
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(
            f"✅ Removed {duplicates_removed} duplicate breadcrumb(s) from {file_path}"
        )
        return True, duplicates_removed
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return False, 0


def process_documentation_files(
    docs_dir: Path, dry_run: bool = True
) -> tuple[int, int, int]:
    """
    Process all markdown files in the documentation directory.
    Returns (files_processed, files_changed, total_duplicates_removed)
    """
    files_processed = 0
    files_changed = 0
    total_duplicates_removed = 0

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        files_processed += 1
        changed, duplicates = find_and_remove_duplicate_breadcrumbs(md_file, dry_run)
        if changed:
            files_changed += 1
            total_duplicates_removed += duplicates

    return files_processed, files_changed, total_duplicates_removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate breadcrumb sections from documentation"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the deduplication (default is dry run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to process"
    )

    args = parser.parse_args()

    # Default to dry run unless --execute is specified
    dry_run = not args.execute
    if args.dry_run:
        dry_run = True

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print("=" * 60)
    print("BREADCRUMB DEDUPLICATION")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Directory: {docs_dir}")
    print()

    files_processed, files_changed, total_duplicates = process_documentation_files(
        docs_dir, dry_run
    )

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {files_processed}")
    print(f"Files with duplicates: {files_changed}")
    print(
        f"Total duplicates {'would be ' if dry_run else ''}removed: {total_duplicates}"
    )

    if dry_run and total_duplicates > 0:
        print()
        print("To execute the deduplication, run:")
        print(f"python {sys.argv[0]} --execute")
    elif not dry_run and total_duplicates > 0:
        print()
        print("✅ Deduplication completed successfully!")
        print("Run the analysis script to verify results:")
        print("python scripts/analyze_breadcrumbs.py --validate")

    print("=" * 60)


if __name__ == "__main__":
    main()
