#!/usr/bin/env python3
"""
Add Missing Test Markers

This script identifies tests without speed markers, runs them to measure execution time,
and adds appropriate markers (fast, medium, slow) based on the execution time.

It addresses the issue of missing markers identified by fix_test_markers.py.

Usage:
    python scripts/add_missing_markers.py [options]

Options:
    --module MODULE       Specific module to process (e.g., tests/unit/interface)
    --category CATEGORY   Test category to process (unit, integration, behavior, all)
    --max-tests N         Maximum number of tests to process in a single run (default: 100)
    --batch-size N        Number of tests to run in a single batch (default: 10)
    --fast-threshold N    Threshold for fast tests in seconds (default: 1.0)
    --medium-threshold N  Threshold for medium tests in seconds (default: 5.0)
    --timeout N           Timeout for test execution in seconds (default: 60)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
    --no-cache            Don't use cached test collection results
    --no-cache-update     Don't update the test collection cache after modifying files
    --progress FILE       Progress file (default: .test_categorization_progress.json)
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
from typing import Any, Dict, List, Optional, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        check_test_has_marker,
        clear_cache,
        collect_tests,
        collect_tests_by_category,
        invalidate_cache_for_files,
    )
except ImportError:
    print(
        "Error: common_test_collector.py not found. Please ensure it exists in the scripts directory."
    )
    sys.exit(1)

    # Define dummy functions if import fails (for type checking)
    def invalidate_cache_for_files(file_paths, verbose=False):
        pass

    def clear_cache(selective=False):
        pass


# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}

# High-priority modules
HIGH_PRIORITY_MODULES = [
    "tests/unit/interface",
    "tests/unit/adapters/memory",
    "tests/unit/adapters/llm",
    "tests/integration/memory",
    "tests/unit/application/wsde",
    "tests/unit/interface/webui",
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Add missing test markers based on execution time."
    )
    parser.add_argument(
        "--module", help="Specific module to process (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to process (default: all)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=100,
        help="Maximum number of tests to process in a single run (default: 100)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of tests to run in a single batch (default: 10)",
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
        "--timeout",
        type=int,
        default=60,
        help="Timeout for test execution in seconds (default: 60)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached test collection results",
    )
    parser.add_argument(
        "--no-cache-update",
        action="store_true",
        help="Don't update the test collection cache after modifying files",
    )
    parser.add_argument(
        "--progress",
        default=".test_categorization_progress.json",
        help="Progress file (default: .test_categorization_progress.json)",
    )
    return parser.parse_args()


def load_progress(progress_file):
    """Load the test categorization progress."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading progress file: {e}")
            return {"tests": {}, "categorized_tests": {}, "last_date": None}
    return {"tests": {}, "categorized_tests": {}, "last_date": None}


def save_progress(progress, progress_file):
    """Save the test categorization progress."""
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Progress saved to {progress_file}")


def collect_unmarked_tests(
    category: str = "all", module: str = None, use_cache: bool = True
) -> list[str]:
    """
    Collect tests without speed markers.

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


def determine_speed_category(
    execution_time: float, fast_threshold: float, medium_threshold: float
) -> str:
    """
    Determine the speed category based on execution time.

    Args:
        execution_time: Test execution time in seconds
        fast_threshold: Threshold for fast tests in seconds
        medium_threshold: Threshold for medium tests in seconds

    Returns:
        Speed category (fast, medium, slow)
    """
    if execution_time < 0:
        # Error during execution, default to medium
        return "medium"
    elif execution_time <= fast_threshold:
        return "fast"
    elif execution_time <= medium_threshold:
        return "medium"
    else:
        return "slow"


def add_marker_to_file(
    file_path: str,
    test_name: str,
    marker: str,
    dry_run: bool = True,
    verbose: bool = False,
) -> tuple[bool, bool]:
    """
    Add a speed marker to a test file.

    Args:
        file_path: Path to the test file
        test_name: Name of the test function or method
        marker: Speed marker to add (fast, medium, slow)
        dry_run: Whether to show changes without modifying the file
        verbose: Whether to show detailed information

    Returns:
        Tuple of (success, file_modified) where:
        - success: Whether the operation was successful
        - file_modified: Whether the file was actually modified
    """
    try:
        with open(file_path) as f:
            content = f.read()

        # Check if the file already has pytest imported
        has_pytest_import = re.search(r"import\s+pytest", content) or re.search(
            r"from\s+pytest\s+import", content
        )

        # Find the test function or method
        if "::" in test_name:
            # Class method
            parts = test_name.split("::")
            class_name = parts[0]
            method_name = parts[1]

            # Find the class
            class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*[\(:]")
            class_match = class_pattern.search(content)

            if not class_match:
                print(f"Error: Class {class_name} not found in {file_path}")
                return False, False

            # Find the method within the class
            class_content = content[class_match.start() :]
            method_pattern = re.compile(rf"def\s+{re.escape(method_name)}\s*\(")
            method_match = method_pattern.search(class_content)

            if not method_match:
                print(
                    f"Error: Method {method_name} not found in class {class_name} in {file_path}"
                )
                return False, False

            # Calculate the position in the original content
            method_pos = class_match.start() + method_match.start()

            # Find the line before the method
            line_start = content.rfind("\n", 0, method_pos) + 1

            # Check if there's already a marker
            marker_line = content[line_start:method_pos].strip()
            if f"@pytest.mark.{marker}" in marker_line:
                if verbose:
                    print(f"Test {test_name} already has {marker} marker")
                return True, False  # Success but no modification

            # Insert the marker before the method
            new_content = (
                content[:line_start]
                + f"    @pytest.mark.{marker}\n"
                + content[line_start:]
            )
        else:
            # Regular function
            func_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
            func_match = func_pattern.search(content)

            if not func_match:
                print(f"Error: Function {test_name} not found in {file_path}")
                return False, False

            # Find the line before the function
            line_start = content.rfind("\n", 0, func_match.start()) + 1

            # Check if there's already a marker
            marker_line = content[line_start : func_match.start()].strip()
            if f"@pytest.mark.{marker}" in marker_line:
                if verbose:
                    print(f"Test {test_name} already has {marker} marker")
                return True, False  # Success but no modification

            # Insert the marker before the function
            new_content = (
                content[:line_start] + f"@pytest.mark.{marker}\n" + content[line_start:]
            )

        # Add pytest import if needed
        if not has_pytest_import:
            import_line = "import pytest\n\n"
            if content.startswith("#!/") or content.startswith("#!"):
                # Find the end of the shebang line
                shebang_end = content.find("\n") + 1
                new_content = (
                    content[:shebang_end] + "\n" + import_line + content[shebang_end:]
                )
            else:
                # Add at the beginning of the file
                new_content = import_line + content

        if verbose:
            print(f"Adding {marker} marker to {test_name} in {file_path}")

        if not dry_run:
            with open(file_path, "w") as f:
                f.write(new_content)

            if verbose:
                print(f"Updated {file_path}")

            return True, True  # Success and file modified
        else:
            # In dry run mode, we would have modified the file
            return True, True

    except Exception as e:
        print(f"Error updating test file {file_path}: {e}")
        return False, False


def update_progress(progress, test_path, marker, execution_time):
    """
    Update the progress file with test categorization results.

    Args:
        progress: Progress data
        test_path: Test path
        marker: Speed marker (fast, medium, slow)
        execution_time: Test execution time in seconds

    Returns:
        Updated progress data
    """
    # Update tests structure (for enhanced_test_categorization.py)
    if "tests" not in progress:
        progress["tests"] = {}

    progress["tests"][test_path] = {
        "marker": marker,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat(),
    }

    # Update categorized_tests structure (for execute_test_categorization.py)
    if "categorized_tests" not in progress:
        progress["categorized_tests"] = {}

    progress["categorized_tests"][test_path] = {
        "speed_category": marker,
        "execution_time": execution_time,
        "categorized_at": datetime.now().isoformat(),
    }

    # Update last_date
    progress["last_date"] = datetime.now().isoformat()

    # Update summary
    if "summary" not in progress:
        progress["summary"] = {"fast": 0, "medium": 0, "slow": 0, "total": 0}

    # Increment the appropriate counter
    progress["summary"][marker] = progress["summary"].get(marker, 0) + 1
    progress["summary"]["total"] = progress["summary"].get("total", 0) + 1

    return progress


def main():
    """Main function."""
    args = parse_args()

    # Collect unmarked tests
    unmarked_tests = collect_unmarked_tests(
        category=args.category, module=args.module, use_cache=not args.no_cache
    )

    # Prioritize tests
    unmarked_tests = prioritize_tests(unmarked_tests, HIGH_PRIORITY_MODULES)

    # Limit the number of tests to process
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

    # Load progress
    progress = load_progress(args.progress)

    # Process each batch
    total_processed = 0
    total_updated = 0
    modified_files = set()  # Track which files were modified

    for i, batch in enumerate(batches):
        print(f"\nProcessing batch {i+1}/{len(batches)} ({len(batch)} tests)...")

        # Run the batch
        batch_results = run_test_batch(batch, timeout=args.timeout)

        # Process results
        for test_path, execution_time in batch_results.items():
            # Determine the speed category
            marker = determine_speed_category(
                execution_time, args.fast_threshold, args.medium_threshold
            )

            # Extract file path and test name
            if "::" in test_path:
                parts = test_path.split("::")
                file_path = parts[0]
                if len(parts) > 2:  # Class-based test
                    class_name = parts[1]
                    test_name = parts[2]
                    # For class methods, we need to handle them differently
                    test_name = f"{class_name}::{test_name}"
                else:  # Function-based test
                    test_name = parts[1]
            else:
                file_path = test_path
                test_name = None

            # Add marker to file
            if test_name:
                success, file_modified = add_marker_to_file(
                    file_path,
                    test_name,
                    marker,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                )

                if success and file_modified:
                    total_updated += 1
                    if not args.dry_run:
                        modified_files.add(file_path)

            # Update progress
            if not args.dry_run:
                progress = update_progress(progress, test_path, marker, execution_time)

            total_processed += 1

    # Save progress
    if not args.dry_run:
        save_progress(progress, args.progress)

        # Invalidate cache for modified files
        if not args.no_cache_update and modified_files:
            print("\nInvalidating cache for modified files...")
            try:
                invalidate_cache_for_files(list(modified_files), args.verbose)
                print(f"Cache invalidated for {len(modified_files)} files")
            except Exception as e:
                print(f"Error invalidating cache: {e}")
                print(
                    "You may need to manually clear the cache with: python -m pytest --cache-clear"
                )

    # Print summary
    print("\nSummary:")
    print(f"  Total tests processed: {total_processed}")
    print(f"  Total files updated: {total_updated}")

    if args.dry_run:
        print("\nNote: This was a dry run. Use without --dry-run to apply changes.")
    else:
        print(f"  Files modified: {len(modified_files)}")

    print("\nDone!")


if __name__ == "__main__":
    main()
