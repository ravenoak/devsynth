#!/usr/bin/env python3
"""
Apply test markers from the .test_categorization_progress.json file to test files.

This script reads the .test_categorization_progress.json file and applies the markers
to the corresponding test files. It handles various edge cases and ensures that markers
are applied correctly.
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Regular expressions for identifying test functions, classes, and markers
FUNCTION_PATTERN = re.compile(r"def\s+(test_\w+)\s*\(")
CLASS_PATTERN = re.compile(r"class\s+(Test\w+)\s*\(")
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow)")

# Default progress file
DEFAULT_PROGRESS_FILE = ".test_categorization_progress.json"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Apply test markers from progress file to test files."
    )
    parser.add_argument(
        "-p",
        "--progress-file",
        default=DEFAULT_PROGRESS_FILE,
        help=f"File containing categorization progress (default: {DEFAULT_PROGRESS_FILE})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information about changes"
    )
    parser.add_argument(
        "--module", help="Specific module to update (e.g., tests/unit/interface)"
    )
    return parser.parse_args()


def load_progress(progress_file: str) -> dict[str, Any]:
    """
    Load categorization progress from file.

    Args:
        progress_file: Path to the progress file

    Returns:
        Dictionary containing categorization progress
    """
    if os.path.exists(progress_file):
        try:
            with open(progress_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error loading progress file {progress_file}")
            return {
                "categorized_tests": {},
                "categorization_counts": {
                    "fast": 0,
                    "medium": 0,
                    "slow": 0,
                    "total": 0,
                },
            }
    else:
        print(f"Progress file {progress_file} not found")
        return {
            "categorized_tests": {},
            "categorization_counts": {"fast": 0, "medium": 0, "slow": 0, "total": 0},
        }


def find_test_files(directory: str | None = None) -> list[Path]:
    """
    Find all test files in the given directory or in the tests directory if not specified.

    Args:
        directory: Directory to search (default: tests)

    Returns:
        List of test file paths
    """
    if directory is None:
        directory = "tests"

    # Check if directory is actually a file path
    if os.path.isfile(directory):
        if directory.endswith(".py") and os.path.basename(directory).startswith(
            "test_"
        ):
            return [Path(directory)]
        else:
            return []

    # If it's a directory, search for test files
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))

    return test_files


def analyze_test_file(file_path: Path) -> tuple[dict[str, list[str]], dict[int, str]]:
    """
    Analyze a test file to extract existing markers and test functions.

    Args:
        file_path: Path to the test file

    Returns:
        Tuple containing:
        - Dictionary mapping test names to their existing markers
        - Dictionary mapping line numbers to test names
    """
    existing_markers = {}
    test_line_numbers = {}

    with open(file_path) as f:
        lines = f.readlines()

    current_markers = []
    current_class = None

    for i, line in enumerate(lines):
        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for class definitions
        class_match = CLASS_PATTERN.search(line)
        if class_match:
            current_class = class_match.group(1)
            # Reset markers when entering a new class
            current_markers = []
            continue

        # Check for test functions or methods
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)

            # For class methods, prefix with class name
            if current_class:
                full_test_name = f"{current_class}::{test_name}"
            else:
                full_test_name = test_name

            test_line_numbers[i] = full_test_name

            if current_markers:
                existing_markers[full_test_name] = current_markers.copy()

            current_markers = []

    return existing_markers, test_line_numbers


def update_test_file(
    file_path: Path,
    categorized_tests: dict[str, str],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """
    Update a test file with markers from the categorized_tests dictionary.

    Args:
        file_path: Path to the test file
        categorized_tests: Dictionary mapping test paths to their markers
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about changes

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    # Analyze the file
    existing_markers, test_line_numbers = analyze_test_file(file_path)

    if verbose:
        print(f"\nAnalyzing file {file_path}")
        print(f"Found {len(test_line_numbers)} test functions/methods")
        for line_num, test_name in test_line_numbers.items():
            print(f"Line {line_num}: {test_name}")

    if not test_line_numbers:
        if verbose:
            print("No test functions/methods found in file")
        return added, updated, unchanged

    with open(file_path) as f:
        lines = f.readlines()

    # Check if pytest is imported
    has_pytest_import = any("import pytest" in line for line in lines)

    # Add pytest import if needed
    if not has_pytest_import and test_line_numbers:
        # Find the last import line
        last_import_line = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                last_import_line = i

        # Insert pytest import after the last import
        lines.insert(last_import_line + 1, "import pytest\n")

        # Update line numbers for all tests
        test_line_numbers = {k + 1: v for k, v in test_line_numbers.items()}

        if dry_run:
            print(f"Would add to {file_path}:{last_import_line+2} - import pytest")

    # Process each test function
    modified_lines = []  # Track which lines we've modified to avoid duplicate changes

    for line_num, test_name in sorted(test_line_numbers.items()):
        if verbose:
            print(f"\nProcessing test {test_name} at line {line_num}")

        # Try to find the test in the categorized_tests dictionary
        test_path = str(file_path) + "::" + test_name

        # Try different variations of the test path
        if test_path in categorized_tests:
            new_marker = categorized_tests[test_path]
            if verbose:
                print(f"Found marker for {test_path}: {new_marker}")
        elif test_name in categorized_tests:
            new_marker = categorized_tests[test_name]
            if verbose:
                print(f"Found marker for {test_name}: {new_marker}")
        else:
            # Try to find a matching test path
            matching_paths = [
                path
                for path in categorized_tests.keys()
                if isinstance(path, str)
                and test_name in path
                and str(file_path) in path
            ]

            if matching_paths:
                new_marker = categorized_tests[matching_paths[0]]
                if verbose:
                    print(f"Found marker for {matching_paths[0]}: {new_marker}")
            else:
                if verbose:
                    print(f"No marker found for {test_name}, skipping")
                continue

        # Check if the test already has the correct marker
        if test_name in existing_markers and new_marker in existing_markers[test_name]:
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
            updated += 1
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
            added += 1

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0):
        with open(file_path, "w") as f:
            f.writelines(lines)

    return added, updated, unchanged


def main():
    """Main function."""
    args = parse_args()

    # Load progress
    progress = load_progress(args.progress_file)
    categorized_tests = progress.get("categorized_tests", {})

    print(
        f"Loaded {len(categorized_tests)} categorized tests from {args.progress_file}"
    )

    # Find test files
    test_files = find_test_files(args.module)
    print(f"Found {len(test_files)} test files")

    # Update test files
    total_added = 0
    total_updated = 0
    total_unchanged = 0

    for i, file_path in enumerate(test_files):
        if i % 10 == 0:
            print(f"Processing file {i+1}/{len(test_files)}...")

        added, updated, unchanged = update_test_file(
            file_path, categorized_tests, args.dry_run, args.verbose
        )

        if args.verbose or added > 0 or updated > 0:
            print(
                f"Results for {file_path}: added={added}, updated={updated}, unchanged={unchanged}"
            )

        total_added += added
        total_updated += updated
        total_unchanged += unchanged

    action = "Would " if args.dry_run else ""
    print(
        f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
