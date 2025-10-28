#!/usr/bin/env python3
"""
Fix Duplicate Markers Script

This script identifies and resolves duplicate marker detections in the test suite.
It addresses the issue where the number of tests with markers exceeds the total
number of tests (100.31%).

The script:
1. Identifies tests that are counted multiple times due to having markers at different levels
   (module, class, function)
2. Analyzes the marker detection logic to find edge cases and false positives
3. Provides a report of duplicate marker detections
4. Optionally fixes the issues by standardizing marker placement

Usage:
    python scripts/fix_duplicate_markers.py [options]

Options:
    --analyze              Analyze duplicate marker detections without making changes
    --fix                  Fix duplicate marker detections by standardizing marker placement
    --verbose              Show detailed information
    --no-cache             Don't use cached test collection results
"""

import argparse
import json
import os
import re
import sys
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
        get_tests_with_markers,
        invalidate_cache_for_files,
        load_cache,
        save_cache,
    )
except ImportError:
    print(
        "Error: common_test_collector.py not found. Please ensure it exists in the scripts directory."
    )
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix duplicate marker detections in the test suite."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze duplicate marker detections without making changes",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix duplicate marker detections by standardizing marker placement",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached test collection results",
    )
    return parser.parse_args()


def get_module_markers(file_path: str) -> dict[str, bool]:
    """
    Get markers defined at the module level.

    Args:
        file_path: Path to the test file

    Returns:
        Dictionary mapping marker types to boolean values
    """
    markers = {"fast": False, "medium": False, "slow": False}

    if not os.path.exists(file_path):
        return markers

    try:
        with open(file_path) as f:
            content = f.read()

        # Check for pytestmark assignments
        for marker_type in markers:
            # Pattern for pytestmark = pytest.mark.marker
            pattern1 = re.compile(rf"pytestmark\s*=\s*pytest\.mark\.{marker_type}")
            # Pattern for pytestmark = [pytest.mark.marker]
            pattern2 = re.compile(
                rf"pytestmark\s*=\s*\[.*?pytest\.mark\.{marker_type}.*?\]"
            )

            if pattern1.search(content) or pattern2.search(content):
                markers[marker_type] = True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return markers


def get_class_markers(file_path: str, class_name: str) -> dict[str, bool]:
    """
    Get markers defined at the class level.

    Args:
        file_path: Path to the test file
        class_name: Name of the class

    Returns:
        Dictionary mapping marker types to boolean values
    """
    markers = {"fast": False, "medium": False, "slow": False}

    if not os.path.exists(file_path):
        return markers

    try:
        with open(file_path) as f:
            content = f.read()

        # Find the class definition
        class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*\(")
        class_match = class_pattern.search(content)

        if class_match:
            # Look for markers before the class definition
            class_pos = class_match.start()
            start_pos = max(
                0, class_pos - 500
            )  # Look at the 500 chars before the class
            class_context_before = content[start_pos:class_pos]

            for marker_type in markers:
                marker_pattern = re.compile(rf"@pytest\.mark\.{marker_type}($|[\s\(])")
                if marker_pattern.search(class_context_before):
                    markers[marker_type] = True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return markers


def get_function_markers(
    file_path: str, function_name: str, class_name: str | None = None
) -> dict[str, bool]:
    """
    Get markers defined at the function level.

    Args:
        file_path: Path to the test file
        function_name: Name of the function
        class_name: Optional name of the class containing the function

    Returns:
        Dictionary mapping marker types to boolean values
    """
    markers = {"fast": False, "medium": False, "slow": False}

    if not os.path.exists(file_path):
        return markers

    try:
        with open(file_path) as f:
            content = f.read()

        if class_name:
            # Find the class definition
            class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*\(")
            class_match = class_pattern.search(content)

            if class_match:
                # Find the function within the class
                class_pos = class_match.start()
                class_content = content[class_pos:]
                function_pattern = re.compile(rf"def\s+{re.escape(function_name)}\s*\(")
                function_match = function_pattern.search(class_content)

                if function_match:
                    # Adjust position to be relative to the entire file
                    function_pos = class_pos + function_match.start()

                    # Look for markers before the function
                    start_pos = max(
                        class_pos, function_pos - 500
                    )  # Look at the 500 chars before the function
                    function_context_before = content[start_pos:function_pos]

                    for marker_type in markers:
                        marker_pattern = re.compile(
                            rf"@pytest\.mark\.{marker_type}($|[\s\(])"
                        )
                        if marker_pattern.search(function_context_before):
                            markers[marker_type] = True
        else:
            # Find the function definition
            function_pattern = re.compile(rf"def\s+{re.escape(function_name)}\s*\(")
            function_match = function_pattern.search(content)

            if function_match:
                # Look for markers before the function
                function_pos = function_match.start()
                start_pos = max(
                    0, function_pos - 500
                )  # Look at the 500 chars before the function
                function_context_before = content[start_pos:function_pos]

                for marker_type in markers:
                    marker_pattern = re.compile(
                        rf"@pytest\.mark\.{marker_type}($|[\s\(])"
                    )
                    if marker_pattern.search(function_context_before):
                        markers[marker_type] = True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return markers


def analyze_duplicate_markers(
    use_cache: bool = True, verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze duplicate marker detections in the test suite.

    Args:
        use_cache: Whether to use cached test collection results
        verbose: Whether to show detailed information

    Returns:
        Dictionary with analysis results
    """
    print("Analyzing duplicate marker detections...")

    # Get all tests
    all_tests = collect_tests(use_cache=use_cache)

    # Get tests with markers
    tests_with_markers = get_tests_with_markers(use_cache=use_cache)

    # Calculate total counts
    total_tests = len(all_tests)
    total_with_markers = 0
    for category in tests_with_markers:
        for marker_type in tests_with_markers[category]:
            total_with_markers += len(tests_with_markers[category][marker_type])

    # Identify tests with multiple markers
    tests_with_multiple_markers = []
    marker_counts_by_test = {}

    for category in tests_with_markers:
        for marker_type in tests_with_markers[category]:
            for test_path in tests_with_markers[category][marker_type]:
                if test_path not in marker_counts_by_test:
                    marker_counts_by_test[test_path] = []
                marker_counts_by_test[test_path].append(marker_type)

    for test_path, markers in marker_counts_by_test.items():
        if len(markers) > 1:
            tests_with_multiple_markers.append({"path": test_path, "markers": markers})

    # Analyze marker placement for tests with multiple markers
    tests_with_marker_conflicts = []

    for test_info in tests_with_multiple_markers:
        test_path = test_info["path"]

        # Extract file path, class name, and function name
        file_path = test_path
        class_name = None
        function_name = None

        if "::" in test_path:
            parts = test_path.split("::")
            if len(parts) > 2:  # Class-based test
                file_path = parts[0]
                class_name = parts[1]
                function_name = parts[2]
            else:  # Function-based test
                file_path = parts[0]
                function_name = parts[1]

        # Get markers at different levels
        module_markers = get_module_markers(file_path)
        class_markers = get_class_markers(file_path, class_name) if class_name else {}
        function_markers = get_function_markers(file_path, function_name, class_name)

        # Check for conflicts
        marker_conflicts = []
        for marker_type in ["fast", "medium", "slow"]:
            markers_at_levels = []

            if module_markers.get(marker_type):
                markers_at_levels.append("module")

            if class_markers.get(marker_type):
                markers_at_levels.append("class")

            if function_markers.get(marker_type):
                markers_at_levels.append("function")

            if len(markers_at_levels) > 1:
                marker_conflicts.append(
                    {"marker": marker_type, "levels": markers_at_levels}
                )

        if marker_conflicts:
            tests_with_marker_conflicts.append(
                {"path": test_path, "conflicts": marker_conflicts}
            )

    # Prepare results
    results = {
        "total_tests": total_tests,
        "total_with_markers": total_with_markers,
        "percentage": total_with_markers / total_tests * 100 if total_tests > 0 else 0,
        "tests_with_multiple_markers": tests_with_multiple_markers,
        "tests_with_marker_conflicts": tests_with_marker_conflicts,
    }

    return results


def fix_duplicate_markers(
    analysis_results: dict[str, Any], verbose: bool = False
) -> dict[str, Any]:
    """
    Fix duplicate marker detections by standardizing marker placement.

    Args:
        analysis_results: Results from analyze_duplicate_markers
        verbose: Whether to show detailed information

    Returns:
        Dictionary with fix results
    """
    print("Fixing duplicate marker detections...")

    fixed_files = []
    skipped_files = []

    # Process tests with marker conflicts
    for test_info in analysis_results["tests_with_marker_conflicts"]:
        test_path = test_info["path"]
        conflicts = test_info["conflicts"]

        # Extract file path, class name, and function name
        file_path = test_path
        class_name = None
        function_name = None

        if "::" in test_path:
            parts = test_path.split("::")
            if len(parts) > 2:  # Class-based test
                file_path = parts[0]
                class_name = parts[1]
                function_name = parts[2]
            else:  # Function-based test
                file_path = parts[0]
                function_name = parts[1]

        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            skipped_files.append({"path": test_path, "reason": "File not found"})
            continue

        try:
            with open(file_path) as f:
                content = f.read()

            modified = False

            # Process each conflict
            for conflict in conflicts:
                marker_type = conflict["marker"]
                levels = conflict["levels"]

                # Standardize by keeping only the function-level marker
                if "function" in levels:
                    # Remove module-level marker
                    if "module" in levels:
                        # Pattern for pytestmark = pytest.mark.marker
                        pattern1 = re.compile(
                            rf"pytestmark\s*=\s*pytest\.mark\.{marker_type}"
                        )
                        # Pattern for pytestmark = [pytest.mark.marker]
                        pattern2 = re.compile(
                            rf"pytestmark\s*=\s*\[.*?pytest\.mark\.{marker_type}.*?\]"
                        )

                        if pattern1.search(content):
                            content = pattern1.sub("", content)
                            modified = True

                        if pattern2.search(content):
                            # This is more complex - we need to remove just the marker from the list
                            # For simplicity, we'll just note that we couldn't fix it automatically
                            skipped_files.append(
                                {
                                    "path": test_path,
                                    "reason": f"Complex module-level marker list with {marker_type}",
                                }
                            )

                    # Remove class-level marker
                    if "class" in levels and class_name:
                        # Find the class definition
                        class_pattern = re.compile(
                            rf"class\s+{re.escape(class_name)}\s*\("
                        )
                        class_match = class_pattern.search(content)

                        if class_match:
                            # Look for markers before the class definition
                            class_pos = class_match.start()
                            start_pos = max(
                                0, class_pos - 500
                            )  # Look at the 500 chars before the class
                            class_context_before = content[start_pos:class_pos]

                            marker_pattern = re.compile(
                                rf"@pytest\.mark\.{marker_type}($|[\s\(])"
                            )
                            marker_match = marker_pattern.search(class_context_before)

                            if marker_match:
                                # Remove the marker line
                                marker_line_start = start_pos + marker_match.start()
                                marker_line_end = content.find("\n", marker_line_start)
                                if marker_line_end > marker_line_start:
                                    content = (
                                        content[:marker_line_start]
                                        + content[marker_line_end + 1 :]
                                    )
                                    modified = True

                # If no function-level marker, standardize by keeping only the class-level marker
                elif "class" in levels:
                    # Remove module-level marker
                    if "module" in levels:
                        # Pattern for pytestmark = pytest.mark.marker
                        pattern1 = re.compile(
                            rf"pytestmark\s*=\s*pytest\.mark\.{marker_type}"
                        )
                        # Pattern for pytestmark = [pytest.mark.marker]
                        pattern2 = re.compile(
                            rf"pytestmark\s*=\s*\[.*?pytest\.mark\.{marker_type}.*?\]"
                        )

                        if pattern1.search(content):
                            content = pattern1.sub("", content)
                            modified = True

                        if pattern2.search(content):
                            # This is more complex - we need to remove just the marker from the list
                            # For simplicity, we'll just note that we couldn't fix it automatically
                            skipped_files.append(
                                {
                                    "path": test_path,
                                    "reason": f"Complex module-level marker list with {marker_type}",
                                }
                            )

            # Write modified content back to file
            if modified:
                with open(file_path, "w") as f:
                    f.write(content)

                fixed_files.append(test_path)

                # Invalidate cache for this file
                invalidate_cache_for_files([file_path])

        except Exception as e:
            skipped_files.append({"path": test_path, "reason": f"Error: {str(e)}"})

    # Prepare results
    results = {"fixed_files": fixed_files, "skipped_files": skipped_files}

    return results


def print_analysis_results(results: dict[str, Any], verbose: bool = False):
    """
    Print analysis results.

    Args:
        results: Results from analyze_duplicate_markers
        verbose: Whether to show detailed information
    """
    print("\nAnalysis Results:")
    print(f"Total tests: {results['total_tests']:,}")
    print(f"Tests with markers: {results['total_with_markers']:,}")
    print(f"Percentage: {results['percentage']:.2f}%")

    if results["percentage"] > 100:
        print(f"\nWARNING: More tests with markers than total tests!")
        print(
            f"Excess: {results['total_with_markers'] - results['total_tests']:,} tests ({results['percentage'] - 100:.2f}%)"
        )

    print(
        f"\nTests with multiple markers: {len(results['tests_with_multiple_markers']):,}"
    )
    print(
        f"Tests with marker conflicts: {len(results['tests_with_marker_conflicts']):,}"
    )

    if verbose:
        print("\nTests with marker conflicts:")
        for test_info in results["tests_with_marker_conflicts"]:
            print(f"  {test_info['path']}")
            for conflict in test_info["conflicts"]:
                print(
                    f"    {conflict['marker']} at levels: {', '.join(conflict['levels'])}"
                )


def print_fix_results(results: dict[str, Any], verbose: bool = False):
    """
    Print fix results.

    Args:
        results: Results from fix_duplicate_markers
        verbose: Whether to show detailed information
    """
    print("\nFix Results:")
    print(f"Fixed files: {len(results['fixed_files']):,}")
    print(f"Skipped files: {len(results['skipped_files']):,}")

    if verbose:
        print("\nFixed files:")
        for file_path in results["fixed_files"]:
            print(f"  {file_path}")

        print("\nSkipped files:")
        for file_info in results["skipped_files"]:
            print(f"  {file_info['path']} - {file_info['reason']}")


def main():
    """Main function."""
    args = parse_args()

    # Analyze duplicate markers
    analysis_results = analyze_duplicate_markers(
        use_cache=not args.no_cache, verbose=args.verbose
    )

    # Print analysis results
    print_analysis_results(analysis_results, verbose=args.verbose)

    # Fix duplicate markers if requested
    if args.fix:
        fix_results = fix_duplicate_markers(analysis_results, verbose=args.verbose)

        # Print fix results
        print_fix_results(fix_results, verbose=args.verbose)

        # Re-analyze after fixing
        print("\nRe-analyzing after fixing...")
        new_analysis_results = analyze_duplicate_markers(
            use_cache=False, verbose=args.verbose  # Force fresh analysis
        )

        # Print new analysis results
        print_analysis_results(new_analysis_results, verbose=args.verbose)

        # Calculate improvement
        old_percentage = analysis_results["percentage"]
        new_percentage = new_analysis_results["percentage"]

        print(f"\nImprovement: {old_percentage - new_percentage:.2f}%")

        if new_percentage > 100:
            print(f"\nWARNING: Still more tests with markers than total tests!")
            print(
                f"Excess: {new_analysis_results['total_with_markers'] - new_analysis_results['total_tests']:,} tests ({new_percentage - 100:.2f}%)"
            )
            print(
                "Consider running the script again or manually fixing the remaining issues."
            )


if __name__ == "__main__":
    main()
