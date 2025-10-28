#!/usr/bin/env python
"""
Enhanced utilities for test scripts.

This module extends the functionality in test_utils.py with additional
features for test collection, marker verification, and synchronization
between test categorization tracking files.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import original test_utils and common test collector
# Import original test_utils and common test collector. When the module is
# executed outside a package context, fall back to direct imports.
try:  # pragma: no cover - import resolution
    from . import common_test_collector, test_utils
except ImportError:  # pragma: no cover - script execution
    import pathlib
    import sys

    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    import common_test_collector
    import test_utils

# Constants
PROGRESS_FILE = ".test_categorization_progress.json"
SCHEDULE_FILE = ".test_categorization_schedule.json"
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")
CLASS_PATTERN = re.compile(r"class (Test\w+)\(")

# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}


def load_progress_file(file_path: str = PROGRESS_FILE) -> dict[str, Any]:
    """
    Load the test categorization progress file.

    Args:
        file_path: Path to the progress file

    Returns:
        Dictionary containing categorization progress
    """
    if os.path.exists(file_path):
        try:
            with open(file_path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error loading progress file {file_path}, creating new progress")
            return {
                "timestamp": datetime.now().isoformat(),
                "categorized_tests": {},
                "categorized_files": [],
                "categorization_counts": {
                    "fast": 0,
                    "medium": 0,
                    "slow": 0,
                    "total": 0,
                },
            }
    else:
        print(f"Progress file {file_path} not found, creating new progress")
        return {
            "timestamp": datetime.now().isoformat(),
            "categorized_tests": {},
            "categorized_files": [],
            "categorization_counts": {"fast": 0, "medium": 0, "slow": 0, "total": 0},
        }


def load_schedule_file(file_path: str = SCHEDULE_FILE) -> dict[str, Any]:
    """
    Load the test categorization schedule file.

    Args:
        file_path: Path to the schedule file

    Returns:
        Dictionary containing categorization schedule
    """
    if os.path.exists(file_path):
        try:
            with open(file_path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error loading schedule file {file_path}")
            return {}
    else:
        print(f"Schedule file {file_path} not found")
        return {}


def save_progress_file(
    progress: dict[str, Any], file_path: str = PROGRESS_FILE
) -> None:
    """
    Save the test categorization progress file.

    Args:
        progress: Dictionary containing categorization progress
        file_path: Path to the progress file
    """
    # Update timestamp
    progress["timestamp"] = datetime.now().isoformat()

    with open(file_path, "w") as f:
        json.dump(progress, f, indent=2)

    print(f"Progress saved to {file_path}")


def save_schedule_file(
    schedule: dict[str, Any], file_path: str = SCHEDULE_FILE
) -> None:
    """
    Save the test categorization schedule file.

    Args:
        schedule: Dictionary containing categorization schedule
        file_path: Path to the schedule file
    """
    # Update timestamp
    if "generated_at" not in schedule:
        schedule["generated_at"] = datetime.now().isoformat()

    schedule["updated_at"] = datetime.now().isoformat()

    with open(file_path, "w") as f:
        json.dump(schedule, f, indent=2)

    print(f"Schedule saved to {file_path}")


def collect_behavior_tests(
    test_dir: str = "tests/behavior", use_cache: bool = True
) -> list[str]:
    """
    Collect behavior tests using a specialized approach.

    Args:
        test_dir: Directory containing behavior tests
        use_cache: Whether to use cached test collection results

    Returns:
        List of behavior test paths
    """
    print(f"Collecting behavior tests in {test_dir}...")

    # Use common_test_collector to collect behavior tests
    return common_test_collector.collect_tests_by_category(
        "behavior", use_cache=use_cache
    )


def collect_all_tests(use_cache: bool = True) -> dict[str, list[str]]:
    """
    Collect all tests in the project, organized by category.

    Args:
        use_cache: Whether to use cached test collection results

    Returns:
        Dictionary mapping test categories to lists of test paths
    """
    all_tests = {}

    # Collect tests for each category using common_test_collector
    for category in common_test_collector.TEST_CATEGORIES:
        all_tests[category] = common_test_collector.collect_tests_by_category(
            category, use_cache=use_cache
        )

    return all_tests


def check_test_has_marker(
    test_path: str, marker_type: str | None = None
) -> tuple[bool, str | None]:
    """
    Check if a test has a speed marker without running pytest.

    Args:
        test_path: Path to the test
        marker_type: Specific marker type to check for (fast, medium, slow, isolation)

    Returns:
        Tuple of (has_marker, marker_type)
    """
    # Use common_test_collector to check for markers
    if marker_type:
        # Check for a specific marker type
        has_marker, found_marker = common_test_collector.check_test_has_marker(
            test_path, [marker_type]
        )
        return has_marker, found_marker
    else:
        # Check for any speed marker
        return common_test_collector.check_test_has_marker(
            test_path, ["fast", "medium", "slow", "isolation"]
        )


def get_test_markers_from_file(file_path: str) -> dict[str, str]:
    """
    Extract all test markers from a file.

    Args:
        file_path: Path to the test file

    Returns:
        Dictionary mapping test names to marker types
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        return {}

    # Read the file content
    with open(file_path) as f:
        lines = f.readlines()

    markers = {}
    current_markers = []

    for i, line in enumerate(lines):
        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)
            if current_markers:
                # Use the last marker if there are multiple
                markers[test_name] = current_markers[-1]
            current_markers = []

    return markers


def count_categorized_tests_accurately(
    module_path: str,
) -> tuple[int, int, dict[str, int]]:
    """
    Count the number of tests in a module that have speed markers, using a more accurate approach.

    Args:
        module_path: Path to the test module

    Returns:
        Tuple of (total_tests, categorized_tests, marker_counts)
    """
    # Find the category for this module
    category = None
    for cat, path in common_test_collector.TEST_CATEGORIES.items():
        if module_path.startswith(path):
            category = cat
            break

    if not category:
        return 0, 0, {"fast": 0, "medium": 0, "slow": 0}

    # Collect all tests in the category using common_test_collector
    all_tests = common_test_collector.collect_tests_by_category(category)

    # Filter tests that belong to this module
    module_tests = [test for test in all_tests if test.startswith(module_path)]
    total_tests = len(module_tests)

    # Count tests with speed markers
    categorized_count = 0
    marker_counts = {"fast": 0, "medium": 0, "slow": 0}

    # Get tests with markers using common_test_collector
    tests_with_markers = common_test_collector.get_tests_with_markers(
        ["fast", "medium", "slow"]
    )

    # Load progress file for more accurate tracking
    progress = load_progress_file()
    categorized_tests = progress.get("categorized_tests", {})

    for test_path in module_tests:
        # First check if the test is in the progress file
        if test_path in categorized_tests:
            marker = categorized_tests[test_path]
            categorized_count += 1
            if marker in marker_counts:
                marker_counts[marker] += 1
            continue

        # If not in progress file, check if it's in the tests_with_markers
        for marker_type in ["fast", "medium", "slow"]:
            if (
                category in tests_with_markers
                and test_path in tests_with_markers[category][marker_type]
            ):
                categorized_count += 1
                marker_counts[marker_type] += 1
                break

    return total_tests, categorized_count, marker_counts


def synchronize_test_categorization() -> dict[str, Any]:
    """
    Synchronize the test categorization tracking between progress file and schedule file.

    Returns:
        Dictionary containing synchronization results
    """
    print("Synchronizing test categorization tracking...")

    # Load progress and schedule files
    progress = load_progress_file()
    schedule = load_schedule_file()

    if not progress or not schedule:
        print("Cannot synchronize: missing progress or schedule file")
        return {"success": False, "error": "Missing progress or schedule file"}

    # Extract categorized tests from progress file
    progress_categorized = progress.get("categorized_tests", {})
    progress_counts = progress.get(
        "categorization_counts", {"fast": 0, "medium": 0, "slow": 0, "total": 0}
    )

    # Extract module test counts from schedule file
    schedule_module_counts = schedule.get("module_test_counts", {})

    # Collect all tests by module using common_test_collector
    all_tests_by_module = {}
    for category in common_test_collector.TEST_CATEGORIES:
        category_tests = common_test_collector.collect_tests_by_category(category)

        for test_path in category_tests:
            # Extract the module path from the test path
            if "::" in test_path:
                module_path = test_path.split("::")[0]
                # Get the directory containing the file
                module_path = os.path.dirname(module_path)
            else:
                module_path = os.path.dirname(test_path)

            if module_path not in all_tests_by_module:
                all_tests_by_module[module_path] = []
            all_tests_by_module[module_path].append(test_path)

    # Update module test counts in schedule file
    for module_path, tests in all_tests_by_module.items():
        total_tests = len(tests)
        categorized_count = sum(1 for test in tests if test in progress_categorized)
        uncategorized_count = total_tests - categorized_count

        if module_path in schedule_module_counts:
            schedule_module_counts[module_path] = {
                "total": total_tests,
                "categorized": categorized_count,
                "uncategorized": uncategorized_count,
            }
        elif uncategorized_count > 0:
            # Add new module to schedule
            schedule_module_counts[module_path] = {
                "total": total_tests,
                "categorized": categorized_count,
                "uncategorized": uncategorized_count,
            }

    # Update total counts in schedule file
    total_tests = sum(len(tests) for tests in all_tests_by_module.values())
    total_categorized = len(progress_categorized)
    total_uncategorized = total_tests - total_categorized

    schedule["total_tests"] = total_tests
    schedule["total_categorized"] = total_categorized
    schedule["total_uncategorized"] = total_uncategorized
    schedule["module_test_counts"] = schedule_module_counts

    # Save updated schedule file
    save_schedule_file(schedule)

    # Verify progress file counts
    actual_fast = sum(1 for marker in progress_categorized.values() if marker == "fast")
    actual_medium = sum(
        1 for marker in progress_categorized.values() if marker == "medium"
    )
    actual_slow = sum(1 for marker in progress_categorized.values() if marker == "slow")
    actual_total = len(progress_categorized)

    # Update progress file counts if needed
    if (
        actual_fast != progress_counts.get("fast", 0)
        or actual_medium != progress_counts.get("medium", 0)
        or actual_slow != progress_counts.get("slow", 0)
        or actual_total != progress_counts.get("total", 0)
    ):

        progress["categorization_counts"] = {
            "fast": actual_fast,
            "medium": actual_medium,
            "slow": actual_slow,
            "total": actual_total,
        }

        # Save updated progress file
        save_progress_file(progress)

    return {
        "success": True,
        "total_tests": total_tests,
        "total_categorized": total_categorized,
        "total_uncategorized": total_uncategorized,
        "fast_tests": actual_fast,
        "medium_tests": actual_medium,
        "slow_tests": actual_slow,
    }


def verify_test_markers(test_dir: str = "tests") -> dict[str, Any]:
    """
    Verify that test markers are correctly applied and recognized by pytest.

    Args:
        test_dir: Directory containing tests to verify

    Returns:
        Dictionary containing verification results
    """
    print(f"Verifying test markers in {test_dir}...")

    # Use common_test_collector to collect all tests
    all_tests = []
    for category in common_test_collector.TEST_CATEGORIES:
        if common_test_collector.TEST_CATEGORIES[category].startswith(test_dir):
            all_tests.extend(common_test_collector.collect_tests_by_category(category))

    # Get tests with markers using common_test_collector
    tests_with_markers = common_test_collector.get_tests_with_markers(
        ["fast", "medium", "slow", "isolation"]
    )

    # Get marker counts using common_test_collector
    marker_counts = common_test_collector.get_marker_counts()

    # Collect all test files for file-level analysis
    test_files = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    # Initialize results
    results = {
        "total_files": len(test_files),
        "files_with_markers": 0,
        "total_tests": len(all_tests),
        "tests_with_markers": sum(
            sum(len(tests) for tests in markers.values())
            for markers in tests_with_markers.values()
        ),
        "marker_counts": {
            "fast": marker_counts["total"]["fast"],
            "medium": marker_counts["total"]["medium"],
            "slow": marker_counts["total"]["slow"],
            "isolation": 0,  # Not tracked in marker_counts
        },
        "files_with_issues": [],
    }

    # Analyze files for issues
    for file_path in test_files:
        # Count tests in the file
        with open(file_path) as f:
            content = f.read()

        test_matches = FUNCTION_PATTERN.findall(content)
        file_test_count = len(test_matches)

        # Check if file has any markers
        has_markers = False
        file_tests_with_markers = 0

        # Count tests with markers in this file
        for category in tests_with_markers:
            for marker_type in tests_with_markers[category]:
                for test_path in tests_with_markers[category][marker_type]:
                    if test_path.startswith(file_path):
                        has_markers = True
                        file_tests_with_markers += 1

        if has_markers:
            results["files_with_markers"] += 1

        # Check for issues
        if file_test_count > 0 and file_tests_with_markers < file_test_count:
            results["files_with_issues"].append(
                {
                    "file": file_path,
                    "total_tests": file_test_count,
                    "tests_with_markers": file_tests_with_markers,
                    "missing_markers": file_test_count - file_tests_with_markers,
                }
            )

    # Verify markers are recognized by pytest
    for marker_type in ["fast", "medium", "slow"]:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_dir,
            f"-m={marker_type}",
            "--collect-only",
            "-q",
        ]

        try:
            collect_result = subprocess.run(
                cmd, check=False, capture_output=True, text=True
            )

            # Count tests collected with this marker
            test_count = 0
            for line in collect_result.stdout.split("\n"):
                if line.startswith(test_dir):
                    test_count += 1

            # Compare with our count
            if test_count != results["marker_counts"][marker_type]:
                print(
                    f"Warning: {marker_type} marker count mismatch - {test_count} tests collected by pytest, {results['marker_counts'][marker_type]} found in files"
                )
                results[f"{marker_type}_marker_mismatch"] = {
                    "pytest_count": test_count,
                    "file_count": results["marker_counts"][marker_type],
                }
        except Exception as e:
            print(f"Error verifying {marker_type} markers: {e}")

    return results


if __name__ == "__main__":
    # Example usage
    parser = argparse.ArgumentParser(description="Enhanced utilities for test scripts.")
    parser.add_argument(
        "--sync", action="store_true", help="Synchronize test categorization tracking"
    )
    parser.add_argument("--verify", action="store_true", help="Verify test markers")
    parser.add_argument(
        "--test-dir", default="tests", help="Directory containing tests to verify"
    )

    args = parser.parse_args()

    if args.sync:
        results = synchronize_test_categorization()
        print(f"Synchronization {'successful' if results['success'] else 'failed'}")
        if results["success"]:
            print(f"Total tests: {results['total_tests']}")
            print(
                f"Categorized: {results['total_categorized']} ({results['total_categorized']/results['total_tests']*100:.1f}%)"
            )
            print(
                f"Uncategorized: {results['total_uncategorized']} ({results['total_uncategorized']/results['total_tests']*100:.1f}%)"
            )
            print(f"Fast tests: {results['fast_tests']}")
            print(f"Medium tests: {results['medium_tests']}")
            print(f"Slow tests: {results['slow_tests']}")

    if args.verify:
        results = verify_test_markers(args.test_dir)
        print(f"Verification results:")
        print(f"Total files: {results['total_files']}")
        print(
            f"Files with markers: {results['files_with_markers']} ({results['files_with_markers']/results['total_files']*100:.1f}%)"
        )
        print(f"Total tests: {results['total_tests']}")
        print(
            f"Tests with markers: {results['tests_with_markers']} ({results['tests_with_markers']/results['total_tests']*100:.1f}%)"
        )
        print(f"Fast tests: {results['marker_counts']['fast']}")
        print(f"Medium tests: {results['marker_counts']['medium']}")
        print(f"Slow tests: {results['marker_counts']['slow']}")
        print(f"Isolation tests: {results['marker_counts']['isolation']}")
        print(f"Files with missing markers: {len(results['files_with_issues'])}")
