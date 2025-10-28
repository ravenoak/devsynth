#!/usr/bin/env python
"""
Script for incremental test categorization.

This script categorizes tests by speed in smaller batches over time, rather than
trying to categorize all tests at once. It builds on the categorize_tests_improved.py
script but adds support for:

1. Categorizing tests in specific directories or modules
2. Limiting the number of tests categorized in a single run
3. Prioritizing uncategorized tests
4. Tracking progress across multiple runs

Usage:
    python scripts/incremental_test_categorization.py [options]

Options:
    --directory DIR       Directory containing tests to analyze (default: tests)
    --module MODULE       Specific module to analyze (e.g., tests/unit/interface)
    --batch-size N        Number of tests to run in each batch (default: 20)
    --max-tests N         Maximum number of tests to analyze in this run (default: 100)
    --fast-threshold N    Threshold for fast tests in seconds (default: 1.0)
    --medium-threshold N  Threshold for medium tests in seconds (default: 5.0)
    --dry-run             Show changes without modifying files
    --update              Update test files with appropriate markers
    --progress-file FILE  File to track categorization progress (default: .test_categorization_progress.json)
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
CLASS_PATTERN = re.compile(r"class\s+(Test\w+)\s*\(")

# Cache directory for test timing data
CACHE_DIR = ".test_timing_cache"

# Default progress file
DEFAULT_PROGRESS_FILE = ".test_categorization_progress.json"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Categorize tests by speed incrementally."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="tests",
        help="Directory containing tests to analyze (default: tests)",
    )
    parser.add_argument(
        "-m", "--module", help="Specific module to analyze (e.g., tests/unit/interface)"
    )
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
        "--force",
        action="store_true",
        help="Force recategorization of tests, even if they have already been categorized",
    )
    parser.add_argument(
        "--progress-file",
        default=DEFAULT_PROGRESS_FILE,
        help=f"File to track categorization progress (default: {DEFAULT_PROGRESS_FILE})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for each test in seconds (default: 30)",
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
            print(f"Error loading progress file {progress_file}, creating new progress")
            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "categorized_tests": {},
                "categorized_files": set(),
                "categorization_counts": {
                    "fast": 0,
                    "medium": 0,
                    "slow": 0,
                    "total": 0,
                },
            }
    else:
        print(f"Progress file {progress_file} not found, creating new progress")
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "categorized_tests": {},
            "categorized_files": [],
            "categorization_counts": {"fast": 0, "medium": 0, "slow": 0, "total": 0},
        }


def save_progress(progress: dict[str, Any], progress_file: str):
    """
    Save categorization progress to file.

    Args:
        progress: Dictionary containing categorization progress
        progress_file: Path to the progress file
    """
    # Update timestamp
    progress["timestamp"] = datetime.datetime.now().isoformat()

    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


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


def find_test_files(directory: str) -> list[Path]:
    """
    Find all test files in the given directory or return the file if directory is a file path.

    Args:
        directory: Directory or file path to search

    Returns:
        List of test file paths
    """
    print(f"DEBUG: Finding test files in {directory}")

    # Check if directory is actually a file path
    if os.path.isfile(directory):
        if directory.endswith(".py") and os.path.basename(directory).startswith(
            "test_"
        ):
            file_path = Path(directory)
            print(f"DEBUG: Found test file (direct): {file_path}")
            return [file_path]
        else:
            print(f"DEBUG: {directory} is a file but not a test file")
            return []

    # If it's a directory, search for test files
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = Path(os.path.join(root, file))
                test_files.append(file_path)
                print(f"DEBUG: Found test file: {file_path}")

    print(f"DEBUG: Found {len(test_files)} test files")
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
    test_markers: dict[str, str],
    dry_run: bool = False,
    verbose: bool = True,
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

    if verbose:
        print(f"\nDEBUG: Analyzing file {file_path}")
        print(f"DEBUG: Found {len(test_line_numbers)} test functions/methods")
        for line_num, test_name in test_line_numbers.items():
            print(f"DEBUG: Line {line_num}: {test_name}")
        print(f"DEBUG: Test markers dictionary has {len(test_markers)} entries")
        print(
            f"DEBUG: First 5 entries in test_markers: {list(test_markers.items())[:5]}"
        )

    if not test_line_numbers:
        if verbose:
            print("DEBUG: No test functions/methods found in file")
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

        if dry_run:
            print(f"Would add to {file_path}:{last_import_line+2} - import pytest")

    # Process each test function
    modified_lines = []  # Track which lines we've modified to avoid duplicate changes

    for line_num, test_name in sorted(test_line_numbers.items()):
        if verbose:
            print(f"\nDEBUG: Processing test {test_name} at line {line_num}")

        # Extract the base test name (without class prefix)
        if "::" in test_name:
            class_name, base_test_name = test_name.split("::")
            if verbose:
                print(
                    f"DEBUG: Class-based test: class={class_name}, method={base_test_name}"
                )
        else:
            class_name = None
            base_test_name = test_name
            if verbose:
                print(f"DEBUG: Function-based test: {base_test_name}")

        # Check if the test name is directly in the markers dictionary
        if test_name in test_markers:
            new_marker = test_markers[test_name]
            if verbose:
                print(f"DEBUG: Direct match found for {test_name}: {new_marker}")
        elif base_test_name in test_markers:
            # Try with just the base test name (without class prefix)
            new_marker = test_markers[base_test_name]
            if verbose:
                print(
                    f"DEBUG: Base name match found for {base_test_name}: {new_marker}"
                )
        else:
            # Try to find a matching test path in the markers dictionary
            # This handles cases where the same test name appears in multiple files
            file_name = file_path.name
            if verbose:
                print(
                    f"DEBUG: No direct match, trying patterns with file_name={file_name}"
                )

            # Try different patterns for matching
            patterns = [
                f"{file_name}::{test_name}",  # Full path with class prefix
                f"{file_name}::{base_test_name}",  # Path with base test name
                (
                    f"{file_name}::{class_name}::{base_test_name}"
                    if class_name
                    else None
                ),  # Path with explicit class
            ]
            patterns = [p for p in patterns if p]

            if verbose:
                print(f"DEBUG: Trying patterns: {patterns}")

            # Look for any matching path
            matching_paths = []
            for pattern in patterns:
                pattern_matches = [
                    path
                    for path in test_markers.keys()
                    if isinstance(path, str) and pattern in path
                ]
                if verbose and pattern_matches:
                    print(f"DEBUG: Pattern {pattern} matched: {pattern_matches}")
                matching_paths.extend(pattern_matches)

            # Also try matching just by test name
            if not matching_paths:
                if verbose:
                    print(f"DEBUG: No pattern matches, trying base name + file name")
                matching_paths = [
                    path
                    for path in test_markers.keys()
                    if isinstance(path, str)
                    and base_test_name in path
                    and file_name in path
                ]
                if verbose and matching_paths:
                    print(f"DEBUG: Base name + file name matched: {matching_paths}")

            if matching_paths:
                # Use the marker from the first matching path
                new_marker = test_markers[matching_paths[0]]
                if verbose:
                    print(f"DEBUG: Using marker from {matching_paths[0]}: {new_marker}")
            else:
                # No matching test found in the markers dictionary
                if verbose:
                    print(f"DEBUG: No match found for {test_name}, skipping")
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
            # First, check if there's a blank line before the function
            # If not, add one for better readability
            if line_num > 0 and not lines[line_num - 1].strip() == "":
                lines.insert(line_num, "\n")
                line_num += 1
                # Update line numbers for subsequent tests
                test_line_numbers = {
                    k + 1 if k >= line_num - 1 else k: v
                    for k, v in test_line_numbers.items()
                }

            # Now add the marker
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


def filter_uncategorized_tests(
    test_list: list[str], progress: dict[str, Any], force: bool = False
) -> list[str]:
    """
    Filter out tests that have already been categorized.

    Args:
        test_list: List of test paths
        progress: Dictionary containing categorization progress
        force: If True, include all tests regardless of categorization status

    Returns:
        List of uncategorized test paths
    """
    if force:
        return test_list

    categorized_tests = progress.get("categorized_tests", {})
    return [test for test in test_list if test not in categorized_tests]


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


def update_progress(
    progress: dict[str, Any], test_times: dict[str, dict[str, Any]], force: bool = False
) -> dict[str, Any]:
    """
    Update categorization progress with new test times.

    Args:
        progress: Dictionary containing categorization progress
        test_times: Dictionary mapping test paths to timing data
        force: If True, update counts for all tests regardless of previous categorization

    Returns:
        Updated progress dictionary
    """
    categorized_tests = progress.get("categorized_tests", {})
    categorization_counts = progress.get(
        "categorization_counts", {"fast": 0, "medium": 0, "slow": 0, "total": 0}
    )

    # If force is True, reset the counts
    if force:
        categorization_counts = {"fast": 0, "medium": 0, "slow": 0, "total": 0}

    # Update categorized tests and counts
    for test_path, data in test_times.items():
        marker = data["marker"]
        old_marker = categorized_tests.get(test_path)
        categorized_tests[test_path] = marker

        # Update counts if this is a new categorization or if force is True
        if force or test_path not in progress.get("categorized_tests", {}):
            categorization_counts["total"] += 1
            categorization_counts[marker] += 1
        # If the marker has changed and old_marker is not None, update the counts
        elif old_marker is not None and old_marker != marker:
            categorization_counts[old_marker] -= 1
            categorization_counts[marker] += 1
        # If old_marker is None but we're updating the marker, increment the count
        elif old_marker is None:
            categorization_counts["total"] += 1
            categorization_counts[marker] += 1

    progress["categorized_tests"] = categorized_tests
    progress["categorization_counts"] = categorization_counts

    return progress


def main():
    """Main function."""
    args = parse_args()

    # Set global thresholds based on command-line arguments
    global FAST_THRESHOLD, MEDIUM_THRESHOLD
    FAST_THRESHOLD = args.fast_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    # Determine the directory to analyze
    directory = args.module if args.module else args.directory

    print(f"Analyzing tests in {directory}...")
    print(f"Fast threshold: {FAST_THRESHOLD}s, Medium threshold: {MEDIUM_THRESHOLD}s")

    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Load progress
    progress = load_progress(args.progress_file)

    # Collect tests
    test_list = collect_tests(directory)

    # Filter out tests that have already been categorized
    uncategorized_tests = filter_uncategorized_tests(test_list, progress, args.force)

    print(
        f"Found {len(uncategorized_tests)} uncategorized tests out of {len(test_list)} total tests"
    )

    if not uncategorized_tests:
        print("No uncategorized tests found.")
        return 0

    # Measure test execution times
    test_times = measure_test_times(
        uncategorized_tests, args.batch_size, args.max_tests, args.timeout
    )

    # Update progress
    progress = update_progress(progress, test_times, args.force)

    # Save progress
    save_progress(progress, args.progress_file)

    print(f"Progress saved to {args.progress_file}")
    print(f"Categorization counts:")
    print(f"  - Fast tests: {progress['categorization_counts']['fast']}")
    print(f"  - Medium tests: {progress['categorization_counts']['medium']}")
    print(f"  - Slow tests: {progress['categorization_counts']['slow']}")
    print(
        f"  - Total categorized: {progress['categorization_counts']['total']} out of {len(test_list)} tests"
    )

    # Extract markers from test times (include all tests, even skipped ones)
    test_markers = {}
    for test_path, data in test_times.items():
        # Extract file path and test name from test path
        if "::" in test_path:
            file_path, *test_parts = test_path.split("::")
            test_name = test_parts[-1]

            # Handle parameterized tests
            if "(" in test_name:
                test_name = test_name.split("(")[0]

            # Add the test name to the markers dictionary
            test_markers[test_name] = data["marker"]

            # Also add the full test path to handle cases where the same test name appears in multiple files
            test_markers[test_path] = data["marker"]
        else:
            # If there's no "::" in the path, just use the filename as the key
            test_markers[os.path.basename(test_path)] = data["marker"]

    # Update test files if requested
    if args.update or args.dry_run:
        test_files = find_test_files(directory)

        total_added = 0
        total_updated = 0
        total_unchanged = 0

        print(f"\nUpdating {len(test_files)} test files...")
        print(f"DEBUG: test_markers dictionary has {len(test_markers)} entries")
        print(
            f"DEBUG: First 5 entries in test_markers: {list(test_markers.items())[:5]}"
        )

        for i, file_path in enumerate(test_files):
            if i % 10 == 0:
                print(f"Processing file {i+1}/{len(test_files)}...")

            print(f"\nDEBUG: Processing file {file_path}")
            added, updated, unchanged = update_test_file(
                file_path, test_markers, args.dry_run, verbose=True
            )
            print(
                f"DEBUG: Results for {file_path}: added={added}, updated={updated}, unchanged={unchanged}"
            )
            total_added += added
            total_updated += updated
            total_unchanged += unchanged

        action = "Would " if args.dry_run else ""
        print(
            f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
        )

    print("\nIncremental test categorization complete")

    # Print tips for running tests by speed category
    print("\nTips for running tests by speed category:")
    print("  - Run fast tests: poetry run devsynth run-tests --fast")
    print("  - Run medium tests: poetry run devsynth run-tests --medium")
    print("  - Run slow tests: poetry run devsynth run-tests --slow")
    print(
        "  - Run fast and medium tests: poetry run devsynth run-tests --fast --medium"
    )

    # Print tips for continuing categorization
    print("\nTo continue categorization:")
    print(
        f"  - Run this script again: python scripts/incremental_test_categorization.py --update"
    )
    print(
        f"  - Categorize a specific module: python scripts/incremental_test_categorization.py --module tests/unit/interface --update"
    )
    print(
        f"  - Adjust batch size: python scripts/incremental_test_categorization.py --batch-size 10 --update"
    )
    print(
        f"  - Adjust max tests: python scripts/incremental_test_categorization.py --max-tests 50 --update"
    )


if __name__ == "__main__":
    main()
