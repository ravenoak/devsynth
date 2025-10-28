#!/usr/bin/env python3
"""
Breadcrumb Analysis Script for DevSynth Documentation Harmonization

This script analyzes breadcrumb patterns in documentation files to identify
duplications and generate reports for the harmonization process.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def find_breadcrumb_patterns(file_path: Path) -> list[tuple[int, str]]:
    """Find breadcrumb patterns in a file and return line numbers and content."""
    breadcrumbs = []
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Look for breadcrumb div patterns
            if '<div class="breadcrumbs">' in line:
                # Capture the breadcrumb section (usually 3-4 lines)
                breadcrumb_section = []
                start_line = i

                # Collect the breadcrumb section
                for j in range(i - 1, min(i + 4, len(lines))):
                    if j < len(lines):
                        breadcrumb_section.append(lines[j].strip())
                        if "</div>" in lines[j]:
                            break

                breadcrumbs.append((start_line, "\n".join(breadcrumb_section)))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return breadcrumbs


def analyze_documentation_breadcrumbs(
    docs_dir: Path,
) -> dict[str, list[tuple[int, str]]]:
    """Analyze all markdown files in docs directory for breadcrumb patterns."""
    breadcrumb_data = {}

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        breadcrumbs = find_breadcrumb_patterns(md_file)
        if breadcrumbs:
            relative_path = str(md_file.relative_to(docs_dir.parent))
            breadcrumb_data[relative_path] = breadcrumbs

    return breadcrumb_data


def generate_report(
    breadcrumb_data: dict[str, list[tuple[int, str]]], validate: bool = False
) -> None:
    """Generate analysis report of breadcrumb patterns."""
    total_files = len(breadcrumb_data)
    total_breadcrumbs = sum(
        len(breadcrumbs) for breadcrumbs in breadcrumb_data.values()
    )
    duplicate_files = sum(
        1 for breadcrumbs in breadcrumb_data.values() if len(breadcrumbs) > 1
    )
    total_duplicates = sum(
        len(breadcrumbs) - 1
        for breadcrumbs in breadcrumb_data.values()
        if len(breadcrumbs) > 1
    )

    print("=" * 60)
    print("BREADCRUMB ANALYSIS REPORT")
    print("=" * 60)
    print(f"Files with breadcrumbs: {total_files}")
    print(f"Total breadcrumb instances: {total_breadcrumbs}")
    print(f"Files with duplicate breadcrumbs: {duplicate_files}")
    print(f"Total duplicate instances: {total_duplicates}")
    print()

    if validate:
        if total_duplicates == 0:
            print("✅ VALIDATION PASSED: No duplicate breadcrumbs found!")
            return
        else:
            print("❌ VALIDATION FAILED: Duplicate breadcrumbs still exist")

    if duplicate_files > 0:
        print("FILES WITH DUPLICATE BREADCRUMBS:")
        print("-" * 40)

        for file_path, breadcrumbs in breadcrumb_data.items():
            if len(breadcrumbs) > 1:
                print(f"\n📁 {file_path}")
                print(f"   Duplicate count: {len(breadcrumbs) - 1}")
                for line_num, content in breadcrumbs:
                    print(f"   Line {line_num}: {content.split(chr(10))[0][:50]}...")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze breadcrumb patterns in documentation"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate that no duplicates exist"
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to analyze"
    )

    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print(f"Analyzing breadcrumbs in: {docs_dir}")
    breadcrumb_data = analyze_documentation_breadcrumbs(docs_dir)
    generate_report(breadcrumb_data, args.validate)

    # Exit with error code if validation fails
    if args.validate:
        total_duplicates = sum(
            len(breadcrumbs) - 1
            for breadcrumbs in breadcrumb_data.values()
            if len(breadcrumbs) > 1
        )
        sys.exit(0 if total_duplicates == 0 else 1)


if __name__ == "__main__":
    main()
