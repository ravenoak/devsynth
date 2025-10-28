#!/usr/bin/env python
"""
Utilities for BDD-style test scripts.

This module provides specialized utilities for working with BDD-style tests,
particularly for test collection, marker verification, and marker application.
It's designed to work with pytest-bdd tests that use @given, @when, @then decorators.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import original test_utils and common test collector
from . import common_test_collector, test_utils, test_utils_extended

# Constants
CACHE_DIR = ".test_timing_cache"

# Enhanced patterns for BDD-style tests
BDD_DECORATOR_PATTERN = re.compile(r"@(given|when|then|scenario|scenarios)")
BDD_FUNCTION_PATTERN = re.compile(r"def (\w+)\(")
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")


def find_bdd_step_files(test_dir: str = "tests/behavior/steps") -> list[str]:
    """
    Find all BDD step definition files.

    Args:
        test_dir: Directory containing BDD step definitions

    Returns:
        List of step definition file paths
    """
    step_files = []

    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith(".py") and file.startswith("test_"):
                step_files.append(os.path.join(root, file))

    return step_files


def find_feature_files(test_dir: str = "tests/behavior/features") -> list[str]:
    """
    Find all feature files.

    Args:
        test_dir: Directory containing feature files

    Returns:
        List of feature file paths
    """
    feature_files = []

    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith(".feature"):
                feature_files.append(os.path.join(root, file))

    return feature_files


def extract_bdd_test_info(file_path: str) -> dict[str, Any]:
    """
    Extract information about BDD tests from a step definition file.

    Args:
        file_path: Path to the step definition file

    Returns:
        Dictionary containing test information
    """
    if not os.path.exists(file_path):
        return {"file_path": file_path, "test_functions": [], "feature_files": []}

    with open(file_path) as f:
        content = f.read()

    # Extract test functions
    test_functions = []
    lines = content.split("\n")

    # Track decorators and functions
    current_decorators = []

    for i, line in enumerate(lines):
        # Check for BDD decorators
        if BDD_DECORATOR_PATTERN.search(line):
            current_decorators.append((i, line.strip()))

        # Check for function definitions
        func_match = BDD_FUNCTION_PATTERN.search(line)
        if func_match and current_decorators:
            func_name = func_match.group(1)

            # Check if this is a test function (has BDD decorators)
            if any(
                d[1].startswith("@given")
                or d[1].startswith("@when")
                or d[1].startswith("@then")
                or d[1].startswith("@scenario")
                for d in current_decorators
            ):

                # Check for existing markers
                has_marker = any(
                    MARKER_PATTERN.search(lines[j])
                    for j in range(max(0, i - len(current_decorators) - 3), i)
                )

                test_functions.append(
                    {
                        "name": func_name,
                        "line": i,
                        "decorators": current_decorators,
                        "has_marker": has_marker,
                    }
                )

            current_decorators = []

    # Extract feature files
    feature_files = []
    scenarios_match = re.search(r'scenarios\([\'"](.+?)[\'"]', content)
    if scenarios_match:
        feature_path = scenarios_match.group(1)
        feature_files.append(feature_path)

    scenario_matches = re.finditer(
        r'@scenario\([\'"](.+?)[\'"],\s*[\'"](.+?)[\'"]\)', content
    )
    for match in scenario_matches:
        feature_path = match.group(1)
        if feature_path not in feature_files:
            feature_files.append(feature_path)

    return {
        "file_path": file_path,
        "test_functions": test_functions,
        "feature_files": feature_files,
    }


def update_bdd_test_file(
    file_path: str, marker: str, dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Update a BDD test file with appropriate markers.

    Args:
        file_path: Path to the test file
        marker: Marker to apply (fast, medium, slow)
        dry_run: Whether to show changes without modifying files

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    # Extract test information
    test_info = extract_bdd_test_info(file_path)

    if not test_info["test_functions"]:
        return 0, 0, 0

    with open(file_path) as f:
        lines = f.readlines()

    modified_lines = lines.copy()
    line_offset = 0  # Track line number changes due to insertions

    for func in test_info["test_functions"]:
        # Skip functions that already have the correct marker
        if func["has_marker"]:
            # Check if it's the same marker
            for i in range(max(0, func["line"] - 10), func["line"]):
                if i < len(lines) and f"@pytest.mark.{marker}" in lines[i]:
                    unchanged += 1
                    break
            else:
                # Has a different marker, need to update
                for i in range(
                    max(0, func["line"] + line_offset - 10), func["line"] + line_offset
                ):
                    if i < len(modified_lines) and MARKER_PATTERN.search(
                        modified_lines[i]
                    ):
                        old_line = modified_lines[i]
                        modified_lines[i] = old_line.replace(
                            f"@pytest.mark.{MARKER_PATTERN.search(old_line).group(1)}",
                            f"@pytest.mark.{marker}",
                        )
                        if dry_run:
                            print(
                                f"Would update {file_path}:{i+1} - {old_line.strip()} -> {modified_lines[i].strip()}"
                            )
                        updated += 1
                        break
        else:
            # No marker, add one
            # Find the last decorator line
            if func["decorators"]:
                last_decorator_line = func["decorators"][-1][0]

                # Insert marker after the last decorator
                indent = re.match(
                    r"(\s*)", modified_lines[last_decorator_line + line_offset]
                ).group(1)
                marker_line = f"{indent}@pytest.mark.{marker}\n"
                modified_lines.insert(
                    last_decorator_line + line_offset + 1, marker_line
                )
                line_offset += 1

                if dry_run:
                    print(
                        f"Would add to {file_path}:{last_decorator_line+2} - {marker_line.strip()}"
                    )
                added += 1

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0):
        with open(file_path, "w") as f:
            f.writelines(modified_lines)

    return added, updated, unchanged


def categorize_bdd_tests(
    test_dir: str = "tests/behavior/steps",
    marker: str = "medium",
    dry_run: bool = False,
    max_files: int | None = None,
) -> dict[str, int]:
    """
    Categorize BDD tests with appropriate markers.

    Args:
        test_dir: Directory containing BDD step definitions
        marker: Marker to apply (fast, medium, slow)
        dry_run: Whether to show changes without modifying files
        max_files: Maximum number of files to process

    Returns:
        Dictionary containing counts of added, updated, and unchanged markers
    """
    step_files = find_bdd_step_files(test_dir)

    if max_files:
        step_files = step_files[:max_files]

    total_added = 0
    total_updated = 0
    total_unchanged = 0
    total_files_modified = 0

    print(f"Found {len(step_files)} BDD step files")
    print(f"Applying {marker} marker to BDD tests...")

    for file_path in step_files:
        added, updated, unchanged = update_bdd_test_file(file_path, marker, dry_run)

        total_added += added
        total_updated += updated
        total_unchanged += unchanged

        if added > 0 or updated > 0:
            total_files_modified += 1

        if added > 0 or updated > 0 or unchanged > 0:
            status = "would be modified" if dry_run else "modified"
            print(
                f"{file_path}: {added} added, {updated} updated, {unchanged} unchanged ({status})"
            )

    # Invalidate cache after modifications
    if not dry_run and (total_added > 0 or total_updated > 0):
        try:
            common_test_collector.invalidate_cache_for_files(step_files)
            print("Cache invalidated for modified files")
        except Exception as e:
            print(f"Warning: Failed to invalidate cache: {e}")

    return {
        "added": total_added,
        "updated": total_updated,
        "unchanged": total_unchanged,
        "files_modified": total_files_modified,
        "total_files": len(step_files),
    }


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Utilities for BDD-style tests")
    parser.add_argument(
        "--categorize", action="store_true", help="Categorize BDD tests with markers"
    )
    parser.add_argument(
        "--marker",
        choices=["fast", "medium", "slow"],
        default="medium",
        help="Marker to apply",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to process"
    )
    parser.add_argument(
        "--dir",
        default="tests/behavior/steps",
        help="Directory containing BDD step definitions",
    )

    args = parser.parse_args()

    if args.categorize:
        results = categorize_bdd_tests(
            args.dir, args.marker, args.dry_run, args.max_files
        )

        print("\nSummary:")
        print(f"Total files: {results['total_files']}")
        print(f"Files modified: {results['files_modified']}")
        print(f"Markers added: {results['added']}")
        print(f"Markers updated: {results['updated']}")
        print(f"Markers unchanged: {results['unchanged']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
