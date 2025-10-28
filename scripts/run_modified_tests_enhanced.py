#!/usr/bin/env python
"""
Enhanced script to run tests for modified files based on git diff.

This script identifies modified files using git diff, determines which tests
might be affected by those changes, and runs only those tests. It integrates
with test_utils_extended.py for more accurate test collection and marker
verification, and uses test history to prioritize tests that failed recently.

Usage:
    python scripts/run_modified_tests_enhanced.py [options]

Options:
    --base COMMIT       Base commit to compare against (default: HEAD~1)
    --test-dir DIR      Directory containing tests (default: tests)
    --src-dir DIR       Directory containing source code (default: src)
    --all-tests         Run all tests for modified files, not just affected tests
    --verbose           Show verbose output
    --parallel          Run tests in parallel using pytest-xdist
    --report            Generate HTML report
    --fast              Run only fast tests
    --medium            Run only medium tests
    --slow              Run only slow tests
    --prioritize        Prioritize tests based on failure history
    --balanced          Use balanced distribution for parallel execution
    --max-tests N       Maximum number of tests to run (default: all)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import test utilities
try:
    from . import common_test_collector, test_utils, test_utils_extended

    EXTENDED_UTILS_AVAILABLE = True
except ImportError:
    print("Warning: test_utils_extended.py not found. Using original implementation.")
    from . import common_test_collector, test_utils

    EXTENDED_UTILS_AVAILABLE = False

# Cache directory for dependency mapping
CACHE_DIR = ".test_dependency_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests for modified files based on git diff."
    )
    parser.add_argument(
        "--base",
        default="HEAD~1",
        help="Base commit to compare against (default: HEAD~1)",
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests (default: tests)",
    )
    parser.add_argument(
        "--src-dir",
        default="src",
        help="Directory containing source code (default: src)",
    )
    parser.add_argument(
        "--all-tests",
        action="store_true",
        help="Run all tests for modified files, not just affected tests",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument("--medium", action="store_true", help="Run only medium tests")
    parser.add_argument("--slow", action="store_true", help="Run only slow tests")
    parser.add_argument(
        "--prioritize",
        action="store_true",
        help="Prioritize tests based on failure history",
    )
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="Use balanced distribution for parallel execution",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=0,
        help="Maximum number of tests to run (default: all)",
    )
    return parser.parse_args()


def get_modified_files(base_commit: str) -> list[str]:
    """
    Get list of modified files compared to the base commit.

    Args:
        base_commit: Base commit to compare against

    Returns:
        List of modified file paths
    """
    try:
        # Get the list of modified files
        cmd = ["git", "diff", "--name-only", base_commit]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Filter out non-Python files and files that don't exist
        modified_files = []
        for file_path in result.stdout.strip().split("\n"):
            if file_path and (
                file_path.endswith(".py") or file_path.endswith(".feature")
            ):
                if os.path.exists(file_path):
                    modified_files.append(file_path)

        return modified_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting modified files: {e}")
        return []


def build_dependency_map(
    src_dir: str, test_dir: str, use_cache: bool = True
) -> dict[str, set[str]]:
    """
    Build a map of source files to test files based on imports and AST analysis.

    Args:
        src_dir: Directory containing source code
        test_dir: Directory containing tests
        use_cache: Whether to use cached dependency map

    Returns:
        Dictionary mapping source files to sets of test files
    """
    # Check if we have a cached dependency map
    cache_file = os.path.join(CACHE_DIR, "dependency_map.json")

    if use_cache and os.path.exists(cache_file):
        # Check if the cache is still valid
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)

            # Use cache if it's less than 1 hour old
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                print(f"Using cached dependency map (less than 1 hour old)")

                # Convert string keys to sets
                dependency_map = {}
                for src_file, test_files in cache_data["dependency_map"].items():
                    dependency_map[src_file] = set(test_files)

                return dependency_map
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache, ignore and build dependency map
            pass

    print("Building dependency map...")

    # Use common_test_collector to analyze test dependencies if available
    if hasattr(common_test_collector, "analyze_test_dependencies"):
        # Collect all tests
        all_tests = common_test_collector.collect_tests(use_cache=True)

        # Analyze dependencies
        dependencies = common_test_collector.analyze_test_dependencies(
            all_tests, use_cache=True
        )

        # Invert the dependencies to get source -> test mapping
        dependency_map = {}
        for test_path, deps in dependencies.items():
            for dep in deps:
                if dep not in dependency_map:
                    dependency_map[dep] = set()
                dependency_map[dep].add(test_path)

        # Cache the dependency map
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "dependency_map": {
                src: list(tests) for src, tests in dependency_map.items()
            },
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        return dependency_map

    # Fallback to original implementation
    print("Using fallback dependency mapping")

    # Find all Python files in the source directory
    src_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                src_files.append(os.path.join(root, file))

    # Find all test files
    test_files = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    # Initialize the dependency map
    dependency_map = {}
    for src_file in src_files:
        dependency_map[src_file] = set()

    # For each test file, find its imports and map them to source files
    for test_file in test_files:
        # Use common_test_collector to find imports if available
        if hasattr(common_test_collector, "find_imports_in_file"):
            imports = common_test_collector.find_imports_in_file(test_file)
        else:
            # Fallback to simple regex-based import detection
            imports = set()
            import_pattern = re.compile(r"^\s*(?:from|import)\s+([.\w]+)")

            try:
                with open(test_file) as f:
                    for line in f:
                        match = import_pattern.match(line)
                        if match:
                            imports.add(match.group(1))
            except Exception as e:
                print(f"Error finding imports in {test_file}: {e}")

        for src_file in src_files:
            # Convert source file path to module name
            src_module = (
                src_file.replace("/", ".").replace("\\", ".").replace(".py", "")
            )

            # Check if the test imports this source file
            for imp in imports:
                if imp in src_module or src_module in imp:
                    dependency_map[src_file].add(test_file)
                    break

    # Cache the dependency map
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "dependency_map": {src: list(tests) for src, tests in dependency_map.items()},
    }
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2)

    return dependency_map


def find_affected_tests(
    modified_files: list[str],
    dependency_map: dict[str, set[str]],
    all_tests: bool = False,
) -> set[str]:
    """
    Find tests affected by modified files.

    Args:
        modified_files: List of modified file paths
        dependency_map: Dictionary mapping source files to test files
        all_tests: Whether to include all tests for modified test files

    Returns:
        Set of affected test file paths
    """
    affected_tests = set()

    for file_path in modified_files:
        if file_path.startswith("tests/") and file_path.endswith(".py"):
            # Modified test file
            if all_tests:
                # Include the entire test file
                affected_tests.add(file_path)
            else:
                # Try to find specific test functions that were modified
                try:
                    # Get the diff for this file
                    cmd = ["git", "diff", file_path]
                    result = subprocess.run(
                        cmd, check=True, capture_output=True, text=True
                    )

                    # Find modified test functions
                    test_func_pattern = re.compile(r"^\+\s*def\s+(test_\w+)")
                    for line in result.stdout.split("\n"):
                        match = test_func_pattern.match(line)
                        if match:
                            test_func = match.group(1)
                            affected_tests.add(f"{file_path}::{test_func}")
                except subprocess.CalledProcessError:
                    # Fall back to including the entire test file
                    affected_tests.add(file_path)
        elif file_path in dependency_map:
            # Modified source file
            affected_tests.update(dependency_map[file_path])

    return affected_tests


def prioritize_tests(tests: set[str], args) -> list[str]:
    """
    Prioritize tests based on various criteria.

    Args:
        tests: Set of test paths
        args: Command-line arguments

    Returns:
        List of test paths, sorted by priority
    """
    # Convert to list for sorting
    test_list = list(tests)

    # Apply speed filters if specified
    if args.fast or args.medium or args.slow:
        filtered_tests = []
        markers = []
        if args.fast:
            markers.append("fast")
        if args.medium:
            markers.append("medium")
        if args.slow:
            markers.append("slow")

        # Get tests with the specified markers
        if EXTENDED_UTILS_AVAILABLE:
            # Use test_utils_extended for more accurate marker detection
            for test in test_list:
                has_marker, marker = test_utils_extended.check_test_has_marker(test)
                if has_marker and marker in markers:
                    filtered_tests.append(test)
        else:
            # Use common_test_collector
            tests_with_markers = common_test_collector.get_tests_with_markers(markers)

            for test in test_list:
                # Extract category from test path
                category = None
                for cat, path in common_test_collector.TEST_CATEGORIES.items():
                    if test.startswith(path):
                        category = cat
                        break

                if category:
                    # Check if test has any of the specified markers
                    for marker in markers:
                        if (
                            marker in tests_with_markers.get(category, {})
                            and test in tests_with_markers[category][marker]
                        ):
                            filtered_tests.append(test)
                            break

        test_list = filtered_tests

    # Prioritize based on failure history if requested
    if args.prioritize and hasattr(common_test_collector, "get_test_failure_rates"):
        # Get test failure rates
        failure_rates = common_test_collector.get_test_failure_rates()

        # Sort tests by failure rate (descending)
        test_list.sort(key=lambda t: failure_rates.get(t, 0.0), reverse=True)

    # Limit the number of tests if specified
    if args.max_tests > 0 and len(test_list) > args.max_tests:
        print(f"Limiting to {args.max_tests} tests (out of {len(test_list)})")
        test_list = test_list[: args.max_tests]

    return test_list


def run_tests(affected_tests: list[str], args) -> int:
    """
    Run the affected tests.

    Args:
        affected_tests: List of affected test file paths
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not affected_tests:
        print("No affected tests found.")
        return 0

    print(f"Running {len(affected_tests)} affected tests...")

    # Use balanced distribution if requested
    if args.balanced and args.parallel and hasattr(test_utils, "distribute_tests"):
        # Get test execution times
        test_times = {}
        for test in affected_tests:
            execution_time, _, _ = test_utils.measure_test_time(test, use_cache=True)
            test_times[test] = execution_time

        # Distribute tests across processes
        num_processes = os.cpu_count() or 4
        test_bins = test_utils.distribute_tests(
            affected_tests, test_times, num_processes
        )

        # Run tests in parallel
        return test_utils.run_tests_in_parallel(test_bins, args)

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest", "--maxfail=1"]
    cmd.extend(affected_tests)

    # Add options based on command-line arguments
    if args.verbose:
        cmd.append("-v")

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Add speed markers if specified
    markers = []
    if args.fast:
        markers.append("fast")
    if args.medium:
        markers.append("medium")
    if args.slow:
        markers.append("slow")

    if markers:
        cmd.extend(["-m", " or ".join(markers)])

    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    # Record test results if common_test_collector has the function
    if hasattr(common_test_collector, "record_test_run") and result.returncode != 0:
        print("Recording test results for future prioritization...")
        # We don't have detailed results, so we'll just record failures
        test_results = {test: False for test in affected_tests}
        common_test_collector.record_test_run(test_results)

    return result.returncode


def main():
    """Main function."""
    args = parse_args()

    # Get modified files
    print(f"Getting modified files compared to {args.base}...")
    modified_files = get_modified_files(args.base)

    if not modified_files:
        print("No modified files found.")
        return 0

    print(f"Found {len(modified_files)} modified files:")
    for file in modified_files:
        print(f"  {file}")

    # Build dependency map
    print("\nBuilding dependency map...")
    dependency_map = build_dependency_map(args.src_dir, args.test_dir)

    # Find affected tests
    print("\nFinding affected tests...")
    affected_tests = find_affected_tests(modified_files, dependency_map, args.all_tests)

    if not affected_tests:
        print("No affected tests found.")
        return 0

    print(f"Found {len(affected_tests)} affected tests")

    # Prioritize tests
    print("\nPrioritizing tests...")
    prioritized_tests = prioritize_tests(affected_tests, args)

    if args.verbose:
        print("Tests to run:")
        for test in prioritized_tests:
            print(f"  {test}")

    # Run the tests
    print("\nRunning affected tests...")
    return run_tests(prioritized_tests, args)


if __name__ == "__main__":
    sys.exit(main())
