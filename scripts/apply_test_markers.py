#!/usr/bin/env python3
"""
Apply Test Markers

This script applies speed markers to test files based on the categorization information
in the progress file. It ensures that markers are properly applied to test files,
which is essential for implementing test filtering and prioritization strategies.

Usage:
    python scripts/apply_test_markers.py [options]

Options:
    --module MODULE       Apply markers to tests in the specified module
    --directory DIR       Apply markers to tests in the specified directory
    --progress-file FILE  Path to the progress file (default: .test_categorization_progress.json)
    --dry-run             Show what would be done without making changes
    --verbose             Show verbose output
    --force               Apply markers even if they already exist

Examples:
    # Apply markers to all tests
    python scripts/apply_test_markers.py

    # Apply markers to tests in a specific module
    python scripts/apply_test_markers.py --module tests/unit/interface

    # Show what would be done without making changes
    python scripts/apply_test_markers.py --dry-run

    # Show verbose output
    python scripts/apply_test_markers.py --verbose
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Constants
PROGRESS_FILE = ".test_categorization_progress.json"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Apply speed markers to test files")

    # Module or directory to analyze
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--module", help="Apply markers to tests in the specified module"
    )
    group.add_argument(
        "--directory",
        default="tests",
        help="Apply markers to tests in the specified directory",
    )

    # Other options
    parser.add_argument(
        "--progress-file", default=PROGRESS_FILE, help="Path to the progress file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--force", action="store_true", help="Apply markers even if they already exist"
    )

    return parser.parse_args()


def load_progress(progress_file: str) -> dict[str, Any]:
    """
    Load the test categorization progress from a file.

    Args:
        progress_file: Path to the progress file

    Returns:
        Dictionary containing categorization progress
    """
    if not os.path.exists(progress_file):
        print(f"Progress file {progress_file} not found")
        return {
            "categorized_tests": {},
            "categorization_counts": {"fast": 0, "medium": 0, "slow": 0, "total": 0},
        }

    try:
        with open(progress_file) as f:
            progress = json.load(f)

        # Ensure the progress file has the expected structure
        if "categorized_tests" not in progress:
            progress["categorized_tests"] = {}

        if "categorization_counts" not in progress:
            progress["categorization_counts"] = {
                "fast": 0,
                "medium": 0,
                "slow": 0,
                "total": 0,
            }

        return progress
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading progress file: {e}")
        return {
            "categorized_tests": {},
            "categorization_counts": {"fast": 0, "medium": 0, "slow": 0, "total": 0},
        }


def find_test_files(directory: str) -> list[Path]:
    """
    Find all test files in a directory.

    Args:
        directory: Directory to search for test files

    Returns:
        List of test file paths
    """
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file(
    file_path: Path,
) -> tuple[
    dict[str, list[str]], dict[int, str], dict[int, list[int]], list[tuple[int, int]]
]:
    """
    Analyze a test file to find existing markers and test line numbers.

    Args:
        file_path: Path to the test file

    Returns:
        Tuple containing:
            - Dictionary mapping test names to existing markers
            - Dictionary mapping line numbers to test names
            - Dictionary mapping test line numbers to misplaced marker line numbers
            - List of tuples (start, end) representing blank line ranges to remove
    """
    existing_markers = {}
    test_line_numbers = {}
    misplaced_markers = {}
    blank_line_ranges = []

    with open(file_path) as f:
        lines = f.readlines()

    # Find all test functions and their markers
    current_markers = []
    current_test_line = None
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for marker lines
        if "@pytest.mark." in line:
            marker_match = re.search(r"@pytest\.mark\.(\w+)", line)
            if marker_match:
                marker = marker_match.group(1)
                if marker in ["fast", "medium", "slow"]:
                    # Check if this marker is properly placed (before a test function)
                    is_properly_placed = False

                    # Look ahead for a test function definition
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip().startswith("def test_") or lines[
                            j
                        ].strip().startswith("async def test_"):
                            # Only consider it properly placed if there's nothing but blank lines or comments between
                            if all(
                                lines[k].strip() == ""
                                or lines[k].strip().startswith("#")
                                for k in range(i + 1, j)
                            ):
                                is_properly_placed = True

                                # Check for blank lines between marker and test function
                                blank_start = i + 1
                                blank_end = j - 1
                                if blank_end >= blank_start and all(
                                    lines[k].strip() == ""
                                    for k in range(blank_start, blank_end + 1)
                                ):
                                    blank_line_ranges.append((blank_start, blank_end))

                                break

                    if is_properly_placed:
                        current_markers.append(marker)
                    else:
                        # This is a misplaced marker, track it
                        if current_test_line is not None:
                            if current_test_line not in misplaced_markers:
                                misplaced_markers[current_test_line] = []
                            misplaced_markers[current_test_line].append(i)

        # Check for test function definitions
        elif line.strip().startswith("def test_") or line.strip().startswith(
            "async def test_"
        ):
            # Extract the test name
            test_match = re.search(r"def\s+(test_\w+)", line)
            if test_match:
                test_name = test_match.group(1)

                # Get the full test name (including class prefix if applicable)
                full_test_name = test_name

                # Store the test line number
                test_line_numbers[i] = full_test_name
                current_test_line = i

                if current_markers:
                    existing_markers[full_test_name] = current_markers.copy()

                current_markers = []

        # Check for markers inside docstrings
        elif '"""' in line or "'''" in line:
            # We're entering or leaving a docstring, check the next few lines for misplaced markers
            docstring_start = i
            docstring_end = None

            # Determine the docstring delimiter
            delimiter = '"""' if '"""' in line else "'''"

            # Check if this is a single-line docstring
            if line.count(delimiter) == 2:
                docstring_end = i
            else:
                # Find the end of the docstring
                for j in range(i + 1, len(lines)):
                    if delimiter in lines[j]:
                        docstring_end = j
                        break

            if docstring_end is not None:
                # Check for markers inside the docstring
                for j in range(docstring_start, docstring_end + 1):
                    if "@pytest.mark." in lines[j]:
                        # This is a misplaced marker inside a docstring
                        if current_test_line is not None:
                            if current_test_line not in misplaced_markers:
                                misplaced_markers[current_test_line] = []
                            misplaced_markers[current_test_line].append(j)

                # Skip to the end of the docstring
                i = docstring_end

        i += 1

    # Check for duplicate markers (multiple markers for the same test)
    duplicate_markers = {}
    for test_line, test_name in test_line_numbers.items():
        # Find all markers for this test
        markers_for_test = []
        for i in range(max(0, test_line - 10), test_line):
            if i < len(lines) and "@pytest.mark." in lines[i]:
                marker_match = re.search(r"@pytest\.mark\.(\w+)", lines[i])
                if marker_match:
                    marker = marker_match.group(1)
                    if marker in ["fast", "medium", "slow"]:
                        markers_for_test.append(i)

        # If there are multiple markers, track them
        if len(markers_for_test) > 1:
            duplicate_markers[test_line] = markers_for_test
            # Add all but the last marker to misplaced markers
            if test_line not in misplaced_markers:
                misplaced_markers[test_line] = []
            misplaced_markers[test_line].extend(markers_for_test[:-1])

    return existing_markers, test_line_numbers, misplaced_markers, blank_line_ranges


def update_test_file(
    file_path: Path,
    test_markers: dict[str, str],
    dry_run: bool = False,
    verbose: bool = False,
    force: bool = False,
) -> tuple[int, int, int]:
    """
    Update a test file with appropriate markers.

    Args:
        file_path: Path to the test file
        test_markers: Dictionary mapping test paths to markers
        dry_run: If True, show what would be done without making changes
        verbose: If True, show verbose output
        force: If True, apply markers even if they already exist

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    # Analyze the file
    existing_markers, test_line_numbers, misplaced_markers, blank_line_ranges = (
        analyze_test_file(file_path)
    )

    if verbose:
        print(f"\nAnalyzing file {file_path}")
        print(f"Found {len(test_line_numbers)} test functions/methods")
        for line_num, test_name in test_line_numbers.items():
            print(f"Line {line_num}: {test_name}")
        if misplaced_markers:
            print(
                f"Found {sum(len(lines) for lines in misplaced_markers.values())} misplaced markers"
            )
            for test_line, marker_lines in misplaced_markers.items():
                test_name = test_line_numbers.get(test_line, "Unknown")
                print(
                    f"  Test {test_name} at line {test_line} has misplaced markers at lines: {marker_lines}"
                )

    if not test_line_numbers:
        if verbose:
            print("No test functions/methods found in file")
        return added, updated, unchanged

    with open(file_path) as f:
        lines = f.readlines()

    # Check if pytest is imported
    has_pytest_import = any("import pytest" in line for line in lines)

    # Add pytest import if needed
    if (
        not has_pytest_import
        and test_line_numbers
        and any(test_name in test_markers for test_name in test_line_numbers.values())
    ):
        # Find the last import line
        last_import_line = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                last_import_line = i

        # Insert pytest import after the last import
        lines.insert(last_import_line + 1, "import pytest\n")

        # Update line numbers for all tests
        test_line_numbers = {k + 1: v for k, v in test_line_numbers.items()}
        misplaced_markers = {
            k + 1: [m + 1 for m in v] for k, v in misplaced_markers.items()
        }

        if dry_run:
            print(f"Would add to {file_path}:{last_import_line+2} - import pytest")

    # First, remove all misplaced markers
    removed_lines = 0
    lines_to_remove = []

    # Collect all misplaced marker lines
    for test_line, marker_lines in misplaced_markers.items():
        lines_to_remove.extend(marker_lines)

    # Sort in reverse order to avoid index shifting when removing lines
    for line_idx in sorted(lines_to_remove, reverse=True):
        if line_idx < len(lines):
            if verbose:
                print(
                    f"Removing misplaced marker at line {line_idx+1}: {lines[line_idx].strip()}"
                )
            lines.pop(line_idx)
            removed_lines += 1

    # Update line numbers after removing misplaced markers
    if removed_lines > 0:
        # Adjust line numbers for test functions
        new_test_line_numbers = {}
        for line_num, test_name in test_line_numbers.items():
            # Count how many removed lines are before this test
            shift = sum(1 for l in lines_to_remove if l < line_num)
            new_test_line_numbers[line_num - shift] = test_name
        test_line_numbers = new_test_line_numbers

    # Process each test function
    modified_lines = []  # Track which lines we've modified to avoid duplicate changes

    for line_num, test_name in sorted(test_line_numbers.items()):
        if verbose:
            print(f"\nProcessing test {test_name} at line {line_num}")

        # Find the marker for this test
        new_marker = None

        # Try different ways to match the test name with the markers dictionary
        # 1. Direct match with the test name
        if test_name in test_markers:
            new_marker = test_markers[test_name]
            if verbose:
                print(f"Direct match found for {test_name}: {new_marker}")

        # 2. Match with file path and test name
        if new_marker is None:
            file_name = file_path.name
            file_path_str = str(file_path)

            # Try different patterns for matching
            patterns = [f"{file_path_str}::{test_name}", f"{file_name}::{test_name}"]

            for pattern in patterns:
                if pattern in test_markers:
                    new_marker = test_markers[pattern]
                    if verbose:
                        print(f"Pattern match found for {pattern}: {new_marker}")
                    break

            # If still no match, try a more flexible approach
            if new_marker is None:
                for marker_path, marker in test_markers.items():
                    if (
                        isinstance(marker_path, str)
                        and test_name in marker_path
                        and (file_name in marker_path or file_path_str in marker_path)
                    ):
                        new_marker = marker
                        if verbose:
                            print(
                                f"Flexible match found for {marker_path}: {new_marker}"
                            )
                        break

        if new_marker is None:
            if verbose:
                print(f"No marker found for {test_name}, skipping")
            continue

        # Check if the test already has the correct marker
        if (
            test_name in existing_markers
            and new_marker in existing_markers[test_name]
            and not force
        ):
            if verbose:
                print(f"Test {test_name} already has marker {new_marker}, skipping")
            unchanged += 1
            continue

        # Find the appropriate position to add or update the marker
        # We want to place it directly before the test function definition
        marker_position = line_num

        # Check if we need to update an existing marker or add a new one
        existing_marker_line = None

        # Search up to 5 lines before the test function to find existing markers
        search_start = max(0, line_num - 5)
        for i in range(search_start, line_num):
            if i >= len(lines):
                continue

            if any(f"@pytest.mark.{m}" in lines[i] for m in ("fast", "medium", "slow")):
                existing_marker_line = i
                break

        # Also check for docstring before the test function
        has_docstring = False
        for i in range(line_num + 1, min(line_num + 10, len(lines))):
            if '"""' in lines[i] or "'''" in lines[i]:
                has_docstring = True
                break

        if existing_marker_line is not None:
            # Update existing marker
            old_line = lines[existing_marker_line]
            lines[existing_marker_line] = old_line.replace(
                f'@pytest.mark.{next(m for m in ("fast", "medium", "slow") if f"@pytest.mark.{m}" in old_line)}',
                f"@pytest.mark.{new_marker}",
            )
            modified_lines.append(existing_marker_line)

            if dry_run:
                print(
                    f"Would update {file_path}:{existing_marker_line+1} - {old_line.strip()} -> {lines[existing_marker_line].strip()}"
                )
            else:
                if verbose:
                    print(
                        f"Updated {file_path}:{existing_marker_line+1} - {old_line.strip()} -> {lines[existing_marker_line].strip()}"
                    )
            updated += 1

            # Remove any extra blank lines between the marker and the test function
            i = existing_marker_line + 1
            while i < line_num:
                if lines[i].strip() == "":
                    lines.pop(i)
                    line_num -= 1
                    # Update line numbers for subsequent tests
                    test_line_numbers = {
                        k - 1 if k > i else k: v for k, v in test_line_numbers.items()
                    }
                else:
                    i += 1
        else:
            # Add new marker
            # Get the indentation of the test function
            indent = re.match(r"(\s*)", lines[line_num]).group(1)
            marker_line = f"{indent}@pytest.mark.{new_marker}\n"

            # Insert marker directly before the test function
            lines.insert(line_num, marker_line)
            modified_lines.append(line_num)

            # Update line numbers for subsequent tests
            test_line_numbers = {
                k + 1 if k >= line_num else k: v for k, v in test_line_numbers.items()
            }

            if dry_run:
                print(f"Would add to {file_path}:{line_num+1} - {marker_line.strip()}")
            else:
                if verbose:
                    print(f"Added to {file_path}:{line_num+1} - {marker_line.strip()}")
            added += 1

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0 or removed_lines > 0):
        with open(file_path, "w") as f:
            f.writelines(lines)

    return added, updated, unchanged


def main():
    """Main function."""
    args = parse_args()

    # Determine the directory to analyze
    directory = args.module if args.module else args.directory

    print(f"Applying markers to tests in {directory}...")

    # Load progress
    progress = load_progress(args.progress_file)
    categorized_tests = progress.get("categorized_tests", {})

    print(
        f"Loaded {len(categorized_tests)} categorized tests from {args.progress_file}"
    )

    # Find test files
    test_files = find_test_files(directory)
    print(f"Found {len(test_files)} test files")

    # Apply markers to test files
    total_added = 0
    total_updated = 0
    total_unchanged = 0

    for file_path in test_files:
        if args.verbose:
            print(f"\nProcessing file {file_path}")

        added, updated, unchanged = update_test_file(
            file_path, categorized_tests, args.dry_run, args.verbose, args.force
        )

        total_added += added
        total_updated += updated
        total_unchanged += unchanged

    action = "Would " if args.dry_run else ""
    print(
        f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
    )

    print("\nMarker application complete")

    # Print tips for running tests by speed category
    print("\nTips for running tests by speed category:")
    print("  - Run fast tests: poetry run devsynth run-tests --fast")
    print("  - Run medium tests: poetry run devsynth run-tests --medium")
    print("  - Run slow tests: poetry run devsynth run-tests --slow")
    print(
        "  - Run fast and medium tests: poetry run devsynth run-tests --fast --medium"
    )

    # Print tips for verifying markers
    print("\nTo verify markers:")
    print("  - Run verify_test_markers.py: python scripts/verify_test_markers.py")
    print(
        "  - Verify markers in a specific module: python scripts/verify_test_markers.py --module tests/unit/interface"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
