#!/usr/bin/env python3
"""
Execute Test Categorization

This script executes the test categorization plan created by create_test_categorization_schedule.py.
It runs tests according to the schedule, measures their execution time, and applies appropriate
speed markers based on the execution time.

Usage:
    python scripts/execute_test_categorization.py [options]

Options:
    --schedule FILE      Schedule file (default: .test_categorization_schedule.json)
    --progress FILE      Progress file (default: .test_categorization_progress.json)
    --date DATE          Date to run tests for (default: today)
    --fast-threshold N   Threshold for fast tests in seconds (default: 0.1)
    --medium-threshold N Threshold for medium tests in seconds (default: 1.0)
    --dry-run            Don't apply markers, just measure execution time
    --force              Force re-categorization of already categorized tests
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import check_test_has_marker
except ImportError:
    print("Error: common_test_collector.py not found")
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Execute the test categorization plan")
    parser.add_argument(
        "--schedule",
        default=".test_categorization_schedule.json",
        help="Schedule file (default: .test_categorization_schedule.json)",
    )
    parser.add_argument(
        "--progress",
        default=".test_categorization_progress.json",
        help="Progress file (default: .test_categorization_progress.json)",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date to run tests for (default: today)",
    )
    parser.add_argument(
        "--fast-threshold",
        type=float,
        default=0.1,
        help="Threshold for fast tests in seconds (default: 0.1)",
    )
    parser.add_argument(
        "--medium-threshold",
        type=float,
        default=1.0,
        help="Threshold for medium tests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't apply markers, just measure execution time",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-categorization of already categorized tests",
    )
    return parser.parse_args()


def load_schedule(schedule_file):
    """Load the test categorization schedule."""
    try:
        with open(schedule_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading schedule file: {e}")
        sys.exit(1)


def load_progress(progress_file):
    """Load the test categorization progress."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading progress file: {e}")
            return {"categorized_tests": {}, "last_date": None}
    return {"categorized_tests": {}, "last_date": None}


def save_progress(progress, progress_file):
    """Save the test categorization progress."""
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Progress saved to {progress_file}")


def get_tests_for_date(schedule, target_date):
    """Get tests scheduled for a specific date."""
    if target_date in schedule["days"]:
        return schedule["days"][target_date]["tests"]
    else:
        print(f"No tests scheduled for {target_date}")
        return []


def filter_uncategorized_tests(tests, progress, force=False):
    """Filter tests that haven't been categorized yet."""
    if force:
        return tests

    categorized_tests = progress["categorized_tests"].keys()
    return [test for test in tests if test not in categorized_tests]


def run_test_and_measure_time(test):
    """Run a test and measure its execution time."""
    cmd = ["python", "-m", "pytest", test, "-v"]

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    execution_time = time.time() - start_time

    passed = result.returncode == 0

    return {
        "test": test,
        "execution_time": execution_time,
        "passed": passed,
        "output": result.stdout,
        "error": result.stderr,
    }


def determine_speed_category(execution_time, fast_threshold, medium_threshold):
    """Determine the speed category based on execution time."""
    if execution_time <= fast_threshold:
        return "fast"
    elif execution_time <= medium_threshold:
        return "medium"
    else:
        return "slow"


def apply_speed_marker(test, speed_category, dry_run=False):
    """Apply a speed marker to a test."""
    if dry_run:
        print(f"Would apply {speed_category} marker to {test}")
        return True

    # Extract file path from test path
    if "::" in test:
        file_path = test.split("::")[0]
        test_name = test.split("::")[-1]
        if "(" in test_name:  # Handle parameterized tests
            test_name = test_name.split("(")[0]
    else:
        file_path = test
        test_name = None

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    try:
        # Read the file content
        with open(file_path) as f:
            content = f.read()

        # Find the test function or class
        if test_name:
            # Find the test function or method
            import re

            # Handle class methods
            if "::" in test and len(test.split("::")) > 2:
                class_name = test.split("::")[1]
                method_name = test_name

                # Find the class
                class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*\(")
                class_match = class_pattern.search(content)

                if class_match:
                    # Find the method within the class
                    class_content = content[class_match.start() :]
                    method_pattern = re.compile(rf"def\s+{re.escape(method_name)}\s*\(")
                    method_match = method_pattern.search(class_content)

                    if method_match:
                        # Calculate the position in the original content
                        method_pos = class_match.start() + method_match.start()

                        # Find the line before the method
                        line_start = content.rfind("\n", 0, method_pos) + 1

                        # Check if there's already a marker
                        marker_line = content[line_start:method_pos].strip()
                        if f"@pytest.mark.{speed_category}" in marker_line:
                            print(f"Test {test} already has {speed_category} marker")
                            return True

                        # Insert the marker before the method
                        new_content = (
                            content[:line_start]
                            + f"    @pytest.mark.{speed_category}\n"
                            + content[line_start:]
                        )

                        # Check if pytest is imported
                        if (
                            "import pytest" not in content
                            and "from pytest import" not in content
                        ):
                            # Add pytest import at the top of the file
                            new_content = "import pytest\n" + new_content

                        # Write the modified content back to the file
                        with open(file_path, "w") as f:
                            f.write(new_content)

                        print(f"Applied {speed_category} marker to {test}")
                        return True
            else:
                # Handle regular functions
                func_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
                func_match = func_pattern.search(content)

                if func_match:
                    # Find the line before the function
                    line_start = content.rfind("\n", 0, func_match.start()) + 1

                    # Check if there's already a marker
                    marker_line = content[line_start : func_match.start()].strip()
                    if f"@pytest.mark.{speed_category}" in marker_line:
                        print(f"Test {test} already has {speed_category} marker")
                        return True

                    # Insert the marker before the function
                    new_content = (
                        content[:line_start]
                        + f"@pytest.mark.{speed_category}\n"
                        + content[line_start:]
                    )

                    # Check if pytest is imported
                    if (
                        "import pytest" not in content
                        and "from pytest import" not in content
                    ):
                        # Add pytest import at the top of the file
                        new_content = "import pytest\n" + new_content

                    # Write the modified content back to the file
                    with open(file_path, "w") as f:
                        f.write(new_content)

                    print(f"Applied {speed_category} marker to {test}")
                    return True

        print(f"Error: Could not find test function or method for {test}")
        return False

    except Exception as e:
        print(f"Error applying marker to {test}: {e}")
        return False


def update_progress(progress, test, speed_category, execution_time):
    """Update the progress tracking file."""
    progress["categorized_tests"][test] = {
        "speed_category": speed_category,
        "execution_time": execution_time,
        "categorized_at": datetime.now().isoformat(),
    }
    progress["last_date"] = datetime.now().isoformat()

    # Update summary counts
    if "summary" not in progress:
        progress["summary"] = {"fast": 0, "medium": 0, "slow": 0, "total": 0}

    progress["summary"][speed_category] = progress["summary"].get(speed_category, 0) + 1
    progress["summary"]["total"] = progress["summary"].get("total", 0) + 1

    return progress


def print_summary(results):
    """Print a summary of the test categorization results."""
    print("\nTest Categorization Summary:")
    print(f"Total tests: {len(results)}")

    # Count by speed category
    speed_counts = {"fast": 0, "medium": 0, "slow": 0}
    for result in results:
        speed_counts[result["speed_category"]] += 1

    print(f"Fast tests: {speed_counts['fast']}")
    print(f"Medium tests: {speed_counts['medium']}")
    print(f"Slow tests: {speed_counts['slow']}")

    # Count passed/failed
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    # Average execution time
    avg_time = (
        sum(result["execution_time"] for result in results) / len(results)
        if results
        else 0
    )
    print(f"Average execution time: {avg_time:.2f}s")


def main():
    """Main function."""
    args = parse_args()

    # Load schedule and progress
    schedule = load_schedule(args.schedule)
    progress = load_progress(args.progress)

    # Get tests for the specified date
    tests = get_tests_for_date(schedule, args.date)
    print(f"Found {len(tests)} tests scheduled for {args.date}")

    # Filter uncategorized tests
    uncategorized_tests = filter_uncategorized_tests(tests, progress, args.force)
    print(f"Found {len(uncategorized_tests)} uncategorized tests")

    if not uncategorized_tests:
        print("No tests to categorize")
        return

    # Run tests and measure execution time
    results = []
    for i, test in enumerate(uncategorized_tests):
        print(f"Running test {i+1}/{len(uncategorized_tests)}: {test}")

        # Check if the test already has a marker
        has_marker, existing_marker = check_test_has_marker(
            test, ["fast", "medium", "slow"]
        )
        if has_marker and not args.force:
            print(f"Test {test} already has {existing_marker} marker, skipping")
            continue

        # Run the test and measure execution time
        result = run_test_and_measure_time(test)

        # Determine speed category
        speed_category = determine_speed_category(
            result["execution_time"], args.fast_threshold, args.medium_threshold
        )

        print(f"Test {test} took {result['execution_time']:.2f}s ({speed_category})")

        # Apply speed marker
        if not args.dry_run:
            success = apply_speed_marker(test, speed_category)
            if success:
                # Update progress
                progress = update_progress(
                    progress, test, speed_category, result["execution_time"]
                )

        # Add to results
        results.append(
            {
                "test": test,
                "execution_time": result["execution_time"],
                "speed_category": speed_category,
                "passed": result["passed"],
            }
        )

    # Save progress
    if not args.dry_run:
        save_progress(progress, args.progress)

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
