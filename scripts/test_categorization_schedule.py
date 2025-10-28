#!/usr/bin/env python
"""
Script to implement a schedule for categorizing remaining tests.

This script creates and manages a schedule for incrementally categorizing
the remaining unmarked tests in the DevSynth project. It prioritizes
high-priority modules and provides a timeline for categorizing all tests.

Usage:
    python scripts/test_categorization_schedule.py [options]

Options:
    --generate-schedule  Generate a new categorization schedule
    --update-progress    Update the progress of the categorization schedule
    --run-scheduled      Run the scheduled categorization for today
    --list-schedule      List the current categorization schedule
    --priority-only      Only include high-priority modules in the schedule
    --days DAYS          Number of days to spread the categorization over (default: 14)
    --batch-size SIZE    Number of tests to categorize in each batch (default: 100)
    --dry-run            Show what would be done without making changes
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import test_utils

# Schedule file
SCHEDULE_FILE = ".test_categorization_schedule.json"

# High-priority modules to categorize first
HIGH_PRIORITY_MODULES = [
    "tests/unit/application/cli",  # CLI components
    "tests/unit/adapters/memory",  # Memory adapters
    "tests/unit/adapters/llm",  # LLM adapters
    "tests/integration/memory",  # Memory integration
    "tests/unit/application/wsde",  # WSDE components
    "tests/unit/application/webui",  # WebUI components
]

# Test categories - ensure consistency with test_metrics_optimized.py
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Implement a schedule for categorizing remaining tests."
    )
    parser.add_argument(
        "--generate-schedule",
        action="store_true",
        help="Generate a new categorization schedule",
    )
    parser.add_argument(
        "--update-progress",
        action="store_true",
        help="Update the progress of the categorization schedule",
    )
    parser.add_argument(
        "--run-scheduled",
        action="store_true",
        help="Run the scheduled categorization for today",
    )
    parser.add_argument(
        "--list-schedule",
        action="store_true",
        help="List the current categorization schedule",
    )
    parser.add_argument(
        "--priority-only",
        action="store_true",
        help="Only include high-priority modules in the schedule",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days to spread the categorization over (default: 14)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of tests to categorize in each batch (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return parser.parse_args()


def collect_all_test_modules() -> list[str]:
    """
    Collect all test modules in the project.

    Returns:
        List of test module paths
    """
    test_modules = []

    # Walk the tests directory
    for root, dirs, files in os.walk("tests"):
        # Skip cache directories
        if ".test_cache" in root or ".pytest_cache" in root:
            continue

        # Check if this directory contains test files
        has_test_files = any(f.startswith("test_") and f.endswith(".py") for f in files)

        if has_test_files:
            # Add this directory as a test module
            test_modules.append(root)

    return test_modules


# This function is replaced by test_utils.collect_tests


def count_tests_in_module(module_path: str) -> int:
    """
    Count the number of tests in a module.

    Args:
        module_path: Path to the test module

    Returns:
        Number of tests in the module
    """
    # Find the category for this module
    category = None
    for cat, path in TEST_CATEGORIES.items():
        if module_path.startswith(path):
            category = cat
            break

    if not category:
        return 0

    # Get the test directory for this category
    test_dir = TEST_CATEGORIES[category]

    # Collect all tests in the category
    all_tests = test_utils.collect_tests(test_dir)

    # Count tests that belong to this module
    test_count = sum(1 for test in all_tests if test.startswith(module_path))

    return test_count


def count_categorized_tests_in_module(module_path: str) -> int:
    """
    Count the number of tests in a module that already have speed markers.

    Args:
        module_path: Path to the test module

    Returns:
        Number of categorized tests in the module
    """
    # Find the category for this module
    category = None
    for cat, path in TEST_CATEGORIES.items():
        if module_path.startswith(path):
            category = cat
            break

    if not category:
        return 0

    # Get the test directory for this category
    test_dir = TEST_CATEGORIES[category]

    # Collect all tests in the category
    all_tests = test_utils.collect_tests(test_dir)

    # Filter tests that belong to this module
    module_tests = [test for test in all_tests if test.startswith(module_path)]

    # Count tests with speed markers
    categorized_count = 0
    for test_path in module_tests:
        # Extract the test file path from the test path
        match = test_path.split("::")[0] if "::" in test_path else test_path
        if not match.endswith(".py"):
            continue

        file_path = match

        # Check if the file exists
        if not os.path.exists(file_path):
            continue

        # Check if the file contains speed markers for this test
        with open(file_path) as f:
            content = f.read()

            # Extract the test name from the test path
            test_name = test_path.split("::")[-1] if "::" in test_path else None
            if not test_name:
                continue

            # Look for speed markers associated with this test
            # This is a simplified approach and may not be 100% accurate
            # A more accurate approach would involve parsing the Python code
            test_def = f"def {test_name}"
            if test_def in content:
                # Find the position of the test definition
                test_pos = content.find(test_def)
                if test_pos > 0:
                    # Check if there's a speed marker before the test definition
                    # within a reasonable number of lines
                    test_context = content[max(0, test_pos - 200) : test_pos]
                    if (
                        "@pytest.mark.fast" in test_context
                        or "@pytest.mark.medium" in test_context
                        or "@pytest.mark.slow" in test_context
                    ):
                        categorized_count += 1

    return categorized_count


def generate_schedule(args) -> dict[str, Any]:
    """
    Generate a schedule for categorizing remaining tests.

    Args:
        args: Command-line arguments

    Returns:
        Dictionary containing the schedule
    """
    print("Generating test categorization schedule...")

    # Collect all test modules
    all_modules = collect_all_test_modules()

    # Filter to high-priority modules if requested
    if args.priority_only:
        modules = [
            m
            for m in all_modules
            if any(m.startswith(hp) for hp in HIGH_PRIORITY_MODULES)
        ]
    else:
        # Start with high-priority modules, then add the rest
        modules = []
        for hp in HIGH_PRIORITY_MODULES:
            modules.extend([m for m in all_modules if m.startswith(hp)])

        # Add remaining modules
        for m in all_modules:
            if not any(m.startswith(hp) for hp in HIGH_PRIORITY_MODULES):
                modules.append(m)

    # Count tests in each module
    module_test_counts = {}
    total_tests = 0
    total_categorized = 0

    for module in modules:
        test_count = count_tests_in_module(module)
        categorized_count = count_categorized_tests_in_module(module)
        uncategorized_count = test_count - categorized_count

        if uncategorized_count > 0:
            module_test_counts[module] = {
                "total": test_count,
                "categorized": categorized_count,
                "uncategorized": uncategorized_count,
            }
            total_tests += test_count
            total_categorized += categorized_count

    # Calculate total uncategorized tests
    total_uncategorized = total_tests - total_categorized

    # Calculate tests per day
    days = args.days
    tests_per_day = (total_uncategorized + days - 1) // days  # Ceiling division

    # Create daily schedule
    daily_schedule = {}
    remaining_modules = list(module_test_counts.keys())
    remaining_tests = total_uncategorized

    for day in range(1, days + 1):
        day_key = f"day_{day}"
        day_date = (
            (datetime.datetime.now() + datetime.timedelta(days=day - 1))
            .date()
            .isoformat()
        )

        # Allocate modules for this day
        day_modules = []
        day_tests = 0

        while remaining_modules and day_tests < tests_per_day:
            module = remaining_modules[0]
            module_tests = module_test_counts[module]["uncategorized"]

            if day_tests + module_tests <= tests_per_day or not day_modules:
                # Add this module to today's schedule
                day_modules.append(module)
                day_tests += module_tests
                remaining_modules.pop(0)
            else:
                # This module would exceed today's quota, try the next one
                break

        daily_schedule[day_key] = {
            "date": day_date,
            "modules": day_modules,
            "total_tests": day_tests,
        }

        remaining_tests -= day_tests

    # Create the schedule
    schedule = {
        "generated_at": datetime.datetime.now().isoformat(),
        "total_tests": total_tests,
        "total_categorized": total_categorized,
        "total_uncategorized": total_uncategorized,
        "days": days,
        "tests_per_day": tests_per_day,
        "batch_size": args.batch_size,
        "module_test_counts": module_test_counts,
        "daily_schedule": daily_schedule,
    }

    return schedule


def save_schedule(schedule: dict[str, Any], dry_run: bool = False) -> None:
    """
    Save the schedule to a file.

    Args:
        schedule: Schedule to save
        dry_run: Whether to show changes without making them
    """
    if dry_run:
        print(f"Would save schedule to {SCHEDULE_FILE}")
        return

    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)

    print(f"Schedule saved to {SCHEDULE_FILE}")


def load_schedule() -> dict[str, Any]:
    """
    Load the schedule from a file.

    Returns:
        Dictionary containing the schedule
    """
    if not os.path.exists(SCHEDULE_FILE):
        print(f"Schedule file {SCHEDULE_FILE} not found")
        return {}

    with open(SCHEDULE_FILE) as f:
        schedule = json.load(f)

    return schedule


def update_progress(args) -> None:
    """
    Update the progress of the categorization schedule.

    Args:
        args: Command-line arguments
    """
    print("Updating categorization progress...")

    # Load the schedule
    schedule = load_schedule()
    if not schedule:
        print("No schedule found. Generate a schedule first.")
        return

    # Count tests in each module
    module_test_counts = schedule["module_test_counts"]
    total_tests = 0
    total_categorized = 0

    for module, counts in module_test_counts.items():
        test_count = count_tests_in_module(module)
        categorized_count = count_categorized_tests_in_module(module)
        uncategorized_count = test_count - categorized_count

        module_test_counts[module] = {
            "total": test_count,
            "categorized": categorized_count,
            "uncategorized": uncategorized_count,
        }

        total_tests += test_count
        total_categorized += categorized_count

    # Calculate total uncategorized tests
    total_uncategorized = total_tests - total_categorized

    # Update the schedule
    schedule["total_tests"] = total_tests
    schedule["total_categorized"] = total_categorized
    schedule["total_uncategorized"] = total_uncategorized
    schedule["updated_at"] = datetime.datetime.now().isoformat()

    # Save the updated schedule
    save_schedule(schedule, args.dry_run)

    # Print progress
    print(
        f"Progress: {total_categorized}/{total_tests} tests categorized ({total_categorized/total_tests*100:.1f}%)"
    )
    print(f"Remaining: {total_uncategorized} tests")


def run_scheduled_categorization(args) -> None:
    """
    Run the scheduled categorization for today.

    Args:
        args: Command-line arguments
    """
    print("Running scheduled categorization for today...")

    # Load the schedule
    schedule = load_schedule()
    if not schedule:
        print("No schedule found. Generate a schedule first.")
        return

    # Find today's schedule
    today = datetime.datetime.now().date()
    today_key = None

    for day_key, day_schedule in schedule["daily_schedule"].items():
        day_date = datetime.datetime.fromisoformat(day_schedule["date"]).date()
        if day_date == today:
            today_key = day_key
            break

    if not today_key:
        print(f"No categorization scheduled for today ({today.isoformat()})")
        return

    # Get the modules to categorize today
    modules = schedule["daily_schedule"][today_key]["modules"]

    if not modules:
        print("No modules to categorize today")
        return

    print(f"Categorizing {len(modules)} modules today:")
    for module in modules:
        print(f"  - {module}")

    # Run the categorization for each module
    for module in modules:
        print(f"\nCategorizing tests in {module}...")

        # Build the command
        cmd = [
            "python",
            "scripts/incremental_test_categorization.py",
            "--module",
            module,
            "--batch-size",
            str(args.batch_size),
            "--max-tests",
            str(schedule["tests_per_day"]),
            "--update",
        ]

        if args.dry_run:
            print(f"Would run: {' '.join(cmd)}")
        else:
            # Run the command
            subprocess.run(cmd)

    # Update the progress
    if not args.dry_run:
        update_progress(args)


def list_schedule(args) -> None:
    """
    List the current categorization schedule.

    Args:
        args: Command-line arguments
    """
    # Load the schedule
    schedule = load_schedule()
    if not schedule:
        print("No schedule found. Generate a schedule first.")
        return

    # Print schedule information
    print("\nTest Categorization Schedule")
    print("===========================")
    print(
        f"Generated: {datetime.datetime.fromisoformat(schedule['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if "updated_at" in schedule:
        print(
            f"Last updated: {datetime.datetime.fromisoformat(schedule['updated_at']).strftime('%Y-%m-%d %H:%M:%S')}"
        )

    print(f"\nTotal tests: {schedule['total_tests']}")
    print(
        f"Categorized: {schedule['total_categorized']} ({schedule['total_categorized']/schedule['total_tests']*100:.1f}%)"
    )
    print(
        f"Uncategorized: {schedule['total_uncategorized']} ({schedule['total_uncategorized']/schedule['total_tests']*100:.1f}%)"
    )
    print(f"\nSchedule duration: {schedule['days']} days")
    print(f"Tests per day: ~{schedule['tests_per_day']}")
    print(f"Batch size: {schedule['batch_size']}")

    # Print daily schedule
    print("\nDaily Schedule:")
    for day_key, day_schedule in sorted(schedule["daily_schedule"].items()):
        day_num = int(day_key.split("_")[1])
        day_date = datetime.datetime.fromisoformat(day_schedule["date"]).date()
        today = datetime.datetime.now().date()

        status = ""
        if day_date < today:
            status = " (past)"
        elif day_date == today:
            status = " (today)"

        print(f"\nDay {day_num} - {day_date.isoformat()}{status}")
        print(f"Modules to categorize: {len(day_schedule['modules'])}")
        print(f"Total tests: {day_schedule['total_tests']}")

        for module in day_schedule["modules"]:
            counts = schedule["module_test_counts"][module]
            print(f"  - {module}: {counts['uncategorized']} uncategorized tests")


def main() -> None:
    """Main function."""
    args = parse_args()

    if args.generate_schedule:
        schedule = generate_schedule(args)
        save_schedule(schedule, args.dry_run)
    elif args.update_progress:
        update_progress(args)
    elif args.run_scheduled:
        run_scheduled_categorization(args)
    elif args.list_schedule:
        list_schedule(args)
    else:
        print(
            "No action specified. Use --generate-schedule, --update-progress, --run-scheduled, or --list-schedule."
        )


if __name__ == "__main__":
    main()
