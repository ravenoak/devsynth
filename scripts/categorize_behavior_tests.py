#!/usr/bin/env python
"""
Script for categorizing behavior tests by speed.

This script is specifically designed to categorize behavior tests by speed,
taking into account their unique structure and execution patterns. It builds
on the existing test categorization infrastructure but is tailored for behavior tests.

Usage:
    python scripts/categorize_behavior_tests.py [options]

Options:
    --batch-size N        Number of tests to run in each batch (default: 20)
    --max-tests N         Maximum number of tests to analyze in this run (default: 100)
    --fast-threshold N    Threshold for fast tests in seconds (default: 1.0)
    --medium-threshold N  Threshold for medium tests in seconds (default: 5.0)
    --dry-run             Show changes without modifying files
    --update              Update test files with appropriate markers
    --timeout N           Timeout for each test in seconds (default: 60)
    --feature FILE        Specific feature file to analyze
    --step-file FILE      Specific step definition file to analyze
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import test_utils

# Thresholds for categorizing tests (in seconds)
FAST_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 5.0

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")
SCENARIO_PATTERN = re.compile(r'@scenario\([\'"](.+?)[\'"],\s*[\'"](.+?)[\'"]\)')
SCENARIOS_PATTERN = re.compile(r'scenarios\([\'"](.+?)[\'"]\)')

# Cache directory for test timing data
CACHE_DIR = ".test_timing_cache"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Categorize behavior tests by speed.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of tests to run in each batch (default: 20)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=100,
        help="Maximum number of tests to analyze in this run (default: 100)",
    )
    parser.add_argument(
        "--fast-threshold",
        type=float,
        default=1.0,
        help="Threshold for fast tests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--medium-threshold",
        type=float,
        default=5.0,
        help="Threshold for medium tests in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update test files with appropriate markers",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for each test in seconds (default: 60)",
    )
    parser.add_argument("--feature", help="Specific feature file to analyze")
    parser.add_argument("--step-file", help="Specific step definition file to analyze")
    return parser.parse_args()


def find_behavior_test_files() -> dict[str, Path]:
    """Find all behavior test files."""
    test_files = {}
    for root, _, files in os.walk("tests/behavior"):
        for file in files:
            if (
                file.startswith("test_")
                and file.endswith(".py")
                and not root.endswith("steps")
            ):
                path = Path(os.path.join(root, file))
                test_files[file] = path
    return test_files


def find_feature_files() -> dict[str, Path]:
    """Find all feature files."""
    feature_files = {}
    for root, _, files in os.walk("tests/behavior/features"):
        for file in files:
            if file.endswith(".feature"):
                path = Path(os.path.join(root, file))
                feature_files[file] = path
    return feature_files


def find_step_files() -> dict[str, Path]:
    """Find all step definition files."""
    step_files = {}
    for root, _, files in os.walk("tests/behavior/steps"):
        for file in files:
            if file.endswith("_steps.py"):
                path = Path(os.path.join(root, file))
                step_files[file] = path
    return step_files


def collect_behavior_tests() -> list[str]:
    """Collect all behavior tests."""
    print("Collecting behavior tests...")

    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check if we have a cached collection
    cache_file = os.path.join(CACHE_DIR, "behavior_tests.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached_data = json.load(f)

            # Use cache if it's less than 1 hour old
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                print(f"Using cached behavior test collection (less than 1 hour old)")
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and collect tests
            pass

    # Collect tests using pytest
    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/behavior/",
        "--collect-only",
        "-q",
    ]

    try:
        collect_result = subprocess.run(
            collect_cmd, check=False, capture_output=True, text=True
        )
        test_list = []

        # Parse the output to get the list of tests
        for line in collect_result.stdout.split("\n"):
            if line.startswith("tests/behavior/"):
                test_list.append(line.strip())

        if not test_list:
            print(f"No behavior tests found")
            return []

        print(f"Found {len(test_list)} behavior tests")

        # Cache the results
        cache_data = {"timestamp": datetime.now().isoformat(), "tests": test_list}
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def run_test_with_timing(test_path: str, timeout: int = 60) -> tuple[float, bool, bool]:
    """
    Run a single test and measure its execution time.

    Args:
        test_path: Path to the test to run
        timeout: Timeout in seconds

    Returns:
        Tuple of (execution_time, passed, skipped)
    """
    # Check if we have a cached timing
    cache_key = test_path.replace("/", "_").replace(":", "_")
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}_timing.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached_data = json.load(f)

            # Use cache if it's less than 24 hours old
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                return (
                    cached_data["execution_time"],
                    cached_data["passed"],
                    cached_data["skipped"],
                )
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and run test
            pass

    # Run the test and measure execution time
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]

    start_time = time.time()

    try:
        # Set up a timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Test timed out after {timeout} seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Cancel the alarm
        signal.alarm(0)

        end_time = time.time()
        execution_time = end_time - start_time

        # Check if the test passed or was skipped
        passed = result.returncode == 0
        skipped = "SKIPPED" in result.stdout

        # Cache the results
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "passed": passed,
            "skipped": skipped,
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return execution_time, passed, skipped
    except TimeoutError as e:
        print(f"Test timed out: {test_path}")

        # Cache the timeout
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": timeout,
            "passed": False,
            "skipped": False,
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return timeout, False, False
    except Exception as e:
        print(f"Error running test: {e}")
        return 0.0, False, False


def measure_test_times(
    test_list: list[str],
    batch_size: int = 20,
    max_tests: int | None = None,
    timeout: int = 60,
) -> dict[str, dict[str, Any]]:
    """
    Measure execution times for a list of tests.

    Args:
        test_list: List of tests to measure
        batch_size: Number of tests to run in each batch
        max_tests: Maximum number of tests to measure (None for all)
        timeout: Timeout for each test in seconds

    Returns:
        Dictionary mapping test names to timing data
    """
    if not test_list:
        return {}

    # Limit the number of tests if specified
    if max_tests is not None and max_tests > 0:
        test_list = test_list[:max_tests]

    print(
        f"Measuring execution times for {len(test_list)} tests in batches of {batch_size}..."
    )

    test_times = {}

    # Process tests in batches
    for i in range(0, len(test_list), batch_size):
        batch = test_list[i : i + batch_size]
        print(
            f"\nProcessing batch {i//batch_size + 1}/{(len(test_list) + batch_size - 1)//batch_size}..."
        )

        for test_path in batch:
            print(f"Running {test_path}...")
            execution_time, passed, skipped = run_test_with_timing(test_path, timeout)

            test_times[test_path] = {
                "execution_time": execution_time,
                "passed": passed,
                "skipped": skipped,
            }

            # Determine marker based on execution time
            # Assign a speed category even for skipped tests
            if execution_time < FAST_THRESHOLD:
                marker = "fast"
            elif execution_time < MEDIUM_THRESHOLD:
                marker = "medium"
            else:
                marker = "slow"

            test_times[test_path]["marker"] = marker

            print(
                f"  Execution time: {execution_time:.2f}s, Marker: {marker}, Passed: {passed}, Skipped: {skipped}"
            )

    return test_times


def extract_test_info(test_path: str) -> dict[str, Any]:
    """
    Extract information about a behavior test.

    Args:
        test_path: Path to the test

    Returns:
        Dictionary containing test information
    """
    # Parse the test path to extract file and test name
    parts = test_path.split("::")
    file_path = parts[0]
    test_name = parts[-1] if len(parts) > 1 else None

    # Read the file content
    with open(file_path) as f:
        content = f.read()

    # Extract feature file references
    feature_files = []

    # Check for scenarios() function calls
    scenarios_matches = SCENARIOS_PATTERN.findall(content)
    feature_files.extend(scenarios_matches)

    # Check for @scenario decorators
    scenario_matches = SCENARIO_PATTERN.findall(content)
    for _, scenario_name in scenario_matches:
        feature_files.append(scenario_name)

    return {
        "file_path": file_path,
        "test_name": test_name,
        "feature_files": feature_files,
    }


def update_test_file(
    file_path: str, test_markers: dict[str, str], dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Update a test file with appropriate markers.

    Args:
        file_path: Path to the test file
        test_markers: Dictionary mapping test names to markers
        dry_run: Whether to show changes without modifying files

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    with open(file_path) as f:
        lines = f.readlines()

    # Find test functions and their line numbers
    test_lines = {}
    for i, line in enumerate(lines):
        match = FUNCTION_PATTERN.search(line)
        if match:
            test_name = match.group(1)
            test_lines[test_name] = i

    # Find existing markers
    existing_markers = {}
    for test_name, line_num in test_lines.items():
        # Look for markers before the test function
        for i in range(max(0, line_num - 5), line_num):
            match = MARKER_PATTERN.search(lines[i])
            if match:
                if test_name not in existing_markers:
                    existing_markers[test_name] = []
                existing_markers[test_name].append(match.group(1))

    # Update markers
    modified_lines = lines.copy()
    line_offset = 0  # Track line number changes due to insertions

    for test_name, line_num in test_lines.items():
        if test_name in test_markers:
            new_marker = test_markers[test_name]

            # Check if the test already has the correct marker
            if (
                test_name in existing_markers
                and new_marker in existing_markers[test_name]
            ):
                unchanged += 1
                continue

            # Check if we need to update an existing marker or add a new one
            if test_name in existing_markers and any(
                m in ("fast", "medium", "slow") for m in existing_markers[test_name]
            ):
                # Update existing marker
                for i in range(
                    max(0, line_num + line_offset - 5), line_num + line_offset
                ):
                    if (
                        i >= 0
                        and i < len(modified_lines)
                        and any(
                            f"@pytest.mark.{m}" in modified_lines[i]
                            for m in ("fast", "medium", "slow")
                        )
                    ):
                        old_line = modified_lines[i]
                        modified_lines[i] = old_line.replace(
                            f'@pytest.mark.{next(m for m in ("fast", "medium", "slow") if f"@pytest.mark.{m}" in old_line)}',
                            f"@pytest.mark.{new_marker}",
                        )
                        if dry_run:
                            print(
                                f"Would update {file_path}:{i+1} - {old_line.strip()} -> {modified_lines[i].strip()}"
                            )
                        updated += 1
                        break
            else:
                # Add new marker
                indent = re.match(
                    r"(\s*)", modified_lines[line_num + line_offset]
                ).group(1)
                marker_line = f"{indent}@pytest.mark.{new_marker}\n"
                modified_lines.insert(line_num + line_offset, marker_line)
                line_offset += 1

                if dry_run:
                    print(
                        f"Would add to {file_path}:{line_num+1} - {marker_line.strip()}"
                    )
                added += 1

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0):
        with open(file_path, "w") as f:
            f.writelines(modified_lines)

    return added, updated, unchanged


def main():
    """Main function."""
    args = parse_args()

    # Set global thresholds based on command-line arguments
    global FAST_THRESHOLD, MEDIUM_THRESHOLD
    FAST_THRESHOLD = args.fast_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    print(f"Fast threshold: {FAST_THRESHOLD}s, Medium threshold: {MEDIUM_THRESHOLD}s")

    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Collect behavior tests
    if args.feature:
        # Analyze a specific feature file
        feature_path = args.feature
        if not os.path.exists(feature_path):
            print(f"Feature file not found: {feature_path}")
            return 1

        # Find tests that use this feature file
        test_list = []
        for test_path in collect_behavior_tests():
            test_info = extract_test_info(test_path)
            if any(
                os.path.basename(feature_path) == os.path.basename(f)
                for f in test_info["feature_files"]
            ):
                test_list.append(test_path)

        print(f"Found {len(test_list)} tests using feature file {feature_path}")
    elif args.step_file:
        # Analyze a specific step definition file
        step_file = args.step_file
        if not os.path.exists(step_file):
            print(f"Step file not found: {step_file}")
            return 1

        # Find tests that use this step file
        # This is more complex and would require parsing imports or running tests with coverage
        # For now, we'll just collect all behavior tests
        test_list = collect_behavior_tests()
        print(
            f"Analyzing all {len(test_list)} behavior tests (can't determine which ones use {step_file})"
        )
    else:
        # Collect all behavior tests
        test_list = collect_behavior_tests()

    if not test_list:
        print("No behavior tests found to analyze.")
        return 0

    # Measure test execution times
    test_times = measure_test_times(
        test_list, args.batch_size, args.max_tests, args.timeout
    )

    if not test_times:
        print("No test timing data collected.")
        return 0

    # Extract markers for each test
    test_markers = {}
    for test_path, data in test_times.items():
        # Extract the test name from the path
        parts = test_path.split("::")
        if len(parts) > 1:
            test_name = parts[-1]
            test_markers[test_name] = data["marker"]

    # Group tests by file
    tests_by_file = {}
    for test_path in test_times:
        file_path = test_path.split("::")[0]
        if file_path not in tests_by_file:
            tests_by_file[file_path] = []
        tests_by_file[file_path].append(test_path)

    # Update test files if requested
    if args.update or args.dry_run:
        total_added = 0
        total_updated = 0
        total_unchanged = 0

        print(f"\nUpdating {len(tests_by_file)} test files...")

        for file_path, tests in tests_by_file.items():
            file_markers = {}
            for test_path in tests:
                parts = test_path.split("::")
                if len(parts) > 1:
                    test_name = parts[-1]
                    if test_name in test_markers:
                        file_markers[test_name] = test_markers[test_name]

            added, updated, unchanged = update_test_file(
                file_path, file_markers, args.dry_run
            )
            total_added += added
            total_updated += updated
            total_unchanged += unchanged

        action = "Would " if args.dry_run else ""
        print(
            f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
        )

    # Print summary
    print("\nBehavior Test Categorization Summary:")
    fast_count = sum(1 for data in test_times.values() if data["marker"] == "fast")
    medium_count = sum(1 for data in test_times.values() if data["marker"] == "medium")
    slow_count = sum(1 for data in test_times.values() if data["marker"] == "slow")

    print(f"  - Fast tests: {fast_count} ({fast_count/len(test_times)*100:.1f}%)")
    print(f"  - Medium tests: {medium_count} ({medium_count/len(test_times)*100:.1f}%)")
    print(f"  - Slow tests: {slow_count} ({slow_count/len(test_times)*100:.1f}%)")
    print(f"  - Total tests analyzed: {len(test_times)}")

    # Print tips for running tests by speed category
    print("\nTips for running behavior tests by speed category:")
    print(
        "  - Run fast behavior tests: poetry run devsynth run-tests --behavior --fast"
    )
    print(
        "  - Run medium behavior tests: poetry run devsynth run-tests --behavior --medium"
    )
    print(
        "  - Run slow behavior tests: poetry run devsynth run-tests --behavior --slow"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
