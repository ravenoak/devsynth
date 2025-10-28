#!/usr/bin/env python3
"""
Fix Behavior Steps Syntax

This script fixes common syntax errors in the behavior steps test files:
1. Incorrect decorator placement (particularly pytest.mark decorators between other decorators and their arguments)
2. Other common syntax issues in behavior test files

Usage:
    python scripts/fix_behavior_syntax.py [options]

Options:
    --module MODULE         Specific module to process (e.g., tests/behavior/steps)
    --file FILE             Specific file to process
    --dry-run               Show changes without modifying files
    --verbose               Show detailed information
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix syntax errors in behavior test files."
    )
    parser.add_argument(
        "--module",
        default="tests/behavior/steps",
        help="Specific module to process (default: tests/behavior/steps)",
    )
    parser.add_argument("--file", help="Specific file to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    return parser.parse_args()


def get_files_to_process(module: str, specific_file: str | None = None) -> list[str]:
    """Get list of files to process."""
    if specific_file:
        return [specific_file]

    files = []
    for root, _, filenames in os.walk(module):
        for filename in filenames:
            if filename.endswith(".py") and filename.startswith("test_"):
                files.append(os.path.join(root, filename))
    return files


def fix_decorator_placement(content: str) -> str:
    """Fix incorrect decorator placement."""
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for decorator patterns like @when( followed by @pytest.mark
        if (
            i < len(lines) - 1
            and re.match(r"^@(when|given|then)\(", line)
            and not line.strip().endswith(")")
            and lines[i + 1].strip().startswith("@pytest.mark")
        ):

            # Store the decorator and its argument parts
            decorator_start = line
            pytest_mark = lines[i + 1]

            # Find the closing part of the decorator
            j = i + 2
            decorator_parts = [decorator_start]

            while j < len(lines) and not re.match(r"^def\s+\w+\(.*\):", lines[j]):
                if not lines[j].strip().startswith("@"):
                    decorator_parts.append(lines[j])
                j += 1

            if j < len(lines):
                function_def = lines[j]

                # Reconstruct the decorator properly
                fixed_lines.append("".join(decorator_parts).rstrip())
                fixed_lines.append(pytest_mark)
                fixed_lines.append(function_def)

                i = j + 1
                continue

        # Check for @pytest.mark between decorator and function
        elif (
            i > 0
            and i < len(lines) - 1
            and lines[i - 1].strip().startswith("@")
            and line.strip().startswith("@pytest.mark")
            and re.match(r"^def\s+\w+\(.*\):", lines[i + 1])
        ):

            # Swap the order of decorators
            fixed_lines.pop()  # Remove the previous decorator
            fixed_lines.append(line)  # Add pytest.mark first
            fixed_lines.append(lines[i - 1])  # Add the other decorator second
            fixed_lines.append(lines[i + 1])  # Add function definition

            i += 2
            continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_syntax_errors(content: str) -> str:
    """Fix other common syntax errors."""
    # Fix unmatched parentheses, brackets, etc.
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for lines that end with unmatched syntax
        if line.strip().endswith(("(", "[", "{")) and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line.startswith(("@", "def", "class")):
                # This is likely an incomplete line
                fixed_line = line + ")"  # Add closing parenthesis
                fixed_lines.append(fixed_line)
                i += 1
                continue

        # Check for decorator and function definition on one line
        if line.strip().startswith("@when(") and "def " in line:
            # Split into decorator and function parts
            parts = line.split("def ", 1)
            if len(parts) == 2:
                decorator_part = parts[0].strip()
                function_part = "def " + parts[1].strip()

                # Add the decorator part
                fixed_lines.append(decorator_part)

                # Add the function part
                fixed_lines.append(function_part)
                i += 1
                continue

        # Check for one-line decorator that should be split
        if line.strip().startswith("@when(") and not line.strip().endswith(")"):
            # Find the closing parenthesis
            j = i
            decorator_parts = [line]
            found_closing = False

            while j + 1 < len(lines) and not found_closing:
                j += 1
                next_line = lines[j]

                if ")" in next_line and "def " in next_line:
                    # Split at the closing parenthesis
                    parts = next_line.split(")", 1)
                    if len(parts) == 2:
                        decorator_parts.append(parts[0] + ")")
                        function_part = parts[1].strip()

                        # Add the decorator parts
                        fixed_lines.append("".join(decorator_parts))

                        # Add the function part if it's a function definition
                        if function_part.startswith("def "):
                            fixed_lines.append(function_part)

                        found_closing = True
                        i = j + 1
                        break
                elif "def " in next_line:
                    # If we find a function definition without closing the decorator,
                    # assume the decorator is complete and add a closing parenthesis
                    fixed_lines.append("".join(decorator_parts) + ")")
                    fixed_lines.append(next_line)
                    found_closing = True
                    i = j + 1
                    break
                else:
                    decorator_parts.append(next_line)

            if found_closing:
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_file(file_path: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """Fix syntax errors in a file."""
    try:
        with open(file_path) as f:
            content = f.read()

        # Apply fixes
        fixed_content = content
        fixed_content = fix_decorator_placement(fixed_content)
        fixed_content = fix_syntax_errors(fixed_content)

        # Check if changes were made
        if content != fixed_content:
            if verbose:
                print(f"Fixed syntax errors in {file_path}")

            if not dry_run:
                with open(file_path, "w") as f:
                    f.write(fixed_content)
            return True
        else:
            if verbose:
                print(f"No syntax errors found in {file_path}")
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function."""
    args = parse_args()

    files = get_files_to_process(args.module, args.file)

    if not files:
        print(f"No files found in {args.module}")
        return

    fixed_count = 0
    for file_path in files:
        if fix_file(file_path, args.dry_run, args.verbose):
            fixed_count += 1

    print(f"Fixed {fixed_count} files out of {len(files)}")

    if args.dry_run:
        print("Dry run completed. No files were modified.")


if __name__ == "__main__":
    main()
