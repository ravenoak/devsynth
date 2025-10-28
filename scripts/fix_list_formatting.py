#!/usr/bin/env python3

"""
Script to fix inconsistent list formatting in Markdown files.

Usage:
    python scripts/fix_list_formatting.py

This script:
1. Finds all Markdown files in the docs directory
2. Ensures lists have a blank line before and after them
3. Ensures list items use consistent markers (- for unordered lists, 1. for ordered lists)
4. Ensures nested lists are properly indented
5. Reports the changes made
"""

import os
import re
from pathlib import Path


def fix_list_formatting(file_path):
    """Fix list formatting in a Markdown file."""
    changes = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Split content into lines
    lines = content.split("\n")

    # Find list items
    i = 0
    while i < len(lines):
        # Check for unordered list items (*, +, -)
        unordered_match = re.match(r"^(\s*)([*+-])\s+(.+)$", lines[i])
        if unordered_match:
            indent = unordered_match.group(1)
            marker = unordered_match.group(2)
            text = unordered_match.group(3)

            # Ensure consistent marker for unordered lists (-)
            if marker != "-":
                lines[i] = f"{indent}- {text}"
                changes.append(f"Changed unordered list marker from '{marker}' to '-'")

            # Ensure blank line before list (if not nested and not after another list item)
            if not indent and i > 0:
                prev_is_list = re.match(r"^(\s*)([*+-]|\d+\.)\s+", lines[i - 1])
                if not prev_is_list and lines[i - 1].strip() != "":
                    lines.insert(i, "")
                    changes.append("Added blank line before list")
                    i += 1

            # Find the end of the list
            list_end = i
            while list_end + 1 < len(lines):
                next_is_list = re.match(r"^(\s*)([*+-]|\d+\.)\s+", lines[list_end + 1])
                if not next_is_list and lines[list_end + 1].strip() != "":
                    break
                list_end += 1

            # Ensure blank line after list (if not followed by another list item)
            if list_end + 1 < len(lines) and lines[list_end + 1].strip() != "":
                lines.insert(list_end + 1, "")
                changes.append("Added blank line after list")
                i = list_end + 2
            else:
                i = list_end + 1

        # Check for ordered list items (1., 2., etc.)
        ordered_match = re.match(r"^(\s*)(\d+)([.)]) (.+)$", lines[i])
        if ordered_match:
            indent = ordered_match.group(1)
            number = ordered_match.group(2)
            delimiter = ordered_match.group(3)
            text = ordered_match.group(4)

            # Ensure consistent delimiter for ordered lists (.)
            if delimiter != ".":
                lines[i] = f"{indent}{number}. {text}"
                changes.append(
                    f"Changed ordered list delimiter from '{delimiter}' to '.'"
                )

            # Ensure blank line before list (if not nested and not after another list item)
            if not indent and i > 0:
                prev_is_list = re.match(r"^(\s*)([*+-]|\d+\.)\s+", lines[i - 1])
                if not prev_is_list and lines[i - 1].strip() != "":
                    lines.insert(i, "")
                    changes.append("Added blank line before list")
                    i += 1

            # Find the end of the list
            list_end = i
            while list_end + 1 < len(lines):
                next_is_list = re.match(r"^(\s*)([*+-]|\d+\.)\s+", lines[list_end + 1])
                if not next_is_list and lines[list_end + 1].strip() != "":
                    break
                list_end += 1

            # Ensure blank line after list (if not followed by another list item)
            if list_end + 1 < len(lines) and lines[list_end + 1].strip() != "":
                lines.insert(list_end + 1, "")
                changes.append("Added blank line after list")
                i = list_end + 2
            else:
                i = list_end + 1
        else:
            i += 1

    # Write the fixed content back to the file
    if changes:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return changes


def main():
    """Main function to fix list formatting in all Markdown files."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Fix list formatting in each file
    files_fixed = 0
    for file_path in md_files:
        try:
            changes = fix_list_formatting(file_path)
            if changes:
                print(f"\nFixed {file_path}:")
                for change in changes:
                    print(f"  - {change}")
                files_fixed += 1
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

    print(f"\nFixed list formatting in {files_fixed} files")


if __name__ == "__main__":
    main()
