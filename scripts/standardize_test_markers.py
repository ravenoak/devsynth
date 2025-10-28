#!/usr/bin/env python3
"""
Standardize Test Markers

This script standardizes marker placement across test files and verifies that markers are correctly placed.
It helps maintain consistency in test marker usage, which is essential for effective test categorization
and execution.

Usage:
    python scripts/standardize_test_markers.py [options]

Options:
    --module MODULE       Specific module to process (e.g., tests/unit/interface)
    --category CATEGORY   Test category to process (unit, integration, behavior, all)
    --max-tests N         Maximum number of tests to process in a single run (default: 100)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
    --verify              Only verify marker placement without making changes
    --fix                 Fix marker placement issues
    --report              Generate a report of marker placement issues
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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

# Standard marker placement patterns
STANDARD_PATTERNS = {
    "function": {
        "correct": r"@pytest\.mark\.[a-z_]+\s*\n\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
        "incorrect": [
            # Marker after function definition
            r"def\s+test_[a-zA-Z0-9_]+\s*\([^)]*\):\s*\n\s*@pytest\.mark\.[a-z_]+",
            # Marker with blank line between marker and function
            r"@pytest\.mark\.[a-z_]+\s*\n\s*\n+\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
            # Multiple markers on the same function
            r"@pytest\.mark\.[a-z_]+\s*\n\s*@pytest\.mark\.[a-z_]+\s*\n\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
        ],
    },
    "class_method": {
        "correct": r"    @pytest\.mark\.[a-z_]+\s*\n\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
        "incorrect": [
            # Marker after method definition
            r"    def\s+test_[a-zA-Z0-9_]+\s*\([^)]*\):\s*\n\s*@pytest\.mark\.[a-z_]+",
            # Marker with blank line between marker and method
            r"    @pytest\.mark\.[a-z_]+\s*\n\s*\n+\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
            # Multiple markers on the same method
            r"    @pytest\.mark\.[a-z_]+\s*\n\s*@pytest\.mark\.[a-z_]+\s*\n\s*def\s+test_[a-zA-Z0-9_]+\s*\(",
        ],
    },
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Standardize marker placement across test files."
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
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify marker placement without making changes",
    )
    parser.add_argument(
        "--fix", action="store_true", help="Fix marker placement issues"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a report of marker placement issues",
    )
    return parser.parse_args()


def collect_test_files(
    category: str = "all", module: str = None, use_cache: bool = True
) -> list[str]:
    """
    Collect test files to process.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to collect tests from
        use_cache: Whether to use cached test collection results

    Returns:
        List of test file paths
    """
    print("Collecting test files...")

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

    # Extract unique file paths
    test_files = set()
    for test in all_tests:
        if "::" in test:
            file_path = test.split("::")[0]
            test_files.add(file_path)
        else:
            test_files.add(test)

    print(f"Found {len(test_files)} test files")
    return list(test_files)


def prioritize_files(files: list[str], priority_modules: list[str]) -> list[str]:
    """
    Prioritize files based on module priority.

    Args:
        files: List of file paths
        priority_modules: List of high-priority modules

    Returns:
        Prioritized list of file paths
    """
    high_priority = []
    normal_priority = []

    for file in files:
        if any(file.startswith(module) for module in priority_modules):
            high_priority.append(file)
        else:
            normal_priority.append(file)

    return high_priority + normal_priority


def analyze_file(
    file_path: str, patterns: dict[str, dict[str, Any]], verbose: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """
    Analyze a file for marker placement issues.

    Args:
        file_path: Path to the file to analyze
        patterns: Dictionary of patterns to look for
        verbose: Whether to show detailed information

    Returns:
        Dictionary of issues found in the file
    """
    if verbose:
        print(f"Analyzing {file_path}...")

    try:
        with open(file_path) as f:
            content = f.read()

        issues = {"function": [], "class_method": []}

        # Check for each pattern type
        for pattern_type, pattern_info in patterns.items():
            # Check for incorrect patterns
            for i, incorrect_pattern in enumerate(pattern_info["incorrect"]):
                matches = re.finditer(incorrect_pattern, content)

                for match in matches:
                    line_start = content[: match.start()].count("\n") + 1
                    line_end = content[: match.end()].count("\n") + 1

                    # Get the context (a few lines before and after)
                    lines = content.split("\n")
                    context_start = max(0, line_start - 3)
                    context_end = min(len(lines), line_end + 3)
                    context = "\n".join(lines[context_start:context_end])

                    issues[pattern_type].append(
                        {
                            "type": f"incorrect_{i+1}",
                            "description": f"Incorrect marker placement for {pattern_type}",
                            "line_start": line_start,
                            "line_end": line_end,
                            "match": match.group(0),
                            "context": context,
                        }
                    )

        return issues

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {"function": [], "class_method": []}


def fix_file(
    file_path: str,
    issues: dict[str, list[dict[str, Any]]],
    dry_run: bool = True,
    verbose: bool = False,
) -> bool:
    """
    Fix marker placement issues in a file.

    Args:
        file_path: Path to the file to fix
        issues: Dictionary of issues to fix
        dry_run: Whether to show changes without modifying the file
        verbose: Whether to show detailed information

    Returns:
        Whether the file was modified
    """
    if verbose:
        print(f"Fixing {file_path}...")

    try:
        with open(file_path) as f:
            content = f.read()

        modified = False
        new_content = content

        # Process function issues
        for issue in issues["function"]:
            if issue["type"] == "incorrect_1":
                # Fix marker after function definition
                if verbose:
                    print(
                        f"  Fixing marker after function definition at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Extract the marker and function definition
                match = re.search(
                    r"(def\s+test_[a-zA-Z0-9_]+\s*\([^)]*\):)\s*\n\s*(@pytest\.mark\.[a-z_]+)",
                    issue["match"],
                )
                if match:
                    func_def = match.group(1)
                    marker = match.group(2)

                    # Create the fixed version
                    fixed = f"{marker}\n{func_def}"

                    # Replace in the content
                    new_content = new_content.replace(issue["match"], fixed)
                    modified = True

            elif issue["type"] == "incorrect_2":
                # Fix marker with blank line between marker and function
                if verbose:
                    print(
                        f"  Fixing marker with blank line at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Replace multiple blank lines with a single newline
                fixed = re.sub(
                    r"(@pytest\.mark\.[a-z_]+)\s*\n\s*\n+\s*(def\s+test_[a-zA-Z0-9_]+\s*\()",
                    r"\1\n\2",
                    issue["match"],
                )

                # Replace in the content
                new_content = new_content.replace(issue["match"], fixed)
                modified = True

            elif issue["type"] == "incorrect_3":
                # Fix multiple markers on the same function
                if verbose:
                    print(
                        f"  Fixing multiple markers at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Extract the markers and function definition
                match = re.search(
                    r"(@pytest\.mark\.[a-z_]+)\s*\n\s*(@pytest\.mark\.[a-z_]+)\s*\n\s*(def\s+test_[a-zA-Z0-9_]+\s*\()",
                    issue["match"],
                )
                if match:
                    marker1 = match.group(1)
                    marker2 = match.group(2)
                    func_def = match.group(3)

                    # Create the fixed version (keeping only the speed marker)
                    if "fast" in marker1 or "medium" in marker1 or "slow" in marker1:
                        fixed = f"{marker1}\n{func_def}"
                    elif "fast" in marker2 or "medium" in marker2 or "slow" in marker2:
                        fixed = f"{marker2}\n{func_def}"
                    else:
                        # If neither is a speed marker, keep the first one
                        fixed = f"{marker1}\n{func_def}"

                    # Replace in the content
                    new_content = new_content.replace(issue["match"], fixed)
                    modified = True

        # Process class method issues (similar to function issues but with indentation)
        for issue in issues["class_method"]:
            if issue["type"] == "incorrect_1":
                # Fix marker after method definition
                if verbose:
                    print(
                        f"  Fixing marker after method definition at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Extract the marker and method definition
                match = re.search(
                    r"(    def\s+test_[a-zA-Z0-9_]+\s*\([^)]*\):)\s*\n\s*(@pytest\.mark\.[a-z_]+)",
                    issue["match"],
                )
                if match:
                    method_def = match.group(1)
                    marker = match.group(2)

                    # Create the fixed version
                    fixed = f"    {marker}\n{method_def}"

                    # Replace in the content
                    new_content = new_content.replace(issue["match"], fixed)
                    modified = True

            elif issue["type"] == "incorrect_2":
                # Fix marker with blank line between marker and method
                if verbose:
                    print(
                        f"  Fixing marker with blank line at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Replace multiple blank lines with a single newline
                fixed = re.sub(
                    r"(    @pytest\.mark\.[a-z_]+)\s*\n\s*\n+\s*(    def\s+test_[a-zA-Z0-9_]+\s*\()",
                    r"\1\n\2",
                    issue["match"],
                )

                # Replace in the content
                new_content = new_content.replace(issue["match"], fixed)
                modified = True

            elif issue["type"] == "incorrect_3":
                # Fix multiple markers on the same method
                if verbose:
                    print(
                        f"  Fixing multiple markers at lines {issue['line_start']}-{issue['line_end']}"
                    )

                # Extract the markers and method definition
                match = re.search(
                    r"(    @pytest\.mark\.[a-z_]+)\s*\n\s*(    @pytest\.mark\.[a-z_]+)\s*\n\s*(    def\s+test_[a-zA-Z0-9_]+\s*\()",
                    issue["match"],
                )
                if match:
                    marker1 = match.group(1)
                    marker2 = match.group(2)
                    method_def = match.group(3)

                    # Create the fixed version (keeping only the speed marker)
                    if "fast" in marker1 or "medium" in marker1 or "slow" in marker1:
                        fixed = f"{marker1}\n{method_def}"
                    elif "fast" in marker2 or "medium" in marker2 or "slow" in marker2:
                        fixed = f"{marker2}\n{method_def}"
                    else:
                        # If neither is a speed marker, keep the first one
                        fixed = f"{marker1}\n{method_def}"

                    # Replace in the content
                    new_content = new_content.replace(issue["match"], fixed)
                    modified = True

        if modified and not dry_run:
            with open(file_path, "w") as f:
                f.write(new_content)

        return modified

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def generate_report(
    results: dict[str, dict[str, list[dict[str, Any]]]],
    output_file: str = "marker_placement_report.json",
):
    """
    Generate a report of marker placement issues.

    Args:
        results: Dictionary of results by file
        output_file: Path to the output file
    """
    # Count issues by type
    issue_counts = {"function": 0, "class_method": 0, "total": 0}

    for file_path, issues in results.items():
        for issue_type, issue_list in issues.items():
            issue_counts[issue_type] += len(issue_list)
            issue_counts["total"] += len(issue_list)

    # Create the report
    report = {
        "summary": {
            "total_files": len(results),
            "files_with_issues": sum(
                1
                for file_path, issues in results.items()
                if sum(len(issue_list) for issue_list in issues.values()) > 0
            ),
            "issue_counts": issue_counts,
        },
        "issues_by_file": results,
    }

    # Write the report to a file
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total files analyzed: {report['summary']['total_files']}")
    print(f"  Files with issues: {report['summary']['files_with_issues']}")
    print(f"  Total issues: {report['summary']['issue_counts']['total']}")
    print(f"  Function issues: {report['summary']['issue_counts']['function']}")
    print(f"  Class method issues: {report['summary']['issue_counts']['class_method']}")


def verify_markers(file_path: str, verbose: bool = False) -> dict[str, Any]:
    """
    Verify that markers are correctly detected by the test collector.

    Args:
        file_path: Path to the file to verify
        verbose: Whether to show detailed information

    Returns:
        Dictionary of verification results
    """
    if verbose:
        print(f"Verifying markers in {file_path}...")

    try:
        # Get all tests in the file
        tests = collect_tests(file_path)

        # Check if each test has a marker
        results = {
            "total_tests": len(tests),
            "tests_with_markers": 0,
            "tests_without_markers": 0,
            "tests": {},
        }

        for test in tests:
            has_marker, marker = check_test_has_marker(test)

            results["tests"][test] = {"has_marker": has_marker, "marker": marker}

            if has_marker:
                results["tests_with_markers"] += 1
            else:
                results["tests_without_markers"] += 1

        return results

    except Exception as e:
        print(f"Error verifying markers in {file_path}: {e}")
        return {
            "total_tests": 0,
            "tests_with_markers": 0,
            "tests_without_markers": 0,
            "tests": {},
            "error": str(e),
        }


def main():
    """Main function."""
    args = parse_args()

    # Collect test files
    test_files = collect_test_files(
        category=args.category, module=args.module, use_cache=True
    )

    # Prioritize files
    test_files = prioritize_files(test_files, HIGH_PRIORITY_MODULES)

    # Limit the number of files to process
    if args.max_tests > 0 and len(test_files) > args.max_tests:
        print(f"Limiting to {args.max_tests} files (out of {len(test_files)} files)")
        test_files = test_files[: args.max_tests]

    # Process each file
    results = {}
    verification_results = {}
    modified_files = []

    for file_path in test_files:
        # Analyze the file for marker placement issues
        issues = analyze_file(file_path, STANDARD_PATTERNS, args.verbose)

        # Store the results
        results[file_path] = issues

        # Fix the file if needed and requested
        if args.fix and sum(len(issue_list) for issue_list in issues.values()) > 0:
            if fix_file(file_path, issues, args.dry_run, args.verbose):
                modified_files.append(file_path)

        # Verify markers if requested
        if args.verify:
            verification_results[file_path] = verify_markers(file_path, args.verbose)

    # Generate a report if requested
    if args.report:
        generate_report(results, "marker_placement_report.json")

        if args.verify:
            # Generate a verification report
            with open("marker_verification_report.json", "w") as f:
                json.dump(verification_results, f, indent=2)

            # Print verification summary
            total_tests = sum(
                result["total_tests"] for result in verification_results.values()
            )
            tests_with_markers = sum(
                result["tests_with_markers"] for result in verification_results.values()
            )
            tests_without_markers = sum(
                result["tests_without_markers"]
                for result in verification_results.values()
            )

            print("\nVerification Summary:")
            print(f"  Total tests: {total_tests}")
            print(
                f"  Tests with markers: {tests_with_markers} ({tests_with_markers / total_tests * 100:.2f}%)"
            )
            print(
                f"  Tests without markers: {tests_without_markers} ({tests_without_markers / total_tests * 100:.2f}%)"
            )

    # Print summary
    print("\nSummary:")
    print(f"  Total files processed: {len(test_files)}")
    print(
        f"  Files with issues: {len([f for f in results if sum(len(issue_list) for issue_list in results[f].values()) > 0])}"
    )

    if args.fix:
        if args.dry_run:
            print("\nNote: This was a dry run. Use without --dry-run to apply changes.")
        else:
            print(f"  Files modified: {len(modified_files)}")

    print("\nDone!")


if __name__ == "__main__":
    main()
