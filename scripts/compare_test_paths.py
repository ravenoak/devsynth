#!/usr/bin/env python3
"""
Compare Test Paths

This script compares test paths from enhanced_test_parser.py and pytest to identify
formatting differences that might cause comparison issues.
"""

import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Set

# Import enhanced_test_parser if available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import enhanced_test_parser
except ImportError:
    print("Warning: enhanced_test_parser.py not found, using basic implementation")
    enhanced_test_parser = None


def get_parser_test_paths(directory: str, include_file_only: bool = True) -> list[str]:
    """
    Get test paths using enhanced_test_parser.

    Args:
        directory: Directory to collect tests from
        include_file_only: Whether to include file-only paths

    Returns:
        List of test paths
    """
    if enhanced_test_parser:
        return enhanced_test_parser.get_test_paths_from_directory(
            directory, use_cache=False, include_file_only=include_file_only
        )
    else:
        # Basic implementation if enhanced_test_parser is not available
        tests = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    tests.append(file_path)
        return tests


def get_pytest_test_paths(directory: str) -> list[str]:
    """
    Get test paths using pytest.

    Args:
        directory: Directory to collect tests from

    Returns:
        List of test paths
    """
    cmd = [sys.executable, "-m", "pytest", directory, "--collect-only", "-q"]

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Extract test paths from output
        pytest_tests = []
        for line in result.stdout.split("\n"):
            if line.strip() and not line.startswith("="):
                pytest_tests.append(line.strip())

        return pytest_tests
    except Exception as e:
        print(f"Error collecting tests with pytest: {e}")
        return []


def normalize_test_path(test_path: str) -> str:
    """
    Normalize a test path for better comparison.

    Args:
        test_path: Test path to normalize

    Returns:
        Normalized test path
    """
    # Remove any leading './' or '../'
    path = re.sub(r"^\.\.?/", "", test_path)

    # Ensure consistent path separators
    path = path.replace("\\", "/")

    # Remove any trailing whitespace
    path = path.strip()

    return path


def analyze_path_differences(
    parser_tests: list[str], pytest_tests: list[str]
) -> dict[str, Any]:
    """
    Analyze differences between parser and pytest test paths.

    Args:
        parser_tests: List of test paths from parser
        pytest_tests: List of test paths from pytest

    Returns:
        Dictionary with analysis results
    """
    # Print sample test paths
    print("\nSample parser test paths:")
    for test in parser_tests[:5]:
        print(f"  {test}")

    print("\nSample pytest test paths:")
    for test in pytest_tests[:5]:
        print(f"  {test}")

    # Normalize test paths
    normalized_parser_tests = [normalize_test_path(test) for test in parser_tests]
    normalized_pytest_tests = [normalize_test_path(test) for test in pytest_tests]

    # Compare results using normalized paths
    parser_set = set(normalized_parser_tests)
    pytest_set = set(normalized_pytest_tests)

    only_in_parser = parser_set - pytest_set
    only_in_pytest = pytest_set - parser_set
    common = parser_set.intersection(pytest_set)

    print(f"\nBefore normalization:")
    print(f"  Parser count: {len(parser_tests)}")
    print(f"  Pytest count: {len(pytest_tests)}")
    print(f"  Common count: {len(set(parser_tests).intersection(set(pytest_tests)))}")

    print(f"\nAfter normalization:")
    print(f"  Parser count: {len(normalized_parser_tests)}")
    print(f"  Pytest count: {len(normalized_pytest_tests)}")
    print(f"  Common count: {len(common)}")
    print(f"  Only in parser: {len(only_in_parser)}")
    print(f"  Only in pytest: {len(only_in_pytest)}")

    # Analyze path patterns
    parser_patterns = analyze_path_patterns(parser_tests)
    pytest_patterns = analyze_path_patterns(pytest_tests)

    print("\nParser path patterns:")
    for pattern, count in parser_patterns.items():
        print(f"  {pattern}: {count}")

    print("\nPytest path patterns:")
    for pattern, count in pytest_patterns.items():
        print(f"  {pattern}: {count}")

    # Extract file-only paths for detailed comparison
    parser_file_only = [test for test in parser_tests if "::" not in test]
    pytest_file_only = [test for test in pytest_tests if "::" not in test]

    # Find common and unique file-only paths
    parser_file_only_set = set(parser_file_only)
    pytest_file_only_set = set(pytest_file_only)
    common_file_only = parser_file_only_set.intersection(pytest_file_only_set)
    only_in_parser_file_only = parser_file_only_set - pytest_file_only_set
    only_in_pytest_file_only = pytest_file_only_set - parser_file_only_set

    print("\nFile-only path comparison:")
    print(f"  Parser file-only count: {len(parser_file_only)}")
    print(f"  Pytest file-only count: {len(pytest_file_only)}")
    print(f"  Common file-only count: {len(common_file_only)}")
    print(f"  Only in parser file-only: {len(only_in_parser_file_only)}")
    print(f"  Only in pytest file-only: {len(only_in_pytest_file_only)}")

    # Print sample file-only paths
    print("\nSample parser file-only paths:")
    for test in parser_file_only[:5]:
        print(f"  {test}")

    print("\nSample pytest file-only paths:")
    for test in pytest_file_only[:5]:
        print(f"  {test}")

    return {
        "parser_count": len(parser_tests),
        "pytest_count": len(pytest_tests),
        "common_count": len(common),
        "only_in_parser_count": len(only_in_parser),
        "only_in_pytest_count": len(only_in_pytest),
        "parser_patterns": parser_patterns,
        "pytest_patterns": pytest_patterns,
        "parser_file_only_count": len(parser_file_only),
        "pytest_file_only_count": len(pytest_file_only),
        "common_file_only_count": len(common_file_only),
    }


def analyze_path_patterns(test_paths: list[str]) -> dict[str, int]:
    """
    Analyze patterns in test paths.

    Args:
        test_paths: List of test paths

    Returns:
        Dictionary mapping patterns to counts
    """
    patterns = {}

    for path in test_paths:
        # Check if path contains ::
        if "::" in path:
            parts = path.split("::")
            if len(parts) == 2:
                pattern = "file::function"
            elif len(parts) == 3:
                pattern = "file::class::method"
            else:
                pattern = f"file::{len(parts)-1}_parts"
        else:
            pattern = "file_only"

        patterns[pattern] = patterns.get(pattern, 0) + 1

    return patterns


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare test paths from enhanced_test_parser.py and pytest."
    )
    parser.add_argument(
        "--directory",
        default="tests/unit/application/memory",
        help="Directory to collect tests from",
    )
    parser.add_argument(
        "--no-file-only",
        action="store_true",
        help="Don't include file-only paths in parser output",
    )

    args = parser.parse_args()

    print(f"Comparing test paths for {args.directory}...")

    # Get pytest test paths
    pytest_tests = get_pytest_test_paths(args.directory)

    # Run comparison with default settings (including file-only paths)
    if not args.no_file_only:
        print("\n=== WITH FILE-ONLY PATHS ===")
        parser_tests = get_parser_test_paths(args.directory, include_file_only=True)
        results = analyze_path_differences(parser_tests, pytest_tests)

        print("\nSummary (with file-only paths):")
        print(f"  Parser count: {results['parser_count']}")
        print(f"  Pytest count: {results['pytest_count']}")
        print(f"  Common count: {results['common_count']}")
        print(f"  Only in parser: {results['only_in_parser_count']}")
        print(f"  Only in pytest: {results['only_in_pytest_count']}")

    # Run comparison without file-only paths
    print("\n=== WITHOUT FILE-ONLY PATHS ===")
    parser_tests = get_parser_test_paths(args.directory, include_file_only=False)
    results = analyze_path_differences(parser_tests, pytest_tests)

    print("\nSummary (without file-only paths):")
    print(f"  Parser count: {results['parser_count']}")
    print(f"  Pytest count: {results['pytest_count']}")
    print(f"  Common count: {results['common_count']}")
    print(f"  Only in parser: {results['only_in_parser_count']}")
    print(f"  Only in pytest: {results['only_in_pytest_count']}")
