#!/usr/bin/env python
"""
BDD Marker Counter

This script counts the markers in behavior test step definition files.
It complements the common_test_collector.py script by providing accurate
marker counts for behavior tests.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector for cache handling
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_test_collector

# Constants
BDD_STEP_DIR = "tests/behavior/steps"
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
BDD_DECORATOR_PATTERN = re.compile(r"@(given|when|then|scenario|scenarios)")


def find_bdd_step_files(test_dir: str = BDD_STEP_DIR) -> list[str]:
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


def count_markers_in_file(file_path: str) -> dict[str, int]:
    """
    Count markers in a BDD step definition file.

    Args:
        file_path: Path to the step definition file

    Returns:
        Dictionary mapping marker types to counts
    """
    marker_counts = {"fast": 0, "medium": 0, "slow": 0, "isolation": 0}

    if not os.path.exists(file_path):
        return marker_counts

    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return marker_counts

    # Find all markers
    for marker_match in MARKER_PATTERN.finditer(content):
        marker_type = marker_match.group(1)
        marker_counts[marker_type] += 1

    return marker_counts


def count_all_bdd_markers(test_dir: str = BDD_STEP_DIR) -> dict[str, int]:
    """
    Count all markers in BDD step definition files.

    Args:
        test_dir: Directory containing BDD step definitions

    Returns:
        Dictionary mapping marker types to counts
    """
    total_counts = {
        "fast": 0,
        "medium": 0,
        "slow": 0,
        "isolation": 0,
        "total_files": 0,
        "files_with_markers": 0,
    }

    step_files = find_bdd_step_files(test_dir)
    total_counts["total_files"] = len(step_files)

    for file_path in step_files:
        file_counts = count_markers_in_file(file_path)

        for marker_type, count in file_counts.items():
            total_counts[marker_type] += count

        if sum(file_counts.values()) > 0:
            total_counts["files_with_markers"] += 1

    return total_counts


def update_task_progress(bdd_counts: dict[str, int]) -> None:
    """
    Update the project status file with the latest BDD marker counts.

    Args:
        bdd_counts: Dictionary mapping marker types to counts
    """
    # Get marker counts from common_test_collector
    common_counts = common_test_collector.get_marker_counts(use_cache=False)

    # Calculate total markers
    total_markers = (
        common_counts["total"]["fast"]
        + common_counts["total"]["medium"]
        + common_counts["total"]["slow"]
        + bdd_counts["fast"]
        + bdd_counts["medium"]
        + bdd_counts["slow"]
    )

    # Get total test count
    total_tests = common_test_collector.get_test_counts(use_cache=False)["total"]

    # Calculate percentage
    percentage = (total_markers / total_tests) * 100 if total_tests > 0 else 0

    # Read the project status file
    task_progress_path = "docs/implementation/project_status.md"
    if not os.path.exists(task_progress_path):
        print(f"Error: {task_progress_path} not found")
        return

    with open(task_progress_path) as f:
        lines = f.readlines()

    # Find all lines with test categorization information and update them
    updated = False
    for i, line in enumerate(lines):
        if (
            "tests now have markers" in line
            or "out of" in line
            and "tests" in line
            and "%" in line
        ) or ("Improved from" in line and "tests" in line and "%" in line):
            # Update the line with the latest counts
            lines[i] = (
                f"  - Improved from 124 to {total_markers} out of {total_tests} tests ({percentage:.2f}%) with speed markers\n"
            )
            updated = True

    # Write the updated file
    with open(task_progress_path, "w") as f:
        f.writelines(lines)

    if updated:
        print(f"Updated {task_progress_path} with latest marker counts")
    else:
        print(f"Warning: No marker count information found in {task_progress_path}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Count markers in BDD step definition files"
    )
    parser.add_argument(
        "--update-progress",
        action="store_true",
        help="Update project status file with the latest counts",
    )
    parser.add_argument(
        "--dir", default=BDD_STEP_DIR, help="Directory containing BDD step definitions"
    )

    args = parser.parse_args()

    bdd_counts = count_all_bdd_markers(args.dir)

    print("BDD Marker Counts:")
    print(f"  Fast: {bdd_counts['fast']}")
    print(f"  Medium: {bdd_counts['medium']}")
    print(f"  Slow: {bdd_counts['slow']}")
    print(f"  Isolation: {bdd_counts['isolation']}")
    print(
        f"  Total: {sum(bdd_counts[m] for m in ['fast', 'medium', 'slow', 'isolation'])}"
    )
    print(
        f"  Files with markers: {bdd_counts['files_with_markers']} out of {bdd_counts['total_files']}"
    )

    # Get marker counts from common_test_collector
    common_counts = common_test_collector.get_marker_counts(use_cache=False)

    print("\nCombined Marker Counts:")
    print(f"  Fast: {common_counts['total']['fast'] + bdd_counts['fast']}")
    print(f"  Medium: {common_counts['total']['medium'] + bdd_counts['medium']}")
    print(f"  Slow: {common_counts['total']['slow'] + bdd_counts['slow']}")
    print(
        f"  Total: {sum(common_counts['total'][m] for m in ['fast', 'medium', 'slow']) + sum(bdd_counts[m] for m in ['fast', 'medium', 'slow'])}"
    )

    if args.update_progress:
        update_task_progress(bdd_counts)


if __name__ == "__main__":
    main()
