#!/usr/bin/env python
"""
Script to run tests for modified files based on git diff.

This script identifies modified files using git diff, determines which tests
might be affected by those changes, and runs only those tests. This can
significantly improve test performance during development by focusing on
tests that are likely to be affected by recent changes.

Usage:
    python scripts/run_modified_tests.py [options]

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
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Mapping of source files to test files
# This will be populated based on import statements and module references
SOURCE_TO_TEST_MAP = {}

# Cache directory for dependency mapping
CACHE_DIR = ".test_dependency_cache"


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


def find_imports_in_file(file_path: str) -> set[str]:
    """
    Find all import statements in a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        Set of imported module names
    """
    if not os.path.exists(file_path) or not file_path.endswith(".py"):
        return set()

    imports = set()
    import_pattern = re.compile(r"^\s*(?:from|import)\s+([.\w]+)")

    try:
        with open(file_path) as f:
            for line in f:
                match = import_pattern.match(line)
                if match:
                    module = match.group(1)
                    # Handle relative imports
                    if module.startswith("."):
                        # Get the package name from the file path
                        package_parts = (
                            file_path.replace("/", ".").replace("\\", ".").split(".")
                        )
                        if len(package_parts) > 1:
                            package = ".".join(package_parts[:-1])
                            # Remove leading dots and combine with package
                            relative_module = module.lstrip(".")
                            if relative_module:
                                module = f"{package}.{relative_module}"
                            else:
                                module = package

                    imports.add(module)

        return imports
    except Exception as e:
        print(f"Error finding imports in {file_path}: {e}")
        return set()


def build_dependency_map(src_dir: str, test_dir: str) -> dict[str, set[str]]:
    """
    Build a map of source files to test files based on imports.

    Args:
        src_dir: Directory containing source code
        test_dir: Directory containing tests

    Returns:
        Dictionary mapping source files to sets of test files
    """
    # Check if we have a cached dependency map
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, "dependency_map.txt")

    if os.path.exists(cache_file):
        # Check if the cache is still valid
        src_mtime = max(
            os.path.getmtime(path)
            for path, _, _ in os.walk(src_dir)
            for path in Path(path).glob("*.py")
        )
        test_mtime = max(
            os.path.getmtime(path)
            for path, _, _ in os.walk(test_dir)
            for path in Path(path).glob("*.py")
        )
        cache_mtime = os.path.getmtime(cache_file)

        if cache_mtime > src_mtime and cache_mtime > test_mtime:
            # Cache is still valid, load it
            dependency_map = {}
            with open(cache_file) as f:
                for line in f:
                    parts = line.strip().split(" -> ")
                    if len(parts) == 2:
                        source_file, test_files = parts
                        dependency_map[source_file] = set(test_files.split(","))

            return dependency_map

    # Build the dependency map
    dependency_map = {}

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
    for src_file in src_files:
        dependency_map[src_file] = set()

    # For each test file, find its imports and map them to source files
    for test_file in test_files:
        imports = find_imports_in_file(test_file)

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

    # Save the dependency map to cache
    with open(cache_file, "w") as f:
        for src_file, test_files in dependency_map.items():
            if test_files:
                f.write(f"{src_file} -> {','.join(test_files)}\n")

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


def run_tests(affected_tests: set[str], args) -> int:
    """
    Run the affected tests.

    Args:
        affected_tests: Set of affected test file paths
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not affected_tests:
        print("No affected tests found.")
        return 0

    print(f"Running {len(affected_tests)} affected tests...")

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

    print(f"Found {len(affected_tests)} affected tests:")
    for test in affected_tests:
        print(f"  {test}")

    # Run the tests
    print("\nRunning affected tests...")
    return run_tests(affected_tests, args)


if __name__ == "__main__":
    sys.exit(main())
