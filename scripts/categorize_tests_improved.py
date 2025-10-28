#!/usr/bin/env python
"""
Improved script to analyze test execution times and add appropriate markers.

This script runs tests to measure execution times, then adds appropriate markers
(fast, medium, slow) to tests based on their execution time. It addresses several
issues with the original categorize_tests.py script:

1. Removes the --benchmark-only flag which was causing tests to be skipped
2. Handles skipped tests properly
3. Provides a fallback mechanism for tests that don't support benchmarking
4. Adds more robust error handling and reporting
5. Implements more aggressive caching to avoid re-running tests unnecessarily

Usage:
    python scripts/categorize_tests_improved.py [options]

Options:
    --directory DIR       Directory containing tests to analyze (default: tests)
    --output FILE         Output file for timing report (default: test_timing_report.json)
    --dry-run             Show changes without modifying files
    --update              Update test files with appropriate markers
    --batch-size N        Number of tests to run in each batch (default: 20)
    --skip-benchmarks     Skip running benchmarks (use existing timing report)
    --fast-threshold N    Threshold for fast tests in seconds (default: 1.0)
    --medium-threshold N  Threshold for medium tests in seconds (default: 5.0)
    --category CAT        Only analyze tests in the specified category
    --max-tests N         Maximum number of tests to analyze (default: all)
    --timeout N           Timeout for each test in seconds (default: 30)
"""

import argparse
import datetime
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Thresholds for categorizing tests (in seconds)
FAST_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 5.0

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")

# Cache directory for test timing data
CACHE_DIR = ".test_timing_cache"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze test execution times and add appropriate markers."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="tests",
        help="Directory containing tests to analyze (default: tests)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="test_timing_report.json",
        help="Output file for timing report (default: test_timing_report.json)",
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
        "--batch-size",
        type=int,
        default=20,
        help="Number of tests to run in each batch (default: 20)",
    )
    parser.add_argument(
        "--skip-benchmarks",
        action="store_true",
        help="Skip running benchmarks (use existing timing report)",
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
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="all",
        help="Only analyze tests in the specified category",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=None,
        help="Maximum number of tests to analyze (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for each test in seconds (default: 30)",
    )
    return parser.parse_args()


def collect_tests(directory: str) -> list[str]:
    """
    Collect all tests in the given directory.

    Args:
        directory: Directory containing tests to collect

    Returns:
        List of test paths
    """
    print(f"Collecting tests in {directory}...")

    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check if we have a cached collection
    cache_key = directory.replace("/", "_")
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}_tests.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached_data = json.load(f)

            # Use cache if it's less than 1 hour old
            cache_time = datetime.datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                print(
                    f"Using cached test collection for {directory} (less than 1 hour old)"
                )
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and collect tests
            pass

    # Collect tests using pytest
    collect_cmd = ["python", "-m", "pytest", directory, "--collect-only", "-q"]

    try:
        collect_result = subprocess.run(
            collect_cmd, check=False, capture_output=True, text=True
        )
        test_list = []

        # Parse the output to get the list of tests
        for line in collect_result.stdout.split("\n"):
            if line.startswith(directory):
                test_list.append(line.strip())

        if not test_list:
            print(f"No tests found in {directory}")
            return []

        print(f"Found {len(test_list)} tests")

        # Cache the results
        cache_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tests": test_list,
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def run_test_with_timing(test_path: str, timeout: int = 30) -> tuple[float, bool, bool]:
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
            cache_time = datetime.datetime.fromisoformat(cached_data["timestamp"])
            if (
                datetime.datetime.now() - cache_time
            ).total_seconds() < 86400:  # 24 hours
                return (
                    cached_data["execution_time"],
                    cached_data["passed"],
                    cached_data["skipped"],
                )
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and run test
            pass

    # Run the test and measure execution time
    cmd = ["python", "-m", "pytest", test_path, "-v"]

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
            "timestamp": datetime.datetime.now().isoformat(),
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
            "timestamp": datetime.datetime.now().isoformat(),
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
    timeout: int = 30,
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

            # Extract the test name from the path
            test_name = test_path.split("::")[-1]

            test_times[test_name] = {
                "execution_time": execution_time,
                "passed": passed,
                "skipped": skipped,
            }

            # Determine marker based on execution time
            if skipped:
                marker = "unknown"
            elif execution_time < FAST_THRESHOLD:
                marker = "fast"
            elif execution_time < MEDIUM_THRESHOLD:
                marker = "medium"
            else:
                marker = "slow"

            test_times[test_name]["marker"] = marker

            print(
                f"  Execution time: {execution_time:.2f}s, Marker: {marker}, Passed: {passed}, Skipped: {skipped}"
            )

    return test_times


def find_test_files(directory: str) -> list[Path]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file(file_path: Path) -> tuple[dict[str, list[str]], dict[int, str]]:
    """
    Analyze a test file to extract existing markers and test functions.

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
    for i, line in enumerate(lines):
        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)
            test_line_numbers[i] = test_name
            if current_markers:
                existing_markers[test_name] = current_markers.copy()
            current_markers = []

    return existing_markers, test_line_numbers


def update_test_file(
    file_path: Path, test_markers: dict[str, str], dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Update a test file with appropriate markers.

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    # Analyze the file
    existing_markers, test_line_numbers = analyze_test_file(file_path)

    if not test_line_numbers:
        return added, updated, unchanged

    with open(file_path) as f:
        lines = f.readlines()

    # Process each test function
    for line_num, test_name in test_line_numbers.items():
        if test_name not in test_markers:
            continue

        new_marker = test_markers[test_name]

        # Skip unknown markers (from skipped tests)
        if new_marker == "unknown":
            continue

        # Check if the test already has the correct marker
        if test_name in existing_markers and new_marker in existing_markers[test_name]:
            unchanged += 1
            continue

        # Check if we need to update an existing marker or add a new one
        if test_name in existing_markers and any(
            m in ("fast", "medium", "slow") for m in existing_markers[test_name]
        ):
            # Update existing marker
            for i in range(
                line_num - 5, line_num
            ):  # Look at a few lines before the test
                if (
                    i >= 0
                    and i < len(lines)
                    and any(
                        f"@pytest.mark.{m}" in lines[i]
                        for m in ("fast", "medium", "slow")
                    )
                ):
                    old_line = lines[i]
                    lines[i] = old_line.replace(
                        f'@pytest.mark.{next(m for m in ("fast", "medium", "slow") if f"@pytest.mark.{m}" in old_line)}',
                        f"@pytest.mark.{new_marker}",
                    )
                    if dry_run:
                        print(
                            f"Would update {file_path}:{i+1} - {old_line.strip()} -> {lines[i].strip()}"
                        )
                    updated += 1
                    break
        else:
            # Add new marker
            marker_line = f"@pytest.mark.{new_marker}\n"
            lines.insert(line_num, marker_line)

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


def identify_isolation_candidates(test_times: dict[str, dict[str, Any]]) -> set[str]:
    """
    Identify tests that might need the isolation marker.

    This looks for tests that are slow or have failed.
    """
    isolation_candidates = set()

    for test_name, data in test_times.items():
        # Tests that are slow or have failed might need isolation
        if data["marker"] == "slow" or not data["passed"]:
            isolation_candidates.add(test_name)

    return isolation_candidates


def main():
    """Main function."""
    args = parse_args()

    # Set global thresholds based on command-line arguments
    global FAST_THRESHOLD, MEDIUM_THRESHOLD
    FAST_THRESHOLD = args.fast_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    # Determine the directory to analyze
    directory = args.directory
    if args.category != "all":
        if args.category == "unit":
            directory = "tests/unit"
        elif args.category == "integration":
            directory = "tests/integration"
        elif args.category == "behavior":
            directory = "tests/behavior"

    print(f"Analyzing tests in {directory}...")
    print(f"Fast threshold: {FAST_THRESHOLD}s, Medium threshold: {MEDIUM_THRESHOLD}s")

    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Collect tests
    test_list = collect_tests(directory)

    # Measure test execution times or load from existing report
    if args.skip_benchmarks:
        print("Skipping benchmarks, using existing timing report...")
        try:
            with open(args.output) as f:
                report = json.load(f)
                test_times = report.get("tests", {})
                if not test_times:
                    print(
                        "No test timing data found in report, measuring execution times..."
                    )
                    test_times = measure_test_times(
                        test_list, args.batch_size, args.max_tests, args.timeout
                    )
        except (FileNotFoundError, json.JSONDecodeError):
            print("Timing report not found or invalid, measuring execution times...")
            test_times = measure_test_times(
                test_list, args.batch_size, args.max_tests, args.timeout
            )
    else:
        # Measure test execution times
        start_time = time.time()
        test_times = measure_test_times(
            test_list, args.batch_size, args.max_tests, args.timeout
        )
        end_time = time.time()
        print(f"Measurement completed in {end_time - start_time:.2f} seconds")

    # Extract markers from test times
    test_markers = {
        name: data["marker"]
        for name, data in test_times.items()
        if data["marker"] != "unknown"
    }

    # Save timing report
    with open(args.output, "w") as f:
        json.dump(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "directory": directory,
                "fast_threshold": FAST_THRESHOLD,
                "medium_threshold": MEDIUM_THRESHOLD,
                "test_count": len(test_markers),
                "fast_tests": sum(
                    1 for marker in test_markers.values() if marker == "fast"
                ),
                "medium_tests": sum(
                    1 for marker in test_markers.values() if marker == "medium"
                ),
                "slow_tests": sum(
                    1 for marker in test_markers.values() if marker == "slow"
                ),
                "tests": test_times,
            },
            f,
            indent=2,
        )

    print(f"Timing report saved to {args.output}")
    print(f"Test counts by speed category:")
    print(
        f"  - Fast tests: {sum(1 for marker in test_markers.values() if marker == 'fast')}"
    )
    print(
        f"  - Medium tests: {sum(1 for marker in test_markers.values() if marker == 'medium')}"
    )
    print(
        f"  - Slow tests: {sum(1 for marker in test_markers.values() if marker == 'slow')}"
    )

    # Identify tests that might need isolation
    isolation_candidates = identify_isolation_candidates(test_times)
    if isolation_candidates:
        print("\nTests that might need the isolation marker:")
        for test in isolation_candidates:
            print(f"  - {test}")

    # Update test files if requested
    if args.update or args.dry_run:
        test_files = find_test_files(directory)

        total_added = 0
        total_updated = 0
        total_unchanged = 0

        print(f"\nUpdating {len(test_files)} test files...")

        for i, file_path in enumerate(test_files):
            if i % 10 == 0:
                print(f"Processing file {i+1}/{len(test_files)}...")

            added, updated, unchanged = update_test_file(
                file_path, test_markers, args.dry_run
            )
            total_added += added
            total_updated += updated
            total_unchanged += unchanged

        action = "Would " if args.dry_run else ""
        print(
            f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
        )

    print("\nTest categorization complete")

    # Print tips for running tests by speed category
    print("\nTips for running tests by speed category:")
    print("  - Run fast tests: poetry run devsynth run-tests --fast")
    print("  - Run medium tests: poetry run devsynth run-tests --medium")
    print("  - Run slow tests: poetry run devsynth run-tests --slow")
    print(
        "  - Run fast and medium tests: poetry run devsynth run-tests --fast --medium"
    )


if __name__ == "__main__":
    main()
