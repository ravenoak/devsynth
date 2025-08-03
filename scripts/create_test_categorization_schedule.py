#!/usr/bin/env python3
"""
Create Test Categorization Schedule

This script creates a schedule for categorizing tests by speed (fast, medium, slow)
in a prioritized and incremental manner.

Usage:
    python scripts/create_test_categorization_schedule.py [options]

Options:
    --output FILE       Output file for the schedule (default: .test_categorization_schedule.json)
    --weeks WEEKS       Number of weeks to schedule (default: 4)
    --tests-per-day N   Target number of tests to categorize per day (default: 100)
    --priority-modules  List of high-priority modules to categorize first
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import collect_tests, collect_tests_by_category, check_test_has_marker
except ImportError:
    print("Error: common_test_collector.py not found")
    sys.exit(1)

# Define high-priority modules
HIGH_PRIORITY_MODULES = [
    "tests/unit/interface",
    "tests/unit/adapters/memory",
    "tests/unit/adapters/llm",
    "tests/integration/memory",
    "tests/unit/application/wsde",
    "tests/unit/interface/webui"
]

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a schedule for categorizing tests by speed"
    )
    parser.add_argument(
        "--output",
        default=".test_categorization_schedule.json",
        help="Output file for the schedule (default: .test_categorization_schedule.json)"
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks to schedule (default: 4)"
    )
    parser.add_argument(
        "--tests-per-day",
        type=int,
        default=100,
        help="Target number of tests to categorize per day (default: 100)"
    )
    parser.add_argument(
        "--priority-modules",
        nargs="+",
        default=HIGH_PRIORITY_MODULES,
        help="List of high-priority modules to categorize first"
    )
    return parser.parse_args()

def collect_all_tests(use_cache=True):
    """Collect all tests."""
    return collect_tests(use_cache=use_cache)

def filter_tests_by_module(tests, module):
    """Filter tests by module."""
    return [test for test in tests if test.startswith(module)]

def filter_unmarked_tests(tests, use_cache=True):
    """Filter tests that don't have speed markers."""
    unmarked_tests = []
    for test in tests:
        has_marker, _ = check_test_has_marker(test, ["fast", "medium", "slow"])
        if not has_marker:
            unmarked_tests.append(test)
    return unmarked_tests

def create_schedule(tests, weeks, tests_per_day, priority_modules):
    """Create a schedule for categorizing tests."""
    # Calculate total days and tests per day
    total_days = weeks * 5  # 5 working days per week
    total_tests = len(tests)
    
    # Adjust tests per day if needed
    if total_tests > total_days * tests_per_day:
        tests_per_day = total_tests // total_days + 1
        print(f"Warning: Adjusted tests per day to {tests_per_day} to fit all tests in {total_days} days")
    
    # Create schedule
    schedule = {
        "created_at": datetime.now().isoformat(),
        "total_tests": total_tests,
        "total_days": total_days,
        "tests_per_day": tests_per_day,
        "priority_modules": priority_modules,
        "days": {}
    }
    
    # Organize tests by priority
    priority_tests = []
    for module in priority_modules:
        module_tests = filter_tests_by_module(tests, module)
        priority_tests.extend(module_tests)
        print(f"Found {len(module_tests)} tests in priority module {module}")
    
    # Remove duplicates while preserving order
    priority_tests = list(dict.fromkeys(priority_tests))
    
    # Get remaining tests
    remaining_tests = [test for test in tests if test not in priority_tests]
    
    # Combine priority tests and remaining tests
    all_tests = priority_tests + remaining_tests
    
    # Create daily schedules
    current_date = datetime.now().date()
    test_index = 0
    
    for day in range(1, total_days + 1):
        # Skip weekends
        while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            current_date += timedelta(days=1)
        
        # Calculate tests for this day
        day_tests = []
        for _ in range(tests_per_day):
            if test_index < len(all_tests):
                day_tests.append(all_tests[test_index])
                test_index += 1
            else:
                break
        
        # Add to schedule
        schedule["days"][current_date.isoformat()] = {
            "day": day,
            "tests": day_tests,
            "count": len(day_tests)
        }
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return schedule

def save_schedule(schedule, output_file):
    """Save the schedule to a file."""
    with open(output_file, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"Schedule saved to {output_file}")

def main():
    """Main function."""
    args = parse_args()
    
    # Collect all tests
    print("Collecting tests...")
    all_tests = collect_all_tests()
    print(f"Found {len(all_tests)} tests")
    
    # Filter unmarked tests
    print("Filtering unmarked tests...")
    unmarked_tests = filter_unmarked_tests(all_tests)
    print(f"Found {len(unmarked_tests)} unmarked tests")
    
    # Create schedule
    print("Creating schedule...")
    schedule = create_schedule(
        unmarked_tests,
        args.weeks,
        args.tests_per_day,
        args.priority_modules
    )
    
    # Save schedule
    save_schedule(schedule, args.output)
    
    # Print summary
    print("\nSchedule Summary:")
    print(f"Total tests to categorize: {schedule['total_tests']}")
    print(f"Total days: {schedule['total_days']}")
    print(f"Tests per day: {schedule['tests_per_day']}")
    print(f"Priority modules: {', '.join(schedule['priority_modules'])}")
    
    # Print first day's tests
    first_day = min(schedule["days"].keys())
    first_day_tests = schedule["days"][first_day]["tests"]
    print(f"\nFirst day ({first_day}) tests ({len(first_day_tests)}):")
    for test in first_day_tests[:5]:
        print(f"  {test}")
    if len(first_day_tests) > 5:
        print(f"  ... and {len(first_day_tests) - 5} more")

if __name__ == "__main__":
    main()