#!/usr/bin/env python
"""
Common utilities for test scripts.

This module provides common functionality for test scripts to eliminate
duplicate code and ensure consistent argument handling across all scripts.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector. Allow execution as a standalone script by
# falling back to a direct import if relative imports fail.
try:  # pragma: no cover - import resolution
    from . import common_test_collector
except ImportError:  # pragma: no cover - script execution
    import pathlib
    import sys

    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    import common_test_collector

# Cache directories
TEST_CACHE_DIR = ".test_cache"
COLLECTION_CACHE_DIR = os.path.join(TEST_CACHE_DIR, "collection")
TIMING_CACHE_DIR = os.path.join(TEST_CACHE_DIR, "timing")
HISTORY_DIR = os.path.join(TEST_CACHE_DIR, "history")

# Ensure cache directories exist
os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)
os.makedirs(TIMING_CACHE_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


def add_common_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common arguments to an argument parser.

    Args:
        parser: Argument parser to add arguments to

    Returns:
        Updated argument parser
    """
    # Test selection options
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests (default: tests)",
    )
    test_group.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="all",
        help="Only run tests in the specified category",
    )
    test_group.add_argument(
        "--speed",
        choices=["fast", "medium", "slow", "all"],
        default="all",
        help="Only run tests with the specified speed marker",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--verbose", action="store_true", help="Show verbose output"
    )
    output_group.add_argument(
        "--report", action="store_true", help="Generate HTML report"
    )

    # Performance options
    perf_group = parser.add_argument_group("Performance Options")
    perf_group.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    perf_group.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (always collect fresh data)",
    )
    perf_group.add_argument(
        "--segment",
        action="store_true",
        help="Run tests in smaller batches to improve performance",
    )
    perf_group.add_argument(
        "--segment-size",
        type=int,
        default=50,
        help="Number of tests per batch when using --segment (default: 50)",
    )

    return parser


def get_test_directory(category: str) -> str:
    """
    Get the test directory for a specific category.

    Args:
        category: Test category (unit, integration, behavior, all)

    Returns:
        Path to the test directory
    """
    if category == "all":
        return "tests"
    elif category in ["unit", "integration", "behavior"]:
        return os.path.join("tests", category)
    else:
        raise ValueError(f"Invalid category: {category}")


def collect_tests(
    test_dir: str, speed: str = "all", use_cache: bool = True
) -> list[str]:
    """
    Collect all tests in the given directory.

    Args:
        test_dir: Directory containing tests to collect
        speed: Test speed to collect (fast, medium, slow, all)
        use_cache: Whether to use cached test collection results

    Returns:
        List of test paths
    """
    print(f"Collecting tests in {test_dir}...")

    # Determine the test category based on the directory
    category = None
    for cat, path in common_test_collector.TEST_CATEGORIES.items():
        if test_dir == path or test_dir.startswith(path + "/"):
            category = cat
            break

    # If no specific category is found, use the common_test_collector.collect_tests function
    if category is None:
        if test_dir == "tests":
            # Collecting all tests
            tests = common_test_collector.collect_tests(use_cache=use_cache)
        else:
            # Custom directory, fall back to the original implementation
            print(
                f"Warning: Using fallback test collection for non-standard directory: {test_dir}"
            )
            return _collect_tests_fallback(test_dir, speed, use_cache)
    else:
        # Collecting tests for a specific category
        tests = common_test_collector.collect_tests_by_category(
            category, use_cache=use_cache
        )

    # Filter by speed if specified
    if speed != "all":
        # Get tests with the specified speed marker
        tests_with_markers = common_test_collector.get_tests_with_markers(
            [speed], use_cache=use_cache
        )

        # Extract tests for the current category with the specified speed marker
        if category is None:
            # If no specific category, combine tests from all categories
            filtered_tests = []
            for cat in tests_with_markers:
                filtered_tests.extend(tests_with_markers[cat][speed])
        else:
            # If specific category, use tests from that category
            filtered_tests = tests_with_markers.get(category, {}).get(speed, [])

        # Special handling for behavior tests - if no tests with speed markers, return all behavior tests
        if category == "behavior" and not filtered_tests:
            print(
                f"No behavior tests found with {speed} marker. Returning all behavior tests..."
            )
            return tests

        tests = filtered_tests

    print(f"Found {len(tests)} tests")
    return tests


def _collect_tests_fallback(
    test_dir: str, speed: str = "all", use_cache: bool = True
) -> list[str]:
    """
    Fallback method to collect tests using pytest directly.
    Used for non-standard test directories that don't match the known categories.

    Args:
        test_dir: Directory containing tests to collect
        speed: Test speed to collect (fast, medium, slow, all)
        use_cache: Whether to use cached test collection results

    Returns:
        List of test paths
    """
    # Create cache directory if it doesn't exist
    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)

    # Check if we have a cached collection
    cache_key = f"{test_dir.replace('/', '_')}_{speed}"
    cache_file = os.path.join(COLLECTION_CACHE_DIR, f"{cache_key}_tests.json")

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cached_data = json.load(f)

            # Use cache if it's less than 1 hour old
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                print(
                    f"Using cached test collection for {test_dir} (less than 1 hour old)"
                )
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and collect tests
            pass

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest", test_dir, "--collect-only", "-q"]

    # Add speed marker if specified
    if speed != "all":
        cmd.extend(["-m", speed])

    try:
        collect_result = subprocess.run(
            cmd, check=False, capture_output=True, text=True
        )
        test_list = []

        # Parse the output to get the list of tests
        for line in collect_result.stdout.split("\n"):
            if line.startswith(test_dir):
                test_list.append(line.strip())

        if not test_list:
            print(f"No tests found in {test_dir}")
            return []

        print(f"Found {len(test_list)} tests")

        # Cache the results
        if use_cache:
            cache_data = {"timestamp": datetime.now().isoformat(), "tests": test_list}
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def run_tests(
    tests: list[str], args, xml_report: str | None = None
) -> tuple[int, dict[str, bool]]:
    """
    Run the specified tests.

    Args:
        tests: List of test paths to run
        args: Command-line arguments
        xml_report: Path to JUnit XML report file (optional)

    Returns:
        Tuple of (exit_code, test_results) where test_results maps test paths to pass/fail status
    """
    if not tests:
        print("No tests to run.")
        return 0, {}

    print(f"Running {len(tests)} tests...")

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend(tests)

    # Add options based on command-line arguments
    if hasattr(args, "verbose") and args.verbose:
        cmd.append("-v")

    if hasattr(args, "parallel") and args.parallel:
        cmd.extend(["-n", "auto"])

    if hasattr(args, "report") and args.report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Add JUnit XML output for parsing test results if specified
    if xml_report:
        cmd.extend(["--junitxml", xml_report])

    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd)
    end_time = time.time()

    print(f"Tests completed in {end_time - start_time:.2f} seconds")

    # Parse the JUnit XML report to get test results if specified
    test_results = {}
    if xml_report and os.path.exists(xml_report):
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(xml_report)
            root = tree.getroot()

            for testcase in root.findall(".//testcase"):
                classname = testcase.get("classname", "")
                name = testcase.get("name", "")
                test_path = f"{classname}.{name}"

                # Check if the test failed
                failure = testcase.find("failure")
                error = testcase.find("error")
                skipped = testcase.find("skipped")

                if failure is not None or error is not None:
                    test_results[test_path] = False
                elif skipped is not None:
                    # Skipped tests are not counted as either passed or failed
                    pass
                else:
                    test_results[test_path] = True
        except Exception as e:
            print(f"Error parsing JUnit XML report: {e}")

    return result.returncode, test_results


def run_tests_in_segments(
    tests: list[str], args, segment_size: int = 50, xml_report: str | None = None
) -> tuple[int, dict[str, bool]]:
    """
    Run tests in smaller batches to improve performance.

    Args:
        tests: List of test paths to run
        args: Command-line arguments
        segment_size: Number of tests per batch
        xml_report: Path to JUnit XML report file (optional)

    Returns:
        Tuple of (exit_code, test_results) where test_results maps test paths to pass/fail status
    """
    if not tests:
        print("No tests to run.")
        return 0, {}

    print(f"Running {len(tests)} tests in segments of {segment_size}...")

    all_results = {}
    exit_code = 0

    # Run tests in batches
    for i in range(0, len(tests), segment_size):
        batch = tests[i : i + segment_size]
        print(
            f"\nRunning batch {i//segment_size + 1}/{(len(tests) + segment_size - 1)//segment_size}..."
        )

        # Create a unique XML report file for this batch if needed
        batch_xml_report = None
        if xml_report:
            batch_xml_report = f"{xml_report}.batch{i//segment_size + 1}"

        # Run the batch
        batch_exit_code, batch_results = run_tests(batch, args, batch_xml_report)

        # Update the overall results
        all_results.update(batch_results)

        # Update the exit code (non-zero if any batch fails)
        if batch_exit_code != 0:
            exit_code = batch_exit_code

    return exit_code, all_results


def clear_all_caches(
    collection: bool = True,
    timing: bool = True,
    history: bool = True,
    common_collector: bool = True,
    verbose: bool = False,
) -> None:
    """
    Clear all test-related caches.

    Args:
        collection: Whether to clear the test collection cache
        timing: Whether to clear the test timing cache
        history: Whether to clear the test history cache
        common_collector: Whether to clear the common_test_collector cache
        verbose: Whether to print verbose output

    Returns:
        None
    """
    import glob
    import shutil

    # Clear common_test_collector cache if requested
    if common_collector:
        try:
            common_test_collector.clear_cache()
            if verbose:
                print("Cleared common_test_collector cache")
        except Exception as e:
            print(f"Error clearing common_test_collector cache: {e}")

    # Clear test collection cache if requested
    if collection:
        try:
            if os.path.exists(COLLECTION_CACHE_DIR):
                # Remove all files in the collection cache directory
                for cache_file in glob.glob(
                    os.path.join(COLLECTION_CACHE_DIR, "*.json")
                ):
                    os.remove(cache_file)
                if verbose:
                    print(f"Cleared test collection cache: {COLLECTION_CACHE_DIR}")
        except Exception as e:
            print(f"Error clearing test collection cache: {e}")

    # Clear test timing cache if requested
    if timing:
        try:
            if os.path.exists(TIMING_CACHE_DIR):
                # Remove all files in the timing cache directory
                for cache_file in glob.glob(os.path.join(TIMING_CACHE_DIR, "*.json")):
                    os.remove(cache_file)
                if verbose:
                    print(f"Cleared test timing cache: {TIMING_CACHE_DIR}")
        except Exception as e:
            print(f"Error clearing test timing cache: {e}")

    # Clear test history cache if requested
    if history:
        try:
            if os.path.exists(HISTORY_DIR):
                # Remove all files in the history directory
                for cache_file in glob.glob(os.path.join(HISTORY_DIR, "*.json")):
                    os.remove(cache_file)
                if verbose:
                    print(f"Cleared test history cache: {HISTORY_DIR}")
        except Exception as e:
            print(f"Error clearing test history cache: {e}")

    if verbose:
        print("Cache clearing completed")


def measure_test_time(
    test_path: str, timeout: int = 30, use_cache: bool = True
) -> tuple[float, bool, bool]:
    """
    Measure the execution time of a single test.

    Args:
        test_path: Path to the test to measure
        timeout: Timeout in seconds
        use_cache: Whether to use cached timing results

    Returns:
        Tuple of (execution_time, passed, skipped)
    """
    # Check if we have a cached timing
    cache_key = test_path.replace("/", "_").replace(":", "_")
    cache_file = os.path.join(TIMING_CACHE_DIR, f"{cache_key}_timing.json")

    if use_cache and os.path.exists(cache_file):
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
            # Invalid cache, ignore and measure the test
            pass

    # Run the test and measure execution time
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--maxfail=1",
        test_path,
        "-v",
    ]

    start_time = time.time()

    try:
        # Set up a timeout
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=timeout
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Check if the test passed or was skipped
        passed = result.returncode == 0
        skipped = "SKIPPED" in result.stdout

        # Cache the results
        if use_cache:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "passed": passed,
                "skipped": skipped,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        return execution_time, passed, skipped
    except subprocess.TimeoutExpired:
        print(f"Test timed out: {test_path}")

        # Cache the timeout
        if use_cache:
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
