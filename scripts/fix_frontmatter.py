#!/usr/bin/env python3
"""Script to fix frontmatter formatting issues in Markdown files.

This script scans all Markdown files in the docs directory and fixes
frontmatter formatting issues, such as the closing --- being on the same line
as the last frontmatter field. When run with ``--check`` it reports files that
need updates without modifying them and exits with status 1 if any are found.
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Regular expression to match YAML frontmatter with closing --- on the same line
# This pattern is more flexible and can handle cases where:
# 1. The opening --- is immediately followed by the first frontmatter field
# 2. The closing --- is on the same line as the last frontmatter field
INVALID_FRONTMATTER_PATTERN = re.compile(r"^---(.*?)([^\n]+)---\s*\n", re.DOTALL)

# Regular expression to match YAML frontmatter with proper formatting
VALID_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def fix_frontmatter(file_path: str, check: bool = False) -> bool:
    """Fix frontmatter formatting issues in a Markdown file.

    Args:
        file_path: The path to the file
        check: If True, do not modify files; only report issues.

    Returns:
        True if the file needs or had updates, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if the file has invalid frontmatter (closing --- on the same line)
        invalid_match = INVALID_FRONTMATTER_PATTERN.search(content)
        if invalid_match:
            # Extract the frontmatter content and the last line
            frontmatter_content = invalid_match.group(1)
            last_line = invalid_match.group(2)

            # Fix the frontmatter by ensuring the closing --- is on a separate line
            fixed_content = (
                f"---\n{frontmatter_content}{last_line}\n---\n"
                + content[invalid_match.end() :]
            )

            if not check:
                # Write the fixed content back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)

            return True

        # Check if the file has valid frontmatter
        valid_match = VALID_FRONTMATTER_PATTERN.search(content)
        if not valid_match:
            # No frontmatter found, nothing to fix
            return False

        # No changes needed
        return False

    except Exception as e:
        print(f"Error fixing frontmatter in {file_path}: {e}", file=sys.stderr)
        return False


def fix_files_in_directory(root_dir: str, check: bool = False):
    """Fix frontmatter issues for all Markdown files below ``root_dir``.

    Args:
        root_dir: The root directory to scan
        check: If True, do not modify files; only report issues

    Returns:
        A tuple of ``(updated_files, error_files)``
    """
    updated_files = []
    error_files = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    if fix_frontmatter(file_path, check=check):
                        updated_files.append(file_path)
                except Exception as e:
                    print(
                        f"Error fixing frontmatter in {file_path}: {e}", file=sys.stderr
                    )
                    error_files.append(file_path)

    return updated_files, error_files


def main() -> None:
    """Entrypoint for command line execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Scan for frontmatter issues without modifying files; exits 1 if any are found.",
    )
    args = parser.parse_args()

    docs_dir = Path(__file__).parent.parent / "docs"

    if args.check:
        print(f"Checking frontmatter formatting in Markdown files in {docs_dir}...")
    else:
        print(
            f"Fixing frontmatter formatting issues in Markdown files in {docs_dir}..."
        )

    updated_files, error_files = fix_files_in_directory(docs_dir, check=args.check)

    if args.check:
        if updated_files:
            print(
                f"Frontmatter formatting issues found in {len(updated_files)} Markdown file(s):"
            )
            for file_path in updated_files:
                rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
                print(f"- {rel_path}")
            sys.exit(1)
        else:
            print("No frontmatter formatting issues found.")
            return

    if not updated_files and not error_files:
        print("No Markdown files were updated.")
        return

    if updated_files:
        print(
            f"Fixed frontmatter formatting issues in {len(updated_files)} Markdown files:"
        )
        for file_path in updated_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")

    if error_files:
        print(
            f"Failed to fix frontmatter formatting issues in {len(error_files)} Markdown files:"
        )
        for file_path in error_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")


if __name__ == "__main__":
    main()
