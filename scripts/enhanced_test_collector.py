#!/usr/bin/env python3
"""
Enhanced Test Collector

This script integrates the enhanced test parser with the existing test infrastructure.
It extends common_test_collector.py to use the enhanced parser for non-behavior tests
while maintaining compatibility with the existing infrastructure.

Key features:
1. Seamless integration with common_test_collector.py
2. More accurate test collection for non-behavior tests
3. Improved marker detection for non-behavior tests
4. Compatible with existing test infrastructure scripts

Usage:
    from enhanced_test_collector import collect_tests, get_tests_with_markers

    # Collect all tests
    tests = collect_tests()

    # Get tests with specific markers
    tests_with_markers = get_tests_with_markers(["fast", "medium", "slow"])
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import common test collector and enhanced test parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_test_collector
import enhanced_test_parser

# Constants
TEST_CATEGORIES = common_test_collector.TEST_CATEGORIES


def collect_tests_by_category(category: str, use_cache: bool = True) -> list[str]:
    """
    Collect tests by category using the appropriate parser.

    Args:
        category: Test category (unit, integration, behavior, etc.)
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    # Use the enhanced parser for non-behavior tests
    if category != "behavior":
        directory = TEST_CATEGORIES.get(category, f"tests/{category}")
        return enhanced_test_parser.get_test_paths_from_directory(directory, use_cache)

    # Use the original implementation for behavior tests
    return common_test_collector.collect_tests_by_category(category, use_cache)


def collect_tests(use_cache: bool = True) -> dict[str, list[str]]:
    """
    Collect all tests in the project, organized by category.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping test categories to lists of test paths
    """
    all_tests = {}

    # Collect tests for each category
    for category in TEST_CATEGORIES:
        all_tests[category] = collect_tests_by_category(category, use_cache)

    return all_tests


def get_tests_with_markers(
    marker_types: list[str] = ["fast", "medium", "slow"], use_cache: bool = True
) -> dict[str, dict[str, list[str]]]:
    """
    Get tests with specific markers, organized by category.

    Args:
        marker_types: List of marker types to check for
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping categories to dictionaries mapping marker types to lists of test paths
    """
    tests_with_markers = {}

    # Get tests with markers for each category
    for category in TEST_CATEGORIES:
        directory = TEST_CATEGORIES.get(category, f"tests/{category}")

        # Use the enhanced parser for non-behavior tests
        if category != "behavior":
            category_markers = enhanced_test_parser.get_tests_with_markers(
                directory, marker_types, use_cache
            )
        else:
            # Use the original implementation for behavior tests
            category_markers = {}
            all_markers = common_test_collector.get_tests_with_markers(
                marker_types, use_cache
            )
            if category in all_markers:
                category_markers = all_markers[category]
            else:
                category_markers = {marker: [] for marker in marker_types}

        tests_with_markers[category] = category_markers

    return tests_with_markers


def get_marker_counts(use_cache: bool = True) -> dict[str, dict[str, int]]:
    """
    Get counts of tests with specific markers, organized by category.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping categories to dictionaries mapping marker types to counts
    """
    marker_counts = {"total": {"fast": 0, "medium": 0, "slow": 0}}

    # Get marker counts for each category
    for category in TEST_CATEGORIES:
        directory = TEST_CATEGORIES.get(category, f"tests/{category}")

        # Use the enhanced parser for non-behavior tests
        if category != "behavior":
            category_counts = enhanced_test_parser.get_marker_counts(
                directory, use_cache
            )
        else:
            # Use the original implementation for behavior tests
            all_counts = common_test_collector.get_marker_counts(use_cache)
            category_counts = all_counts.get(
                category, {"fast": 0, "medium": 0, "slow": 0}
            )

        marker_counts[category] = category_counts

        # Update total counts
        for marker, count in category_counts.items():
            marker_counts["total"][marker] += count

    return marker_counts


def check_test_has_marker(
    test_path: str, marker_types: list[str] = ["fast", "medium", "slow"]
) -> tuple[bool, str | None]:
    """
    Check if a test has a specific marker.

    Args:
        test_path: Path to the test
        marker_types: List of marker types to check for

    Returns:
        Tuple of (has_marker, marker_type)
    """
    # Determine the category based on the test path
    category = None
    for cat, path in TEST_CATEGORIES.items():
        if test_path.startswith(path):
            category = cat
            break

    # Use the enhanced parser for non-behavior tests
    if category and category != "behavior":
        # Parse the file to get test metadata
        file_path = test_path.split("::")[0] if "::" in test_path else test_path
        tests = enhanced_test_parser.parse_test_file(file_path)

        # Find the test in the parsed tests
        for test in tests:
            if test["path"] == test_path:
                for marker in test.get("markers", []):
                    if marker in marker_types:
                        return True, marker
                return False, None

    # Use the original implementation for behavior tests or if category not determined
    return common_test_collector.check_test_has_marker(test_path, marker_types)


def verify_test_counts(use_cache: bool = True) -> dict[str, Any]:
    """
    Verify test counts between different collection methods.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary with verification results
    """
    results = {
        "categories": {},
        "total": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
    }

    # Verify each category
    for category in TEST_CATEGORIES:
        directory = TEST_CATEGORIES[category]

        # Collect tests using pytest
        pytest_tests = common_test_collector.collect_tests_with_pytest(directory)
        pytest_count = len(pytest_tests)

        # Collect tests using the enhanced collector
        enhanced_tests = collect_tests_by_category(category, use_cache)
        enhanced_count = len(enhanced_tests)

        # Calculate discrepancy
        discrepancy = abs(pytest_count - enhanced_count)

        # Store results
        results["categories"][category] = {
            "pytest_count": pytest_count,
            "enhanced_count": enhanced_count,
            "discrepancy": discrepancy,
        }

        # Update totals
        results["total"]["pytest_count"] += pytest_count
        results["total"]["enhanced_count"] += enhanced_count
        results["total"]["discrepancy"] += discrepancy

    return results


def verify_marker_detection(use_cache: bool = True) -> dict[str, Any]:
    """
    Verify marker detection between different collection methods.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary with verification results
    """
    results = {
        "markers": {
            "fast": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
            "medium": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
            "slow": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
        },
        "categories": {},
    }

    # Get marker counts using the enhanced collector
    enhanced_counts = get_marker_counts(use_cache)

    # Verify each category
    for category in TEST_CATEGORIES:
        directory = TEST_CATEGORIES[category]

        # Initialize category results
        results["categories"][category] = {
            "markers": {
                "fast": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
                "medium": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
                "slow": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
            }
        }

        # Get markers from pytest
        pytest_markers = {}
        for marker in ["fast", "medium", "slow"]:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                directory,
                f"-m={marker}",
                "--collect-only",
                "-q",
            ]

            try:
                import subprocess

                result = subprocess.run(
                    cmd, check=False, capture_output=True, text=True
                )

                # Extract test paths from output
                pytest_tests = []
                for line in result.stdout.split("\n"):
                    if line.strip() and not line.startswith("="):
                        pytest_tests.append(line.strip())

                pytest_markers[marker] = pytest_tests

            except Exception as e:
                print(f"Error collecting {marker} markers with pytest: {e}")
                pytest_markers[marker] = []

        # Count markers
        for marker in ["fast", "medium", "slow"]:
            enhanced_count = enhanced_counts.get(category, {}).get(marker, 0)
            pytest_count = len(pytest_markers.get(marker, []))
            discrepancy = abs(pytest_count - enhanced_count)

            # Update category results
            results["categories"][category]["markers"][marker] = {
                "enhanced_count": enhanced_count,
                "pytest_count": pytest_count,
                "discrepancy": discrepancy,
            }

            # Update total results
            results["markers"][marker]["enhanced_count"] += enhanced_count
            results["markers"][marker]["pytest_count"] += pytest_count
            results["markers"][marker]["discrepancy"] += discrepancy

    return results


def generate_test_isolation_report(directory: str = "tests") -> dict[str, Any]:
    """
    Generate a report on test isolation issues.

    Args:
        directory: Directory to analyze

    Returns:
        Dictionary with test isolation report
    """
    # Import test isolation analyzer
    try:
        from test_isolation_analyzer import analyze_test_isolation

        return analyze_test_isolation(directory)
    except ImportError:
        print(
            "Warning: test_isolation_analyzer not found, falling back to basic analysis"
        )

        # Basic analysis of test isolation issues
        report = {"total_tests": 0, "potential_issues": [], "recommendations": []}

        # Collect all tests
        all_tests = []
        for category in TEST_CATEGORIES:
            cat_tests = collect_tests_by_category(category)
            all_tests.extend(cat_tests)

        report["total_tests"] = len(all_tests)

        # Add general recommendations
        report["recommendations"] = [
            "Use pytest fixtures for setup and teardown",
            "Avoid global state in tests",
            "Use monkeypatch for patching",
            "Reset mocks between tests",
            "Use tmpdir fixture for file operations",
            "Isolate database operations",
        ]

        return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced test collector for non-behavior tests."
    )
    parser.add_argument(
        "--verify-counts",
        action="store_true",
        help="Verify test counts between different collection methods",
    )
    parser.add_argument(
        "--verify-markers",
        action="store_true",
        help="Verify marker detection between different collection methods",
    )
    parser.add_argument(
        "--isolation-report",
        action="store_true",
        help="Generate a report on test isolation issues",
    )
    parser.add_argument("--directory", default="tests", help="Directory to analyze")
    parser.add_argument("--output", help="Output file for reports (JSON format)")

    args = parser.parse_args()

    if args.verify_counts:
        results = verify_test_counts()
        print("Test count verification results:")
        print(
            f"Total: {results['total']['enhanced_count']} tests (enhanced), {results['total']['pytest_count']} tests (pytest)"
        )
        print(f"Total discrepancy: {results['total']['discrepancy']}")

        for category, cat_results in results["categories"].items():
            print(
                f"{category}: {cat_results['enhanced_count']} tests (enhanced), {cat_results['pytest_count']} tests (pytest), discrepancy: {cat_results['discrepancy']}"
            )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

    elif args.verify_markers:
        results = verify_marker_detection()
        print("Marker detection verification results:")

        for marker in ["fast", "medium", "slow"]:
            print(
                f"{marker}: {results['markers'][marker]['enhanced_count']} tests (enhanced), {results['markers'][marker]['pytest_count']} tests (pytest), discrepancy: {results['markers'][marker]['discrepancy']}"
            )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

    elif args.isolation_report:
        results = generate_test_isolation_report(args.directory)
        print("Test isolation report:")
        print(f"Total tests: {results['total_tests']}")
        print("Recommendations:")
        for recommendation in results["recommendations"]:
            print(f"- {recommendation}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

    else:
        # Just collect and count tests
        all_tests = collect_tests()
        total_count = sum(len(tests) for tests in all_tests.values())
        print(f"Found {total_count} tests in total:")

        for category, tests in all_tests.items():
            print(f"  {category}: {len(tests)} tests")
