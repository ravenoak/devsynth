#!/usr/bin/env python
"""
Script to verify that test markers are correctly applied and recognized by pytest.

This script builds on fix_test_markers.py to verify that markers are correctly applied
and recognized by pytest. It provides detailed reporting of marker issues and can
fix common issues automatically.

Usage:
    python -m scripts.verify_test_markers [options]

Options:
    --directory DIR       Directory containing tests to verify (default: tests)
    --module MODULE       Specific module to verify (e.g., tests/unit/interface)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information about verification
    --fix                 Fix marker issues automatically
    --report              Generate a report of marker issues
    --report-file FILE    File to save the report to (default: test_markers_report.json)
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

# Import enhanced test utilities
from . import test_utils_extended as test_utils_ext

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")
CLASS_PATTERN = re.compile(r"class (Test\w+)\(")
PYTEST_IMPORT_PATTERN = re.compile(r"import\s+pytest|from\s+pytest\s+import")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify that test markers are correctly applied and recognized by pytest."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="tests",
        help="Directory containing tests to verify (default: tests)",
    )
    parser.add_argument(
        "-m", "--module", help="Specific module to verify (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed information about verification",
    )
    parser.add_argument(
        "--fix", action="store_true", help="Fix marker issues automatically"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a report of marker issues"
    )
    parser.add_argument(
        "--report-file",
        default="test_markers_report.json",
        help="File to save the report to (default: test_markers_report.json)",
    )
    return parser.parse_args()


def find_test_files(directory: str, max_depth: int = 5) -> List[Path]:
    """Find all test files in the given directory without unbounded traversal."""
    base_path = Path(directory).resolve()
    if base_path.is_file():
        return [base_path]

    test_files: List[Path] = []
    for path in base_path.rglob("test_*.py"):
        try:
            relative = path.relative_to(base_path)
        except ValueError:
            continue
        if len(relative.parts) <= max_depth:
            test_files.append(path)
    return test_files


def verify_file_markers(
    file_path: Path, verbose: bool = False, timeout: Optional[int] = 30
) -> Dict[str, Any]:
    """
    Verify markers in a test file.

    Args:
        file_path: Path to the test file
        verbose: Whether to show detailed information about verification

    Returns:
        Dictionary containing verification results
    """
    if verbose:
        print(f"Verifying markers in {file_path}...")

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    # Read the file content
    with open(file_path, "r") as f:
        content = f.read()
        lines = content.split("\n")

    # Check if pytest is imported
    has_pytest_import = bool(PYTEST_IMPORT_PATTERN.search(content))

    # Extract test functions
    test_functions = FUNCTION_PATTERN.findall(content)

    # Extract markers
    markers = {}
    current_markers = []

    for i, line in enumerate(lines):
        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)
            if current_markers:
                # Use the last marker if there are multiple
                markers[test_name] = current_markers[-1]
            current_markers = []

    # Check for misaligned markers
    misaligned_markers = []
    for i, line in enumerate(lines):
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            marker_type = marker_match.group(1)

            # Check if this marker is associated with a test function
            is_associated = False
            for j in range(i + 1, min(i + 10, len(lines))):
                func_match = FUNCTION_PATTERN.search(lines[j] if j < len(lines) else "")
                if func_match:
                    is_associated = True
                    break

            if not is_associated:
                misaligned_markers.append(
                    {"line": i, "marker": marker_type, "text": line.strip()}
                )

    # Check for duplicate markers
    duplicate_markers = []
    for test_name in test_functions:
        marker_count = 0
        for i, line in enumerate(lines):
            if f"def {test_name}(" in line:
                # Check for markers before this function
                for j in range(i - 1, max(0, i - 10), -1):
                    marker_match = MARKER_PATTERN.search(lines[j])
                    if marker_match:
                        marker_count += 1

        if marker_count > 1:
            duplicate_markers.append(
                {"test_name": test_name, "marker_count": marker_count}
            )

    # Check if markers are recognized by pytest
    recognized_markers = {}

    # First, check if pytest.ini has the markers registered
    pytest_ini_path = Path(os.path.join(os.path.dirname(file_path), "pytest.ini"))
    repo_root = None

    # Try to find pytest.ini by traversing up the directory tree
    current_dir = os.path.dirname(file_path)
    while current_dir and current_dir != "/":
        potential_ini = os.path.join(current_dir, "pytest.ini")
        if os.path.exists(potential_ini):
            pytest_ini_path = Path(potential_ini)
            repo_root = current_dir
            break
        current_dir = os.path.dirname(current_dir)

    markers_registered = {}
    if os.path.exists(pytest_ini_path):
        with open(pytest_ini_path, "r") as f:
            pytest_ini_content = f.read()
            for marker_type in ["fast", "medium", "slow"]:
                markers_registered[marker_type] = (
                    f"{marker_type}:" in pytest_ini_content
                )

    # Check each marker type
    for marker_type in ["fast", "medium", "slow"]:
        # Count markers of this type in the file
        marker_count = sum(1 for m in markers.values() if m == marker_type)

        if marker_count > 0:
            # Check if pytest recognizes these markers
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(file_path),
                f"-m={marker_type}",
                "--collect-only",
                "-q",  # Use quiet output for reliable parsing
            ]

            try:
                collect_result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                # Count tests collected with this marker
                collected_count = 0
                collected_tests = []

                # Parse the output to count collected tests and identify which tests were collected
                rel_path = os.path.relpath(file_path)
                for line in collect_result.stdout.split("\n"):
                    if str(file_path) in line or rel_path in line:
                        collected_count += 1
                        # Extract the test name from the output
                        test_parts = line.strip().split("::")
                        if len(test_parts) >= 2:
                            test_name = test_parts[-1]
                            if "(" in test_name:  # Handle parameterized tests
                                test_name = test_name.split("(")[0]
                            collected_tests.append(test_name)

                # Identify which tests have the marker but weren't collected
                uncollected_tests = []
                for test_name, marker in markers.items():
                    if marker == marker_type and test_name not in collected_tests:
                        uncollected_tests.append(test_name)

                recognized_markers[marker_type] = {
                    "file_count": marker_count,
                    "pytest_count": collected_count,
                    "recognized": collected_count == marker_count,
                    "registered_in_pytest_ini": markers_registered.get(
                        marker_type, False
                    ),
                    "uncollected_tests": uncollected_tests,
                }
            except Exception as e:
                recognized_markers[marker_type] = {
                    "file_count": marker_count,
                    "pytest_count": 0,
                    "recognized": False,
                    "registered_in_pytest_ini": markers_registered.get(
                        marker_type, False
                    ),
                    "error": str(e),
                    "uncollected_tests": [],
                }

    # Prepare verification results
    results = {
        "file_path": str(file_path),
        "has_pytest_import": has_pytest_import,
        "test_functions": len(test_functions),
        "markers": markers,
        "tests_with_markers": len(markers),
        "tests_without_markers": len(test_functions) - len(markers),
        "misaligned_markers": misaligned_markers,
        "duplicate_markers": duplicate_markers,
        "recognized_markers": recognized_markers,
        "issues": [],
    }

    # Identify issues
    if not has_pytest_import and len(markers) > 0:
        results["issues"].append(
            {
                "type": "missing_pytest_import",
                "message": "File has markers but no pytest import",
            }
        )

    if len(misaligned_markers) > 0:
        results["issues"].append(
            {
                "type": "misaligned_markers",
                "message": f"File has {len(misaligned_markers)} misaligned markers",
            }
        )

    if len(duplicate_markers) > 0:
        results["issues"].append(
            {
                "type": "duplicate_markers",
                "message": f"File has {len(duplicate_markers)} tests with duplicate markers",
            }
        )

    for marker_type, info in recognized_markers.items():
        if not info.get("recognized", False):
            results["issues"].append(
                {
                    "type": "unrecognized_markers",
                    "message": f"{marker_type} markers are not recognized by pytest ({info['file_count']} in file, {info['pytest_count']} recognized)",
                }
            )

    if verbose and results["issues"]:
        print(f"  Issues found in {file_path}:")
        for issue in results["issues"]:
            print(f"    - {issue['message']}")

    return results


def fix_marker_issues(
    file_path: Path,
    verification_results: Dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Fix marker issues in a test file.

    Args:
        file_path: Path to the test file
        verification_results: Dictionary containing verification results
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about fixes

    Returns:
        Dictionary containing fix results
    """
    if verbose:
        print(f"Fixing marker issues in {file_path}...")

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    # Read the file content
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Track changes
    changes = {
        "added_pytest_import": False,
        "fixed_misaligned_markers": 0,
        "fixed_duplicate_markers": 0,
        "total_changes": 0,
    }

    # Fix missing pytest import
    if (
        not verification_results["has_pytest_import"]
        and len(verification_results["markers"]) > 0
    ):
        # Find the best place to add the import
        import_line = -1
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_line = i

        if import_line >= 0:
            # Add import after the last import
            if verbose:
                print(f"  Adding pytest import after line {import_line+1}")

            if not dry_run:
                lines.insert(import_line + 1, "import pytest\n")

                # Update line numbers for subsequent issues
                for marker in verification_results.get("misaligned_markers", []):
                    if marker["line"] > import_line:
                        marker["line"] += 1

            changes["added_pytest_import"] = True
            changes["total_changes"] += 1
        else:
            # Add import at the beginning of the file
            if verbose:
                print(f"  Adding pytest import at the beginning of the file")

            if not dry_run:
                lines.insert(0, "import pytest\n\n")

                # Update line numbers for subsequent issues
                for marker in verification_results.get("misaligned_markers", []):
                    marker["line"] += 2

            changes["added_pytest_import"] = True
            changes["total_changes"] += 1

    # Fix misaligned markers
    for marker in verification_results.get("misaligned_markers", []):
        line_num = marker["line"]
        marker_type = marker["marker"]

        # Find the next test function after this marker
        next_func_line = None
        next_func_name = None

        for i in range(line_num + 1, min(line_num + 20, len(lines))):
            func_match = FUNCTION_PATTERN.search(lines[i] if i < len(lines) else "")
            if func_match:
                next_func_line = i
                next_func_name = func_match.group(1)
                break

        if next_func_line is not None:
            # Check if the function already has a speed marker
            has_speed_marker = False
            for i in range(next_func_line - 1, max(0, next_func_line - 10), -1):
                if MARKER_PATTERN.search(lines[i]):
                    has_speed_marker = True
                    break

            if has_speed_marker:
                # Function already has a speed marker, remove the misaligned one
                if verbose:
                    print(
                        f"  Removing misaligned marker at line {line_num+1}: {marker['text']}"
                    )

                if not dry_run:
                    lines[line_num] = ""

                changes["fixed_misaligned_markers"] += 1
                changes["total_changes"] += 1
            else:
                # Move the marker to just before the function
                if verbose:
                    print(
                        f"  Moving marker from line {line_num+1} to line {next_func_line+1}"
                    )

                if not dry_run:
                    # Remove the original marker
                    lines[line_num] = ""

                    # Add the marker before the function
                    indent = re.match(r"(\s*)", lines[next_func_line]).group(1)
                    lines.insert(
                        next_func_line, f"{indent}@pytest.mark.{marker_type}\n"
                    )

                    # Update line numbers for subsequent markers
                    for other_marker in verification_results.get(
                        "misaligned_markers", []
                    ):
                        if other_marker["line"] > line_num:
                            other_marker["line"] += 1

                changes["fixed_misaligned_markers"] += 1
                changes["total_changes"] += 1
        else:
            # No function found after this marker, remove it
            if verbose:
                print(
                    f"  Removing orphaned marker at line {line_num+1}: {marker['text']}"
                )

            if not dry_run:
                lines[line_num] = ""

            changes["fixed_misaligned_markers"] += 1
            changes["total_changes"] += 1

    # Fix duplicate markers
    for duplicate in verification_results.get("duplicate_markers", []):
        test_name = duplicate["test_name"]

        # Find the test function
        func_line = None
        for i, line in enumerate(lines):
            if f"def {test_name}(" in line:
                func_line = i
                break

        if func_line is not None:
            # Find all markers for this function
            markers_to_remove = []
            kept_marker = None

            for i in range(func_line - 1, max(0, func_line - 10), -1):
                marker_match = MARKER_PATTERN.search(lines[i])
                if marker_match:
                    if kept_marker is None:
                        kept_marker = marker_match.group(1)
                    else:
                        markers_to_remove.append(i)

            # Remove duplicate markers
            for i in sorted(markers_to_remove, reverse=True):
                if verbose:
                    print(
                        f"  Removing duplicate marker at line {i+1}: {lines[i].strip()}"
                    )

                if not dry_run:
                    lines[i] = ""

                changes["fixed_duplicate_markers"] += 1
                changes["total_changes"] += 1

    # Write changes back to the file
    if not dry_run and changes["total_changes"] > 0:
        with open(file_path, "w") as f:
            f.writelines(lines)

    return changes


def verify_directory_markers(
    directory: str,
    verbose: bool = False,
    progress_interval: int = 50,
    timeout: Optional[int] = 30,
) -> Dict[str, Any]:
    """
    Verify markers in all test files in a directory.

    Args:
        directory: Directory containing test files
        verbose: Whether to show detailed information about verification

    Returns:
        Dictionary containing verification results
    """
    print(f"Verifying markers in {directory}...")

    # Find all test files
    test_files = find_test_files(directory)

    if not test_files:
        print(f"No test files found in {directory}")
        return {"success": False, "error": f"No test files found in {directory}"}

    # Verify markers in each file
    results = {
        "directory": directory,
        "total_files": len(test_files),
        "files_with_issues": 0,
        "total_test_functions": 0,
        "total_markers": 0,
        "total_misaligned_markers": 0,
        "total_duplicate_markers": 0,
        "total_unrecognized_markers": 0,
        "marker_counts": {"fast": 0, "medium": 0, "slow": 0, "isolation": 0},
        "files": {},
    }

    start = time.time()
    for idx, file_path in enumerate(test_files, 1):
        file_results = verify_file_markers(file_path, verbose, timeout=timeout)

        # Update overall results
        results["total_test_functions"] += file_results["test_functions"]
        results["total_markers"] += file_results["tests_with_markers"]
        results["total_misaligned_markers"] += len(file_results["misaligned_markers"])
        results["total_duplicate_markers"] += len(file_results["duplicate_markers"])

        # Update marker counts
        for marker_type, count in file_results.get("recognized_markers", {}).items():
            results["marker_counts"][marker_type] = (
                results["marker_counts"].get(marker_type, 0) + count["file_count"]
            )
            if not count.get("recognized", False):
                results["total_unrecognized_markers"] += count["file_count"]

        # Check if file has issues
        if file_results["issues"]:
            results["files_with_issues"] += 1
            results["files"][str(file_path)] = file_results

        if idx % progress_interval == 0:
            elapsed = time.time() - start
            print(f"Processed {idx}/{len(test_files)} files ({elapsed:.1f}s elapsed)")
            start = time.time()

    return results


def fix_directory_markers(
    directory: str,
    verification_results: Dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Fix marker issues in all test files in a directory.

    Args:
        directory: Directory containing test files
        verification_results: Dictionary containing verification results
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about fixes

    Returns:
        Dictionary containing fix results
    """
    print(f"Fixing marker issues in {directory}...")

    # Track changes
    changes = {
        "total_files_fixed": 0,
        "total_pytest_imports_added": 0,
        "total_misaligned_markers_fixed": 0,
        "total_duplicate_markers_fixed": 0,
        "total_changes": 0,
        "files": {},
    }

    # Fix issues in each file
    for file_path_str, file_results in verification_results.get("files", {}).items():
        file_path = Path(file_path_str)

        if file_results["issues"]:
            file_changes = fix_marker_issues(file_path, file_results, dry_run, verbose)

            if file_changes["total_changes"] > 0:
                changes["total_files_fixed"] += 1
                changes["total_pytest_imports_added"] += (
                    1 if file_changes["added_pytest_import"] else 0
                )
                changes["total_misaligned_markers_fixed"] += file_changes[
                    "fixed_misaligned_markers"
                ]
                changes["total_duplicate_markers_fixed"] += file_changes[
                    "fixed_duplicate_markers"
                ]
                changes["total_changes"] += file_changes["total_changes"]
                changes["files"][file_path_str] = file_changes

    return changes


def generate_report(
    verification_results: Dict[str, Any],
    fix_results: Optional[Dict[str, Any]] = None,
    report_file: str = "test_markers_report.json",
) -> None:
    """
    Generate a report of marker issues.

    Args:
        verification_results: Dictionary containing verification results
        fix_results: Dictionary containing fix results (optional)
        report_file: File to save the report to
    """
    print(f"Generating report to {report_file}...")

    # Prepare report
    report = {
        "timestamp": datetime.now().isoformat(),
        "verification": verification_results,
    }

    if fix_results:
        report["fixes"] = fix_results

    # Save report
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to {report_file}")


def main():
    """Main function."""
    args = parse_args()

    # Determine the directory to verify
    directory = args.module if args.module else args.directory

    # Verify markers
    verification_results = verify_directory_markers(directory, args.verbose)

    # Print verification summary
    print("\nVerification Summary:")
    print(f"  Total files: {verification_results['total_files']}")
    print(f"  Files with issues: {verification_results['files_with_issues']}")
    print(f"  Total test functions: {verification_results['total_test_functions']}")
    print(
        f"  Functions with markers: {verification_results['total_markers']} ({verification_results['total_markers']/verification_results['total_test_functions']*100:.1f}%)"
    )
    print(f"  Misaligned markers: {verification_results['total_misaligned_markers']}")
    print(f"  Duplicate markers: {verification_results['total_duplicate_markers']}")
    print(
        f"  Unrecognized markers: {verification_results['total_unrecognized_markers']}"
    )
    print(f"  Marker counts:")
    print(f"    - Fast: {verification_results['marker_counts'].get('fast', 0)}")
    print(f"    - Medium: {verification_results['marker_counts'].get('medium', 0)}")
    print(f"    - Slow: {verification_results['marker_counts'].get('slow', 0)}")
    print(
        f"    - Isolation: {verification_results['marker_counts'].get('isolation', 0)}"
    )

    # Fix issues if requested
    fix_results = None
    if args.fix:
        fix_results = fix_directory_markers(
            directory, verification_results, args.dry_run, args.verbose
        )

        # Print fix summary
        action = "Would fix" if args.dry_run else "Fixed"
        print(f"\n{action} Issues Summary:")
        print(f"  Files fixed: {fix_results['total_files_fixed']}")
        print(f"  Pytest imports added: {fix_results['total_pytest_imports_added']}")
        print(
            f"  Misaligned markers fixed: {fix_results['total_misaligned_markers_fixed']}"
        )
        print(
            f"  Duplicate markers fixed: {fix_results['total_duplicate_markers_fixed']}"
        )
        print(f"  Total changes: {fix_results['total_changes']}")

    # Generate report if requested
    if args.report:
        generate_report(verification_results, fix_results, args.report_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
