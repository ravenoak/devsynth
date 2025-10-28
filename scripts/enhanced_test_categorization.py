#!/usr/bin/env python3
"""
Enhanced Test Categorization Script

This script enhances the test categorization process by:
1. Identifying unmarked tests and measuring their execution time
2. Categorizing tests as fast, medium, or slow based on execution time
3. Adding appropriate markers to test files with improved placement
4. Tracking progress and generating reports
5. Integrating with fix_test_markers.py to ensure correct marker placement
6. Supporting incremental categorization with prioritization

Usage:
    python scripts/enhanced_test_categorization.py [options]

Options:
    --module MODULE       Specific module to categorize (e.g., tests/unit/interface)
    --category CATEGORY   Test category to categorize (unit, integration, behavior, all)
    --max-tests N         Maximum number of tests to categorize in a single run
    --batch-size N        Number of tests to run in a single batch
    --priority            Prioritize high-priority modules
    --force               Force recategorization of tests, even if already categorized
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
    --fix-markers         Fix marker placement issues after categorization
    --report              Generate a categorization report
    --update              Update test files with markers (default is dry-run)
    --no-cache            Don't use cached test collection results
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
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        check_test_has_marker,
        collect_tests,
        collect_tests_by_category,
        get_marker_counts,
        get_test_counts,
    )
except ImportError:
    print(
        "Error: common_test_collector.py not found. Please ensure it exists in the scripts directory."
    )
    sys.exit(1)

# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}

# Speed thresholds (in seconds)
FAST_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 5.0

# Progress file
PROGRESS_FILE = Path(".test_categorization_progress.json")

# High-priority modules
HIGH_PRIORITY_MODULES = [
    "tests/unit/application/cli",
    "tests/unit/adapters/memory",
    "tests/unit/adapters/llm",
    "tests/integration/memory",
    "tests/unit/application/wsde",
    "tests/unit/interface/webui",
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced test categorization script.")
    parser.add_argument(
        "--module", help="Specific module to categorize (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to categorize (default: all)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=50,
        help="Maximum number of tests to categorize in a single run (default: 50)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tests to run in a single batch (default: 10)",
    )
    parser.add_argument(
        "--priority", action="store_true", help="Prioritize high-priority modules"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recategorization of tests, even if already categorized",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--fix-markers",
        action="store_true",
        help="Fix marker placement issues after categorization",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a categorization report"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update test files with markers (default is dry-run)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached test collection results",
    )
    return parser.parse_args()


def load_progress():
    """Load categorization progress from file."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading progress file: {e}")
            return {"tests": {}}
    return {"tests": {}}


def save_progress(progress):
    """Save categorization progress to file."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def collect_unmarked_tests(
    category: str = "all", module: str = None, use_cache: bool = True
) -> list[str]:
    """
    Collect unmarked tests.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to collect tests from
        use_cache: Whether to use cached test collection results

    Returns:
        List of unmarked test paths
    """
    print("Collecting unmarked tests...")

    # Determine which categories to collect
    categories = [category] if category != "all" else list(TEST_CATEGORIES.keys())

    # Collect all tests
    all_tests = []
    for cat in categories:
        if module:
            # If module is specified, collect tests from that module
            if os.path.exists(module):
                tests = collect_tests_by_category(cat, use_cache=use_cache)
                tests = [t for t in tests if t.startswith(module)]
                all_tests.extend(tests)
        else:
            # Otherwise, collect all tests for the category
            tests = collect_tests_by_category(cat, use_cache=use_cache)
            all_tests.extend(tests)

    # Filter out tests that already have markers
    unmarked_tests = []
    for test in all_tests:
        has_marker, _ = check_test_has_marker(test)
        if not has_marker:
            unmarked_tests.append(test)

    print(
        f"Found {len(unmarked_tests)} unmarked tests out of {len(all_tests)} total tests"
    )
    return unmarked_tests


def prioritize_tests(tests: list[str], priority_modules: list[str]) -> list[str]:
    """
    Prioritize tests based on module priority.

    Args:
        tests: List of test paths
        priority_modules: List of high-priority modules

    Returns:
        Prioritized list of test paths
    """
    high_priority = []
    normal_priority = []

    for test in tests:
        if any(test.startswith(module) for module in priority_modules):
            high_priority.append(test)
        else:
            normal_priority.append(test)

    return high_priority + normal_priority


def run_test_batch(batch: list[str], timeout: int = 60) -> dict[str, float]:
    """
    Run a batch of tests and measure execution time.

    Args:
        batch: List of tests to run
        timeout: Timeout in seconds

    Returns:
        Dictionary mapping test paths to execution times
    """
    results = {}

    for test in batch:
        print(f"Running test: {test}")

        # Build the pytest command
        cmd = [sys.executable, "-m", "pytest", test, "-v"]

        # Run the test and measure execution time
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            execution_time = time.time() - start_time

            # Store the result
            results[test] = execution_time

            # Print result
            status = "PASSED" if result.returncode == 0 else "FAILED"
            print(f"  {status} in {execution_time:.2f}s")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT after {timeout}s")
            results[test] = timeout
        except Exception as e:
            print(f"  ERROR: {e}")
            results[test] = -1

    return results


def determine_speed_category(execution_time: float) -> str:
    """
    Determine the speed category based on execution time.

    Args:
        execution_time: Test execution time in seconds

    Returns:
        Speed category (fast, medium, slow)
    """
    if execution_time < 0:
        # Error during execution, default to medium
        return "medium"
    elif execution_time < FAST_THRESHOLD:
        return "fast"
    elif execution_time < MEDIUM_THRESHOLD:
        return "medium"
    else:
        return "slow"


def update_test_file(
    file_path: str,
    test_name: str,
    marker: str,
    dry_run: bool = True,
    verbose: bool = False,
) -> bool:
    """
    Update a test file with a speed marker.

    Args:
        file_path: Path to the test file
        test_name: Name of the test function
        marker: Speed marker to add (fast, medium, slow)
        dry_run: Whether to show changes without modifying the file
        verbose: Whether to show detailed information

    Returns:
        Whether the update was successful
    """
    try:
        with open(file_path) as f:
            lines = f.readlines()

        # Find the test function
        test_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
        test_line = -1

        for i, line in enumerate(lines):
            if test_pattern.search(line):
                test_line = i
                break

        if test_line == -1:
            print(f"Error: Test function {test_name} not found in {file_path}")
            return False

        # Check if pytest is imported
        has_pytest_import = False
        for line in lines:
            if re.search(r"import\s+pytest", line) or re.search(
                r"from\s+pytest\s+import", line
            ):
                has_pytest_import = True
                break

        # Add pytest import if needed
        if not has_pytest_import:
            # Find the last import line
            last_import_line = -1
            for i, line in enumerate(lines):
                if re.search(r"import\s+\w+|from\s+\w+\s+import", line):
                    last_import_line = i

            # Add pytest import after the last import
            if last_import_line != -1:
                lines.insert(last_import_line + 1, "import pytest\n")
                # Adjust test_line if it's after the import
                if test_line > last_import_line:
                    test_line += 1
            else:
                # Add pytest import at the beginning of the file
                lines.insert(0, "import pytest\n\n")
                test_line += 1

        # Check if the test already has a speed marker
        has_marker = False
        for i in range(max(0, test_line - 5), test_line):
            if re.search(rf"@pytest\.mark\.(fast|medium|slow)", lines[i]):
                has_marker = True
                break

        if has_marker:
            if verbose:
                print(f"Test {test_name} in {file_path} already has a speed marker")
            return False

        # Add the marker before the test function
        marker_line = f"@pytest.mark.{marker}\n"
        lines.insert(test_line, marker_line)

        if verbose:
            print(f"Adding {marker} marker to {test_name} in {file_path}")

        if not dry_run:
            with open(file_path, "w") as f:
                f.writelines(lines)

            if verbose:
                print(f"Updated {file_path}")

        return True
    except Exception as e:
        print(f"Error updating test file {file_path}: {e}")
        return False


def fix_marker_placement(
    module: str = None, dry_run: bool = True, verbose: bool = False
):
    """
    Fix marker placement issues using fix_test_markers.py.

    Args:
        module: Specific module to fix
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information
    """
    print("Fixing marker placement issues...")

    # Build the command
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_test_markers.py"),
        "--fix-all",
    ]

    if module:
        cmd.extend(["--module", module])

    if dry_run:
        cmd.append("--dry-run")

    if verbose:
        cmd.append("--verbose")

    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error fixing marker placement: {e}")
    except FileNotFoundError:
        print(
            "Error: fix_test_markers.py not found. Please ensure it exists in the scripts directory."
        )


def generate_report(
    results: dict[str, dict[str, Any]],
    output_file: str = "test_categorization_report.json",
):
    """
    Generate a categorization report.

    Args:
        results: Dictionary mapping test paths to categorization results
        output_file: Path to the output file
    """
    print("Generating categorization report...")

    # Calculate summary statistics
    total_tests = len(results)
    categorized_tests = sum(1 for result in results.values() if result.get("marker"))

    category_counts = {
        "fast": sum(1 for result in results.values() if result.get("marker") == "fast"),
        "medium": sum(
            1 for result in results.values() if result.get("marker") == "medium"
        ),
        "slow": sum(1 for result in results.values() if result.get("marker") == "slow"),
    }

    # Create the report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "categorized_tests": categorized_tests,
            "category_counts": category_counts,
        },
        "results": results,
    }

    # Write the report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Categorized tests: {categorized_tests}")
    print(f"  Fast tests: {category_counts['fast']}")
    print(f"  Medium tests: {category_counts['medium']}")
    print(f"  Slow tests: {category_counts['slow']}")


def update_progress_file(results: dict[str, dict[str, Any]]):
    """
    Update the progress file with categorization results.

    Args:
        results: Dictionary mapping test paths to categorization results
    """
    print("Updating progress file...")

    # Load existing progress
    progress = load_progress()

    # Update with new results
    for test_path, result in results.items():
        if "marker" in result:
            progress["tests"][test_path] = {
                "marker": result["marker"],
                "execution_time": result["execution_time"],
                "timestamp": datetime.now().isoformat(),
            }

    # Save updated progress
    save_progress(progress)

    print(f"Progress file updated: {PROGRESS_FILE}")


def main():
    """Main function."""
    args = parse_args()

    # Collect unmarked tests
    unmarked_tests = collect_unmarked_tests(
        category=args.category, module=args.module, use_cache=not args.no_cache
    )

    # Load existing progress
    progress = load_progress()

    # Filter out tests that have already been categorized (unless --force is specified)
    if not args.force:
        unmarked_tests = [t for t in unmarked_tests if t not in progress["tests"]]

    # Prioritize tests if requested
    if args.priority:
        unmarked_tests = prioritize_tests(unmarked_tests, HIGH_PRIORITY_MODULES)

    # Limit the number of tests to categorize
    if args.max_tests > 0 and len(unmarked_tests) > args.max_tests:
        print(
            f"Limiting to {args.max_tests} tests (out of {len(unmarked_tests)} unmarked tests)"
        )
        unmarked_tests = unmarked_tests[: args.max_tests]

    # Create batches of tests
    batches = [
        unmarked_tests[i : i + args.batch_size]
        for i in range(0, len(unmarked_tests), args.batch_size)
    ]

    # Run tests and categorize them
    results = {}

    for i, batch in enumerate(batches):
        print(f"\nProcessing batch {i+1}/{len(batches)} ({len(batch)} tests)...")

        # Run the batch
        batch_results = run_test_batch(batch, timeout=60)

        # Categorize tests
        for test_path, execution_time in batch_results.items():
            # Determine the speed category
            marker = determine_speed_category(execution_time)

            # Extract file path and test name
            if "::" in test_path:
                parts = test_path.split("::")
                file_path = parts[0]
                if len(parts) > 2:  # Class-based test
                    class_name = parts[1]
                    test_name = parts[2]
                    full_test_name = f"{class_name}.{test_name}"
                else:  # Function-based test
                    test_name = parts[1]
                    full_test_name = test_name
            else:
                file_path = test_path
                test_name = None
                full_test_name = None

            # Update the test file
            updated = False
            if test_name:
                updated = update_test_file(
                    file_path,
                    test_name,
                    marker,
                    dry_run=not args.update,
                    verbose=args.verbose,
                )

            # Store the result
            results[test_path] = {
                "file_path": file_path,
                "test_name": full_test_name,
                "execution_time": execution_time,
                "marker": marker,
                "updated": updated,
            }

    # Fix marker placement if requested
    if args.fix_markers and args.update:
        fix_marker_placement(
            module=args.module, dry_run=not args.update, verbose=args.verbose
        )

    # Generate report if requested
    if args.report:
        generate_report(results)

    # Update progress file if not in dry-run mode
    if args.update:
        update_progress_file(results)

    # Print summary
    print("\nSummary:")
    print(f"  Total tests processed: {len(results)}")
    print(f"  Fast tests: {sum(1 for r in results.values() if r['marker'] == 'fast')}")
    print(
        f"  Medium tests: {sum(1 for r in results.values() if r['marker'] == 'medium')}"
    )
    print(f"  Slow tests: {sum(1 for r in results.values() if r['marker'] == 'slow')}")
    print(f"  Files updated: {sum(1 for r in results.values() if r['updated'])}")

    if not args.update:
        print("\nNote: This was a dry run. Use --update to apply changes.")

    print("\nDone!")


if __name__ == "__main__":
    main()
