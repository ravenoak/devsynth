#!/usr/bin/env python
"""
Script to prioritize tests based on failure history.

This script tracks test failures and uses that information to prioritize tests,
running tests that are more likely to fail first. This can provide faster
feedback during development by surfacing failures earlier in the test run.

Usage:
    python scripts/prioritize_tests.py [options]

Options:
    --test-dir DIR      Directory containing tests (default: tests)
    --history-file FILE File to store failure history (default: .test_history.json)
    --top N             Run only the top N most likely to fail tests (default: all)
    --verbose           Show verbose output
    --parallel          Run tests in parallel using pytest-xdist
    --report            Generate HTML report
    --update-only       Only update the failure history, don't run tests
    --reset             Reset the failure history
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

# Directory for test history data
HISTORY_DIR = ".test_history"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prioritize tests based on failure history."
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests (default: tests)",
    )
    parser.add_argument(
        "--history-file",
        default=os.path.join(HISTORY_DIR, "test_history.json"),
        help="File to store failure history (default: .test_history/test_history.json)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Run only the top N most likely to fail tests (default: all)",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only update the failure history, don't run tests",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset the failure history"
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="all",
        help="Only run tests in the specified category",
    )
    parser.add_argument(
        "--speed",
        choices=["fast", "medium", "slow", "all"],
        default="all",
        help="Only run tests with the specified speed marker",
    )
    return parser.parse_args()


def collect_tests(
    test_dir: str, category: str = "all", speed: str = "all"
) -> list[str]:
    """
    Collect all tests in the given directory.

    Args:
        test_dir: Directory containing tests to collect
        category: Test category to collect (unit, integration, behavior, all)
        speed: Test speed to collect (fast, medium, slow, all)

    Returns:
        List of test paths
    """
    print(f"Collecting tests in {test_dir}...")

    # Determine the test directory based on category
    if category != "all":
        if category == "unit":
            test_dir = os.path.join("tests", "unit")
        elif category == "integration":
            test_dir = os.path.join("tests", "integration")
        elif category == "behavior":
            test_dir = os.path.join("tests", "behavior")

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
        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def load_test_history(history_file: str) -> dict[str, dict[str, Any]]:
    """
    Load test failure history from file.

    Args:
        history_file: Path to the history file

    Returns:
        Dictionary mapping test paths to failure history
    """
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error loading history file {history_file}, creating new history")
            return {}
    else:
        print(f"History file {history_file} not found, creating new history")
        return {}


def save_test_history(history: dict[str, dict[str, Any]], history_file: str):
    """
    Save test failure history to file.

    Args:
        history: Dictionary mapping test paths to failure history
        history_file: Path to the history file
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(history_file), exist_ok=True)

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def reset_test_history(history_file: str):
    """
    Reset the test failure history.

    Args:
        history_file: Path to the history file
    """
    if os.path.exists(history_file):
        os.remove(history_file)
        print(f"Reset test history in {history_file}")
    else:
        print(f"History file {history_file} not found, nothing to reset")


def calculate_failure_probability(test_history: dict[str, Any]) -> float:
    """
    Calculate the probability of a test failing based on its history.

    Args:
        test_history: Dictionary containing test failure history

    Returns:
        Probability of the test failing (0.0 to 1.0)
    """
    # If the test has never been run, assume a 50% chance of failure
    if "runs" not in test_history or test_history["runs"] == 0:
        return 0.5

    # Calculate the basic failure rate
    failure_rate = test_history.get("failures", 0) / test_history["runs"]

    # Apply recency bias - more recent failures are weighted more heavily
    if "last_run" in test_history and "last_failure" in test_history:
        last_run = datetime.fromisoformat(test_history["last_run"])
        last_failure = datetime.fromisoformat(test_history["last_failure"])

        # If the test has never failed, the recency factor is 0
        if last_failure == datetime.min:
            recency_factor = 0.0
        else:
            # Calculate how recently the test failed relative to its last run
            # A test that failed on its last run will have a recency factor of 1.0
            # A test that failed a long time ago will have a recency factor close to 0.0
            time_since_last_run = (datetime.now() - last_run).total_seconds()
            time_since_last_failure = (datetime.now() - last_failure).total_seconds()

            if time_since_last_run == 0:
                recency_factor = 0.0
            else:
                recency_factor = max(
                    0.0, 1.0 - (time_since_last_failure / time_since_last_run)
                )

        # Combine the basic failure rate with the recency factor
        # This gives more weight to tests that failed recently
        return 0.7 * failure_rate + 0.3 * recency_factor

    return failure_rate


def prioritize_tests(
    tests: list[str], history: dict[str, dict[str, Any]]
) -> list[tuple[str, float]]:
    """
    Prioritize tests based on their failure history.

    Args:
        tests: List of test paths
        history: Dictionary mapping test paths to failure history

    Returns:
        List of (test_path, failure_probability) tuples, sorted by probability
    """
    prioritized_tests = []

    for test in tests:
        # Get the test's history, or create a new entry if it doesn't exist
        test_history = history.get(
            test,
            {
                "runs": 0,
                "failures": 0,
                "last_run": datetime.min.isoformat(),
                "last_failure": datetime.min.isoformat(),
            },
        )

        # Calculate the probability of the test failing
        failure_probability = calculate_failure_probability(test_history)

        prioritized_tests.append((test, failure_probability))

    # Sort tests by failure probability (highest first)
    prioritized_tests.sort(key=lambda x: x[1], reverse=True)

    return prioritized_tests


def run_tests(
    prioritized_tests: list[tuple[str, float]], args
) -> tuple[int, dict[str, bool]]:
    """
    Run the prioritized tests.

    Args:
        prioritized_tests: List of (test_path, failure_probability) tuples
        args: Command-line arguments

    Returns:
        Tuple of (exit_code, test_results) where test_results maps test paths to pass/fail status
    """
    if not prioritized_tests:
        print("No tests to run.")
        return 0, {}

    # Limit to the top N tests if specified
    if args.top is not None and args.top > 0:
        prioritized_tests = prioritized_tests[: args.top]
        print(f"Running top {len(prioritized_tests)} tests...")
    else:
        print(f"Running {len(prioritized_tests)} tests in priority order...")

    # Extract just the test paths
    test_paths = [test for test, _ in prioritized_tests]

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend(test_paths)

    # Add options based on command-line arguments
    if args.verbose:
        cmd.append("-v")

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Add JUnit XML output for parsing test results
    xml_report = os.path.join(HISTORY_DIR, "junit_report.xml")
    cmd.extend(["--junitxml", xml_report])

    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd)
    end_time = time.time()

    print(f"Tests completed in {end_time - start_time:.2f} seconds")

    # Parse the JUnit XML report to get test results
    test_results = {}
    if os.path.exists(xml_report):
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


def update_test_history(
    history: dict[str, dict[str, Any]], test_results: dict[str, bool]
) -> dict[str, dict[str, Any]]:
    """
    Update the test failure history based on test results.

    Args:
        history: Dictionary mapping test paths to failure history
        test_results: Dictionary mapping test paths to pass/fail status

    Returns:
        Updated history dictionary
    """
    now = datetime.now().isoformat()

    for test_path, passed in test_results.items():
        # Get the test's history, or create a new entry if it doesn't exist
        test_history = history.get(
            test_path,
            {
                "runs": 0,
                "failures": 0,
                "last_run": datetime.min.isoformat(),
                "last_failure": datetime.min.isoformat(),
            },
        )

        # Update the history
        test_history["runs"] = test_history.get("runs", 0) + 1
        test_history["last_run"] = now

        if not passed:
            test_history["failures"] = test_history.get("failures", 0) + 1
            test_history["last_failure"] = now

        history[test_path] = test_history

    return history


def main():
    """Main function."""
    args = parse_args()

    # Reset the test history if requested
    if args.reset:
        reset_test_history(args.history_file)
        if args.update_only:
            return 0

    # Load the test history
    history = load_test_history(args.history_file)

    # Collect tests
    tests = collect_tests(args.test_dir, args.category, args.speed)

    if not tests:
        print("No tests found.")
        return 0

    # Prioritize tests based on failure history
    prioritized_tests = prioritize_tests(tests, history)

    # Print the prioritized tests
    print("\nTests prioritized by failure probability:")
    for i, (test, probability) in enumerate(prioritized_tests[:10]):
        print(f"{i+1}. {test} - {probability:.2f}")

    if len(prioritized_tests) > 10:
        print(f"... and {len(prioritized_tests) - 10} more tests")

    # If update-only is specified, don't run the tests
    if args.update_only:
        print("\nSkipping test execution (--update-only specified)")
        return 0

    # Run the tests
    exit_code, test_results = run_tests(prioritized_tests, args)

    # Update the test history
    if test_results:
        history = update_test_history(history, test_results)
        save_test_history(history, args.history_file)
        print(f"Updated test history in {args.history_file}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
