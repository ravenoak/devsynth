#!/usr/bin/env python
"""
Script to standardize the placement of pytest markers in test files.

This script ensures that markers are placed consistently in a way that both
apply_speed_markers.py and common_test_collector.py can reliably detect them.

The script:
1. Finds all test files in the project
2. Analyzes each file to identify test functions and their markers
3. Standardizes marker placement by ensuring they are directly above the test function
4. Updates the test collection cache to reflect the changes

Usage:
    python scripts/standardize_marker_placement.py [options]

Options:
    --dry-run             Show changes without modifying files
    --category CAT        Only process tests in the specified category (unit, integration, behavior, all)
    --verbose             Show verbose output
    --no-cache-update     Don't update the test collection cache after modifying files
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Import common test collector for cache invalidation
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import clear_cache, invalidate_cache_for_files
except ImportError:
    print(
        "Warning: common_test_collector.py not found. Cache invalidation will be skipped."
    )

    # Define dummy functions if import fails
    def invalidate_cache_for_files(file_paths, verbose=False):
        if verbose:
            print("Cache invalidation skipped (common_test_collector.py not found)")

    def clear_cache(selective=False):
        print("Cache clearing skipped (common_test_collector.py not found)")


# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "property": "tests/property",
}

# Regex patterns
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
CLASS_PATTERN = re.compile(r"class\s+(\w+)\s*\(")
FUNCTION_PATTERN = re.compile(r"def\s+(test_\w+)\s*\(")
INDENTATION_PATTERN = re.compile(r"^(\s*)")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Standardize the placement of pytest markers in test files."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "property", "all"],
        default="all",
        help="Only process tests in the specified category",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--no-cache-update",
        action="store_true",
        help="Don't update the test collection cache after modifying files",
    )
    return parser.parse_args()


def find_test_files(directory: str) -> list[Path]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file(
    file_path: Path,
) -> tuple[
    dict[str, list[str]], dict[int, str], dict[int, str], list[tuple[int, int, str]]
]:
    """
    Analyze a test file to extract existing markers, test functions, and classes.

    Returns:
        Tuple containing:
        - Dictionary mapping test names to their existing markers
        - Dictionary mapping line numbers to test names
        - Dictionary mapping line numbers to class names
        - List of tuples (start_line, end_line, indentation) for each test function
    """
    existing_markers = {}
    test_line_numbers = {}
    class_line_numbers = {}
    test_function_ranges = []

    with open(file_path) as f:
        lines = f.readlines()

    current_markers = []
    current_class = None
    current_class_indent = ""
    in_class = False

    for i, line in enumerate(lines):
        # Check for class definitions
        class_match = CLASS_PATTERN.search(line)
        if class_match:
            current_class = class_match.group(1)
            class_line_numbers[i] = current_class
            current_class_indent = INDENTATION_PATTERN.match(line).group(1)
            in_class = True

        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)
            test_line_numbers[i] = test_name

            # Determine the indentation level
            indentation = INDENTATION_PATTERN.match(line).group(1)

            # If we're in a class and the indentation is greater than the class indentation,
            # this is a method of the class
            if in_class and len(indentation) > len(current_class_indent):
                # For class methods, the full name includes the class name
                full_test_name = f"{current_class}::{test_name}"
            else:
                # For standalone functions, just use the function name
                full_test_name = test_name
                in_class = False  # Reset in_class if we're back to the module level

            # Store markers for this test
            if current_markers:
                existing_markers[full_test_name] = current_markers.copy()

            # Find the end of the function
            # This is a simple heuristic: we look for the next line with the same or less indentation
            # that's not empty or a comment
            start_line = i
            end_line = i
            for j in range(i + 1, len(lines)):
                line_indent = INDENTATION_PATTERN.match(lines[j]).group(1)
                if (
                    lines[j].strip()
                    and len(line_indent) <= len(indentation)
                    and not lines[j].strip().startswith("#")
                ):
                    end_line = j - 1
                    break
                end_line = j

            test_function_ranges.append((start_line, end_line, indentation))
            current_markers = []

    return existing_markers, test_line_numbers, class_line_numbers, test_function_ranges


def standardize_markers_in_file(
    file_path: Path, dry_run: bool = False, verbose: bool = False
) -> tuple[int, bool]:
    """
    Standardize marker placement in a test file.

    Args:
        file_path: Path to the test file
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show verbose output

    Returns:
        Tuple containing the number of standardized markers and whether the file was modified
    """
    standardized = 0
    file_modified = False

    # Analyze the file
    existing_markers, test_line_numbers, class_line_numbers, test_function_ranges = (
        analyze_test_file(file_path)
    )

    if not test_line_numbers:
        return standardized, file_modified

    with open(file_path) as f:
        lines = f.readlines()

    # First pass: remove all existing markers
    markers_to_remove = []
    for i, line in enumerate(lines):
        if MARKER_PATTERN.search(line):
            markers_to_remove.append(i)

    # Remove markers from bottom to top to avoid index shifting
    for i in sorted(markers_to_remove, reverse=True):
        if dry_run:
            if verbose:
                print(f"Would remove from {file_path}:{i+1} - {lines[i].strip()}")
        else:
            if verbose:
                print(f"Removed from {file_path}:{i+1} - {lines[i].strip()}")
            lines.pop(i)
            file_modified = True

    # If we removed any markers, we need to reanalyze the file
    if markers_to_remove:
        # Adjust test line numbers based on removed markers
        new_test_line_numbers = {}
        for line_num, test_name in test_line_numbers.items():
            # Calculate how many markers were removed before this line
            removed_before = sum(1 for i in markers_to_remove if i < line_num)
            new_test_line_numbers[line_num - removed_before] = test_name
        test_line_numbers = new_test_line_numbers

        # Adjust class line numbers based on removed markers
        new_class_line_numbers = {}
        for line_num, class_name in class_line_numbers.items():
            # Calculate how many markers were removed before this line
            removed_before = sum(1 for i in markers_to_remove if i < line_num)
            new_class_line_numbers[line_num - removed_before] = class_name
        class_line_numbers = new_class_line_numbers

        # Adjust test function ranges based on removed markers
        new_test_function_ranges = []
        for start_line, end_line, indentation in test_function_ranges:
            # Calculate how many markers were removed before the start and end lines
            removed_before_start = sum(1 for i in markers_to_remove if i < start_line)
            removed_before_end = sum(1 for i in markers_to_remove if i < end_line)
            new_test_function_ranges.append(
                (
                    start_line - removed_before_start,
                    end_line - removed_before_end,
                    indentation,
                )
            )
        test_function_ranges = new_test_function_ranges

    # Second pass: add markers in the standardized location (directly above the test function)
    # Process in reverse order to avoid index shifting
    for line_num, test_name in sorted(test_line_numbers.items(), reverse=True):
        # Find the class this test belongs to, if any
        test_class = None
        for class_line, class_name in class_line_numbers.items():
            if class_line < line_num:
                test_class = class_name
                break

        # Determine the full test name
        if test_class:
            full_test_name = f"{test_class}::{test_name}"
        else:
            full_test_name = test_name

        # Find the indentation for this test
        indentation = ""
        for start_line, _, indent in test_function_ranges:
            if start_line == line_num:
                indentation = indent
                break

        # Check if this test had markers
        if full_test_name in existing_markers:
            for marker in existing_markers[full_test_name]:
                marker_line = f"{indentation}@pytest.mark.{marker}\n"
                lines.insert(line_num, marker_line)

                if dry_run:
                    if verbose:
                        print(
                            f"Would add to {file_path}:{line_num+1} - {marker_line.strip()}"
                        )
                else:
                    if verbose:
                        print(
                            f"Added to {file_path}:{line_num+1} - {marker_line.strip()}"
                        )
                standardized += 1
                file_modified = True

    # Write changes back to the file
    if not dry_run and file_modified:
        with open(file_path, "w") as f:
            f.writelines(lines)

    return standardized, file_modified


def main():
    """Main function."""
    args = parse_args()

    # Determine the directories to analyze
    if args.category == "all":
        directories = [TEST_CATEGORIES[cat] for cat in TEST_CATEGORIES]
    else:
        directories = [TEST_CATEGORIES[args.category]]

    print(f"Analyzing tests in {', '.join(directories)}...")

    # Find all test files
    test_files = []
    for directory in directories:
        test_files.extend(find_test_files(directory))

    print(f"Found {len(test_files)} test files.")

    # Standardize markers in each file
    total_standardized = 0
    modified_files = []

    for file_path in test_files:
        standardized, file_modified = standardize_markers_in_file(
            file_path, args.dry_run, args.verbose
        )
        total_standardized += standardized

        if file_modified and not args.dry_run:
            modified_files.append(str(file_path))

    action = "Would standardize" if args.dry_run else "Standardized"
    print(f"\n{action} {total_standardized} markers in {len(modified_files)} files")

    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
    else:
        print(f"\n{len(modified_files)} files have been updated.")

        # Invalidate cache for modified files
        if not args.no_cache_update and modified_files:
            print("\nInvalidating cache for modified files...")
            try:
                invalidate_cache_for_files(modified_files, args.verbose)
                print(f"Cache invalidated for {len(modified_files)} files")

                # Also clear the entire cache to ensure consistency
                clear_cache()
                print("Full cache cleared to ensure consistency")
            except Exception as e:
                print(f"Error invalidating cache: {e}")
                print(
                    "You may need to manually clear the cache with: python -m pytest --cache-clear"
                )


if __name__ == "__main__":
    main()
