#!/usr/bin/env python
"""
Script to analyze marker application and detection in a sample of test files.

This script helps understand the specific differences between how apply_speed_markers.py
and common_test_collector.py handle markers. It:

1. Selects a sample of test files
2. Analyzes how markers are applied by apply_speed_markers.py
3. Analyzes how markers are detected by common_test_collector.py
4. Compares the results to identify specific patterns or issues

Usage:
    python scripts/analyze_marker_discrepancy.py [options]

Options:
    --sample-size N        Number of test files to sample (default: 10)
    --verbose              Show verbose output
    --report-file FILE     Save the report to the specified file (default: marker_analysis_report.json)
"""

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector for marker detection
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import check_test_has_marker, clear_cache
except ImportError:
    print(
        "Error: common_test_collector.py not found or required functions not available."
    )
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze marker application and detection in a sample of test files."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of test files to sample (default: 10)",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--report-file",
        type=str,
        default="marker_analysis_report.json",
        help="Save the report to the specified file",
    )
    return parser.parse_args()


def find_all_test_files() -> list[str]:
    """
    Find all test files in the project.

    Returns:
        List of test file paths
    """
    test_files = []
    test_dirs = ["tests/unit", "tests/integration", "tests/behavior", "tests/property"]

    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for root, _, files in os.walk(test_dir):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        test_files.append(os.path.join(root, file))

    return test_files


def find_test_functions_in_file(file_path: str) -> list[str]:
    """
    Find all test functions in a file.

    Args:
        file_path: Path to the test file

    Returns:
        List of test function names
    """
    test_functions = []

    try:
        with open(file_path) as f:
            content = f.read()

        # Find all test functions (both standalone and class-based)
        import re

        # Find standalone test functions
        standalone_tests = re.findall(r"def\s+(test_\w+)\s*\(", content)
        test_functions.extend([(file_path, test) for test in standalone_tests])

        # Find class-based test methods
        class_matches = re.finditer(r"class\s+(\w+)\s*\(", content)
        for class_match in class_matches:
            class_name = class_match.group(1)
            class_content = content[class_match.start() :]

            # Find test methods within the class
            method_matches = re.finditer(r"def\s+(test_\w+)\s*\(", class_content)
            for method_match in method_matches:
                method_name = method_match.group(1)
                test_functions.append((file_path, f"{class_name}::{method_name}"))

    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")

    return test_functions


def analyze_apply_speed_markers(
    test_path: str, verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze how apply_speed_markers.py would handle a test.

    Args:
        test_path: Path to the test (file::class::method or file::method)
        verbose: Whether to show verbose output

    Returns:
        Dictionary containing analysis results
    """
    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
    else:
        file_path = test_path

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    # Read the file content
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Error reading file {file_path}: {e}"}

    # Extract test name from test path
    test_name = None
    class_name = None

    if "::" in test_path:
        parts = test_path.split("::")
        if len(parts) > 2:  # Class-based test
            file_path = parts[0]
            class_name = parts[1]
            test_name = parts[2]
        else:  # Function-based test
            file_path = parts[0]
            test_name = parts[1]

    # Check for existing markers
    import re

    marker_pattern = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")

    # Find the test function/method in the file
    if class_name:
        # Find the class
        class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*\(")
        class_match = class_pattern.search(content)

        if class_match:
            # Find the test method within the class
            class_content = content[class_match.start() :]
            test_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
            test_match = test_pattern.search(class_content)

            if test_match:
                # Look for markers before the test method
                test_pos = class_match.start() + test_match.start()
                start_pos = max(class_match.start(), test_pos - 1000)
                test_context = content[start_pos:test_pos]

                # Check for markers
                markers = []
                for match in marker_pattern.finditer(test_context):
                    markers.append(match.group(1))

                return {
                    "test_path": test_path,
                    "existing_markers": markers,
                    "apply_speed_markers_detection": "existing" if markers else "none",
                }
    else:
        # Find the test function
        test_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
        test_match = test_pattern.search(content)

        if test_match:
            # Look for markers before the test function
            start_pos = max(0, test_match.start() - 1000)
            test_context = content[start_pos : test_match.start()]

            # Check for markers
            markers = []
            for match in marker_pattern.finditer(test_context):
                markers.append(match.group(1))

            return {
                "test_path": test_path,
                "existing_markers": markers,
                "apply_speed_markers_detection": "existing" if markers else "none",
            }

    return {
        "test_path": test_path,
        "existing_markers": [],
        "apply_speed_markers_detection": "none",
    }


def analyze_common_test_collector(
    test_path: str, verbose: bool = False
) -> dict[str, Any]:
    """
    Analyze how common_test_collector.py would handle a test.

    Args:
        test_path: Path to the test (file::class::method or file::method)
        verbose: Whether to show verbose output

    Returns:
        Dictionary containing analysis results
    """
    # Clear the cache to ensure fresh results
    clear_cache()

    # Check if the test has a marker
    has_marker, marker_type = check_test_has_marker(test_path)

    return {
        "test_path": test_path,
        "has_marker": has_marker,
        "marker_type": marker_type,
        "common_test_collector_detection": "detected" if has_marker else "none",
    }


def compare_analyses(
    apply_analysis: dict[str, Any], collector_analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Compare the analyses from apply_speed_markers.py and common_test_collector.py.

    Args:
        apply_analysis: Analysis from apply_speed_markers.py
        collector_analysis: Analysis from common_test_collector.py

    Returns:
        Dictionary containing comparison results
    """
    # Check if both analyses are for the same test
    if apply_analysis.get("test_path") != collector_analysis.get("test_path"):
        return {"error": "Analyses are for different tests"}

    # Compare marker detection
    apply_detection = apply_analysis.get("apply_speed_markers_detection", "none")
    collector_detection = collector_analysis.get(
        "common_test_collector_detection", "none"
    )

    # Determine if there's a discrepancy
    discrepancy = apply_detection != collector_detection

    # If both detected markers, check if they're the same
    if apply_detection == "existing" and collector_detection == "detected":
        apply_markers = apply_analysis.get("existing_markers", [])
        collector_marker = collector_analysis.get("marker_type")

        if collector_marker in apply_markers:
            discrepancy = False
        else:
            discrepancy = True

    return {
        "test_path": apply_analysis.get("test_path"),
        "apply_speed_markers_detection": apply_detection,
        "common_test_collector_detection": collector_detection,
        "apply_markers": apply_analysis.get("existing_markers", []),
        "collector_marker": collector_analysis.get("marker_type"),
        "discrepancy": discrepancy,
        "discrepancy_type": (
            determine_discrepancy_type(apply_analysis, collector_analysis)
            if discrepancy
            else None
        ),
    }


def determine_discrepancy_type(
    apply_analysis: dict[str, Any], collector_analysis: dict[str, Any]
) -> str:
    """
    Determine the type of discrepancy between apply_speed_markers.py and common_test_collector.py.

    Args:
        apply_analysis: Analysis from apply_speed_markers.py
        collector_analysis: Analysis from common_test_collector.py

    Returns:
        String describing the type of discrepancy
    """
    apply_detection = apply_analysis.get("apply_speed_markers_detection", "none")
    collector_detection = collector_analysis.get(
        "common_test_collector_detection", "none"
    )

    if apply_detection == "existing" and collector_detection == "none":
        return "apply_detects_collector_misses"
    elif apply_detection == "none" and collector_detection == "detected":
        return "collector_detects_apply_misses"
    elif apply_detection == "existing" and collector_detection == "detected":
        apply_markers = apply_analysis.get("existing_markers", [])
        collector_marker = collector_analysis.get("marker_type")

        if collector_marker not in apply_markers:
            return "different_markers"

    return "unknown"


def main():
    """Main function."""
    args = parse_args()

    print(
        f"Analyzing marker application and detection in {args.sample_size} test files..."
    )

    # Find all test files
    all_test_files = find_all_test_files()
    print(f"Found {len(all_test_files)} test files in total.")

    # Select a random sample
    if len(all_test_files) > args.sample_size:
        sample_files = random.sample(all_test_files, args.sample_size)
    else:
        sample_files = all_test_files

    print(f"Selected {len(sample_files)} test files for analysis.")

    # Find test functions in each file
    all_test_functions = []
    for file_path in sample_files:
        test_functions = find_test_functions_in_file(file_path)
        all_test_functions.extend(test_functions)

    print(f"Found {len(all_test_functions)} test functions in the sample files.")

    # Analyze each test function
    results = []
    discrepancy_count = 0
    discrepancy_types = {}

    for file_path, test_function in all_test_functions:
        test_path = f"{file_path}::{test_function}"

        if args.verbose:
            print(f"Analyzing {test_path}...")

        # Analyze with apply_speed_markers.py
        apply_analysis = analyze_apply_speed_markers(test_path, args.verbose)

        # Analyze with common_test_collector.py
        collector_analysis = analyze_common_test_collector(test_path, args.verbose)

        # Compare the analyses
        comparison = compare_analyses(apply_analysis, collector_analysis)

        # Track discrepancies
        if comparison.get("discrepancy", False):
            discrepancy_count += 1
            discrepancy_type = comparison.get("discrepancy_type", "unknown")
            discrepancy_types[discrepancy_type] = (
                discrepancy_types.get(discrepancy_type, 0) + 1
            )

            if args.verbose:
                print(f"  Discrepancy found: {discrepancy_type}")
                print(
                    f"    apply_speed_markers: {apply_analysis.get('existing_markers', [])}"
                )
                print(
                    f"    common_test_collector: {collector_analysis.get('marker_type')}"
                )

        results.append(comparison)

    # Generate a report
    report = {
        "sample_size": len(sample_files),
        "test_functions": len(all_test_functions),
        "discrepancies": discrepancy_count,
        "discrepancy_rate": (
            discrepancy_count / len(all_test_functions) if all_test_functions else 0
        ),
        "discrepancy_types": discrepancy_types,
        "results": results,
    }

    # Save the report
    with open(args.report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nAnalysis complete. Report saved to {args.report_file}")
    print(
        f"Discrepancies found: {discrepancy_count} out of {len(all_test_functions)} ({report['discrepancy_rate']:.2%})"
    )
    print("\nDiscrepancy types:")
    for discrepancy_type, count in discrepancy_types.items():
        print(f"  {discrepancy_type}: {count} ({count / discrepancy_count:.2%})")


if __name__ == "__main__":
    main()
