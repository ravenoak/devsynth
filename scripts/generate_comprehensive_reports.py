#!/usr/bin/env python3
"""
Generate Comprehensive Reports

This script generates comprehensive reports for the DevSynth project to verify
the enhanced test infrastructure and provide data for documentation. It combines
the functionality of enhanced_test_parser.py, enhanced_test_collector.py, and
test_isolation_analyzer.py to generate reports on test counts, marker detection,
and test isolation issues.

Usage:
    python generate_comprehensive_reports.py --all
    python generate_comprehensive_reports.py --test-counts
    python generate_comprehensive_reports.py --marker-detection
    python generate_comprehensive_reports.py --test-isolation
"""

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test infrastructure tools
try:
    import enhanced_test_collector
    import enhanced_test_parser
    import test_isolation_analyzer
except ImportError as e:
    print(f"Error importing test infrastructure tools: {e}")
    print(
        "Make sure enhanced_test_parser.py, enhanced_test_collector.py, and test_isolation_analyzer.py are in the same directory as this script."
    )
    sys.exit(1)

# Constants
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "performance": "tests/performance",
    "property": "tests/property",
}

HIGH_PRIORITY_MODULES = [
    "tests/unit/application",
    "tests/unit/adapters",
    "tests/integration/general",
    "tests/unit/interface",
]


def generate_test_count_report() -> dict[str, Any]:
    """
    Generate a comprehensive report on test counts.

    Returns:
        Dictionary with test count report
    """
    print("Generating test count report...")

    # Initialize the report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "categories": {},
        "total": {
            "enhanced_count": 0,
            "pytest_count": 0,
            "discrepancy": 0,
            "discrepancy_percentage": 0,
        },
    }

    # Verify test counts for each category
    for category in TEST_CATEGORIES:
        print(f"  Processing {category} tests...")
        directory = TEST_CATEGORIES[category]

        # Collect tests using pytest
        pytest_tests = (
            enhanced_test_collector.common_test_collector.collect_tests_with_pytest(
                directory
            )
        )
        pytest_count = len(pytest_tests)

        # Collect tests using the enhanced collector
        enhanced_tests = enhanced_test_collector.collect_tests_by_category(
            category, use_cache=False
        )
        enhanced_count = len(enhanced_tests)

        # Calculate discrepancy
        discrepancy = abs(pytest_count - enhanced_count)
        discrepancy_percentage = (
            (discrepancy / max(pytest_count, 1)) * 100 if pytest_count > 0 else 0
        )

        # Store results
        report["categories"][category] = {
            "pytest_count": pytest_count,
            "enhanced_count": enhanced_count,
            "discrepancy": discrepancy,
            "discrepancy_percentage": discrepancy_percentage,
            "only_in_pytest": len(set(pytest_tests) - set(enhanced_tests)),
            "only_in_enhanced": len(set(enhanced_tests) - set(pytest_tests)),
            "common": len(set(pytest_tests).intersection(set(enhanced_tests))),
        }

        # Update totals
        report["total"]["pytest_count"] += pytest_count
        report["total"]["enhanced_count"] += enhanced_count
        report["total"]["discrepancy"] += discrepancy

    # Calculate total discrepancy percentage
    report["total"]["discrepancy_percentage"] = (
        (report["total"]["discrepancy"] / max(report["total"]["pytest_count"], 1)) * 100
        if report["total"]["pytest_count"] > 0
        else 0
    )

    # Add detailed comparison for each category
    for category in TEST_CATEGORIES:
        print(f"  Generating detailed comparison for {category} tests...")
        directory = TEST_CATEGORIES[category]

        # Compare with pytest
        comparison = enhanced_test_parser.compare_with_pytest(directory)

        # Add detailed comparison to the report
        report["categories"][category]["detailed_comparison"] = comparison

    print("Test count report generated.")
    return report


def generate_marker_detection_report() -> dict[str, Any]:
    """
    Generate a comprehensive report on marker detection.

    Returns:
        Dictionary with marker detection report
    """
    print("Generating marker detection report...")

    # Initialize the report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "markers": {
            "fast": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
            "medium": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
            "slow": {"enhanced_count": 0, "pytest_count": 0, "discrepancy": 0},
        },
        "categories": {},
    }

    # Verify marker detection
    marker_results = enhanced_test_collector.verify_marker_detection(use_cache=False)

    # Copy the results to the report
    report["markers"] = marker_results["markers"]
    report["categories"] = marker_results["categories"]

    # Calculate percentages
    for marker in ["fast", "medium", "slow"]:
        enhanced_count = report["markers"][marker]["enhanced_count"]
        pytest_count = report["markers"][marker]["pytest_count"]
        discrepancy = report["markers"][marker]["discrepancy"]

        report["markers"][marker]["discrepancy_percentage"] = (
            (discrepancy / max(pytest_count, 1)) * 100 if pytest_count > 0 else 0
        )

    # Calculate total marker coverage
    all_tests = enhanced_test_collector.collect_tests(use_cache=False)
    total_tests = sum(len(tests) for tests in all_tests.values())

    total_marked_tests = sum(
        report["markers"][marker]["enhanced_count"]
        for marker in ["fast", "medium", "slow"]
    )

    report["total_tests"] = total_tests
    report["total_marked_tests"] = total_marked_tests
    report["marker_coverage_percentage"] = (
        (total_marked_tests / max(total_tests, 1)) * 100 if total_tests > 0 else 0
    )

    print("Marker detection report generated.")
    return report


def generate_test_isolation_report() -> dict[str, Any]:
    """
    Generate a comprehensive report on test isolation issues.

    Returns:
        Dictionary with test isolation report
    """
    print("Generating test isolation report...")

    # Initialize the report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "high_priority_modules": {},
        "best_practices": test_isolation_analyzer.generate_isolation_best_practices(),
        "overall": {
            "total_files": 0,
            "files_with_issues": 0,
            "total_issues": 0,
            "issues_by_type": {},
        },
    }

    # Analyze high-priority modules
    for module in HIGH_PRIORITY_MODULES:
        print(f"  Analyzing {module}...")

        # Skip if the module doesn't exist
        if not os.path.exists(module):
            print(f"  Warning: Module {module} does not exist, skipping.")
            continue

        # Analyze the module
        module_results = test_isolation_analyzer.analyze_test_isolation(module)

        # Add to the report
        report["high_priority_modules"][module] = module_results

        # Update overall counts
        report["overall"]["total_files"] += module_results["total_files"]
        report["overall"]["files_with_issues"] += module_results["files_with_issues"]
        report["overall"]["total_issues"] += module_results["total_issues"]

        # Update issues by type
        for issue_type, count in module_results["issues_by_type"].items():
            report["overall"]["issues_by_type"][issue_type] = (
                report["overall"]["issues_by_type"].get(issue_type, 0) + count
            )

    # Calculate percentages
    report["overall"]["files_with_issues_percentage"] = (
        (
            report["overall"]["files_with_issues"]
            / max(report["overall"]["total_files"], 1)
        )
        * 100
        if report["overall"]["total_files"] > 0
        else 0
    )

    # Add overall recommendations
    report["overall"]["recommendations"] = []

    # Collect all recommendations from high-priority modules
    all_recommendations = set()
    for module_results in report["high_priority_modules"].values():
        for recommendation in module_results["recommendations"]:
            all_recommendations.add(recommendation)

    # Add to the report
    report["overall"]["recommendations"] = list(all_recommendations)

    print("Test isolation report generated.")
    return report


def save_report(report: dict[str, Any], filename: str):
    """
    Save a report to a file.

    Args:
        report: Report to save
        filename: Filename to save to
    """
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {filename}")


def print_report_summary(report_type: str, report: dict[str, Any]):
    """
    Print a summary of a report.

    Args:
        report_type: Type of report
        report: Report to summarize
    """
    print(f"\n{report_type} Report Summary:")

    if report_type == "Test Count":
        print(f"Total tests (pytest): {report['total']['pytest_count']}")
        print(f"Total tests (enhanced): {report['total']['enhanced_count']}")
        print(
            f"Total discrepancy: {report['total']['discrepancy']} ({report['total']['discrepancy_percentage']:.2f}%)"
        )

        print("\nBy category:")
        for category, cat_report in report["categories"].items():
            print(
                f"  {category}: {cat_report['pytest_count']} (pytest), {cat_report['enhanced_count']} (enhanced), discrepancy: {cat_report['discrepancy']} ({cat_report['discrepancy_percentage']:.2f}%)"
            )

    elif report_type == "Marker Detection":
        print(f"Total tests: {report['total_tests']}")
        print(f"Total marked tests: {report['total_marked_tests']}")
        print(f"Marker coverage: {report['marker_coverage_percentage']:.2f}%")

        print("\nBy marker:")
        for marker in ["fast", "medium", "slow"]:
            marker_report = report["markers"][marker]
            print(
                f"  {marker}: {marker_report['enhanced_count']} (enhanced), {marker_report['pytest_count']} (pytest), discrepancy: {marker_report['discrepancy']} ({marker_report['discrepancy_percentage']:.2f}%)"
            )

    elif report_type == "Test Isolation":
        print(f"Total files analyzed: {report['overall']['total_files']}")
        print(
            f"Files with issues: {report['overall']['files_with_issues']} ({report['overall']['files_with_issues_percentage']:.2f}%)"
        )
        print(f"Total issues: {report['overall']['total_issues']}")

        print("\nIssues by type:")
        for issue_type, count in report["overall"]["issues_by_type"].items():
            print(f"  {issue_type}: {count}")

        print("\nTop recommendations:")
        for i, recommendation in enumerate(report["overall"]["recommendations"][:5], 1):
            print(f"  {i}. {recommendation}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comprehensive reports for the DevSynth project."
    )
    parser.add_argument("--all", action="store_true", help="Generate all reports")
    parser.add_argument(
        "--test-counts", action="store_true", help="Generate test count report"
    )
    parser.add_argument(
        "--marker-detection",
        action="store_true",
        help="Generate marker detection report",
    )
    parser.add_argument(
        "--test-isolation", action="store_true", help="Generate test isolation report"
    )
    parser.add_argument(
        "--output-dir", default=".", help="Directory to save reports to"
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate reports
    if args.all or args.test_counts:
        test_count_report = generate_test_count_report()
        save_report(
            test_count_report, os.path.join(args.output_dir, "test_count_report.json")
        )
        print_report_summary("Test Count", test_count_report)

    if args.all or args.marker_detection:
        marker_detection_report = generate_marker_detection_report()
        save_report(
            marker_detection_report,
            os.path.join(args.output_dir, "marker_detection_report.json"),
        )
        print_report_summary("Marker Detection", marker_detection_report)

    if args.all or args.test_isolation:
        test_isolation_report = generate_test_isolation_report()
        save_report(
            test_isolation_report,
            os.path.join(args.output_dir, "test_isolation_report.json"),
        )
        print_report_summary("Test Isolation", test_isolation_report)

    print("\nAll reports generated successfully.")


if __name__ == "__main__":
    main()
