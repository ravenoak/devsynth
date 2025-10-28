#!/usr/bin/env python
"""
Script to fix misaligned test markers in test files.

This script addresses issues with marker placement in test files by:
1. Identifying test files with misaligned markers
2. Analyzing the structure of test files more robustly
3. Fixing the placement of markers to ensure they're correctly associated with test functions
4. Handling different code formatting styles

Usage:
    python scripts/fix_test_markers.py [options]

Options:
    --directory DIR       Directory containing tests to analyze (default: tests)
    --module MODULE       Specific module to analyze (e.g., tests/unit/interface)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information about changes
    --fix-all             Fix all marker issues, not just misaligned markers
    --report              Generate a report of marker issues
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")
CLASS_PATTERN = re.compile(r"class (Test\w+)\(")
DECORATOR_PATTERN = re.compile(r"@\w+(\.\w+)*")
IMPORT_PATTERN = re.compile(r"import\s+\w+|from\s+\w+\s+import")
DOCSTRING_START_PATTERN = re.compile(r'"""|\'\'\'\s*$')
DOCSTRING_END_PATTERN = re.compile(r'"""|\'\'\'')
BLANK_LINE_PATTERN = re.compile(r"^\s*$")
COMMENT_PATTERN = re.compile(r"^\s*#")

# Cache file for test files with marker issues
CACHE_FILE = ".test_marker_issues.json"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix misaligned test markers in test files."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="tests",
        help="Directory containing tests to analyze (default: tests)",
    )
    parser.add_argument(
        "-m", "--module", help="Specific module to analyze (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed information about changes",
    )
    parser.add_argument(
        "--fix-all",
        action="store_true",
        help="Fix all marker issues, not just misaligned markers",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a report of marker issues"
    )
    return parser.parse_args()


def find_test_files(directory: str) -> list[Path]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file_structure(file_path: Path) -> dict[str, Any]:
    """
    Analyze a test file to extract its structure, including imports, classes, functions,
    decorators, docstrings, and comments.

    Returns:
        Dictionary containing the file structure
    """
    with open(file_path) as f:
        lines = f.readlines()

    structure = {
        "imports": [],
        "classes": {},
        "functions": {},
        "decorators": {},
        "docstrings": {},
        "comments": [],
        "blank_lines": [],
        "lines": lines,
    }

    in_docstring = False
    docstring_start = -1
    current_class = None

    for i, line in enumerate(lines):
        # Track docstrings
        if DOCSTRING_START_PATTERN.search(line) and not in_docstring:
            in_docstring = True
            docstring_start = i
        elif DOCSTRING_END_PATTERN.search(line) and in_docstring:
            in_docstring = False
            structure["docstrings"][docstring_start] = i

        # Skip processing if in a docstring
        if in_docstring:
            continue

        # Track imports
        if IMPORT_PATTERN.search(line):
            structure["imports"].append(i)

        # Track blank lines
        if BLANK_LINE_PATTERN.match(line):
            structure["blank_lines"].append(i)

        # Track comments
        if COMMENT_PATTERN.match(line):
            structure["comments"].append(i)

        # Track classes
        class_match = CLASS_PATTERN.search(line)
        if class_match:
            class_name = class_match.group(1)
            structure["classes"][class_name] = {"line": i, "functions": {}}
            current_class = class_name

        # Track functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            func_name = func_match.group(1)
            if current_class:
                structure["classes"][current_class]["functions"][func_name] = {
                    "line": i,
                    "decorators": [],
                }
            else:
                structure["functions"][func_name] = {"line": i, "decorators": []}

        # Track decorators
        decorator_match = DECORATOR_PATTERN.match(line.strip())
        if decorator_match:
            structure["decorators"][i] = line.strip()

            # Associate decorator with the next function or class
            next_func = None
            for j in range(i + 1, min(i + 10, len(lines))):
                func_match = FUNCTION_PATTERN.search(lines[j])
                if func_match:
                    next_func = func_match.group(1)
                    if current_class:
                        if (
                            next_func
                            in structure["classes"][current_class]["functions"]
                        ):
                            structure["classes"][current_class]["functions"][next_func][
                                "decorators"
                            ].append(i)
                    else:
                        if next_func in structure["functions"]:
                            structure["functions"][next_func]["decorators"].append(i)
                    break

    return structure


def identify_marker_issues(
    file_path: Path, structure: dict[str, Any]
) -> dict[str, Any]:
    """
    Identify marker issues in a test file.

    Args:
        file_path: Path to the test file
        structure: Dictionary containing the file structure

    Returns:
        Dictionary containing marker issues
    """
    issues = {
        "misaligned_markers": [],
        "missing_markers": [],
        "duplicate_markers": [],
        "inconsistent_markers": [],
    }

    lines = structure["lines"]

    # Check for misaligned markers
    for i, line in enumerate(lines):
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            marker_type = marker_match.group(1)

            # Check if this marker is associated with a function
            is_associated = False
            for func_name, func_info in structure["functions"].items():
                if i in func_info["decorators"]:
                    is_associated = True
                    break

            if not is_associated:
                for class_name, class_info in structure["classes"].items():
                    for func_name, func_info in class_info["functions"].items():
                        if i in func_info["decorators"]:
                            is_associated = True
                            break

            if not is_associated:
                # This marker is not properly associated with a function
                issues["misaligned_markers"].append(
                    {"line": i, "marker": marker_type, "text": line.strip()}
                )

    # Check for missing markers (functions without speed markers)
    for func_name, func_info in structure["functions"].items():
        has_speed_marker = False
        for decorator_line in func_info["decorators"]:
            if MARKER_PATTERN.search(lines[decorator_line]):
                has_speed_marker = True
                break

        if not has_speed_marker:
            issues["missing_markers"].append(
                {"line": func_info["line"], "function": func_name}
            )

    for class_name, class_info in structure["classes"].items():
        for func_name, func_info in class_info["functions"].items():
            has_speed_marker = False
            for decorator_line in func_info["decorators"]:
                if MARKER_PATTERN.search(lines[decorator_line]):
                    has_speed_marker = True
                    break

            if not has_speed_marker:
                issues["missing_markers"].append(
                    {"line": func_info["line"], "function": f"{class_name}.{func_name}"}
                )

    # Check for duplicate markers (functions with multiple speed markers)
    for func_name, func_info in structure["functions"].items():
        speed_markers = []
        for decorator_line in func_info["decorators"]:
            marker_match = MARKER_PATTERN.search(lines[decorator_line])
            if marker_match:
                speed_markers.append(marker_match.group(1))

        if len(speed_markers) > 1:
            issues["duplicate_markers"].append(
                {
                    "line": func_info["line"],
                    "function": func_name,
                    "markers": speed_markers,
                }
            )

    for class_name, class_info in structure["classes"].items():
        for func_name, func_info in class_info["functions"].items():
            speed_markers = []
            for decorator_line in func_info["decorators"]:
                marker_match = MARKER_PATTERN.search(lines[decorator_line])
                if marker_match:
                    speed_markers.append(marker_match.group(1))

            if len(speed_markers) > 1:
                issues["duplicate_markers"].append(
                    {
                        "line": func_info["line"],
                        "function": f"{class_name}.{func_name}",
                        "markers": speed_markers,
                    }
                )

    # Check for inconsistent markers (different markers for similar functions)
    function_markers = {}
    for func_name, func_info in structure["functions"].items():
        for decorator_line in func_info["decorators"]:
            marker_match = MARKER_PATTERN.search(lines[decorator_line])
            if marker_match:
                function_markers[func_name] = marker_match.group(1)

    for class_name, class_info in structure["classes"].items():
        for func_name, func_info in class_info["functions"].items():
            for decorator_line in func_info["decorators"]:
                marker_match = MARKER_PATTERN.search(lines[decorator_line])
                if marker_match:
                    function_markers[f"{class_name}.{func_name}"] = marker_match.group(
                        1
                    )

    # Group functions by name pattern
    function_groups = {}
    for func_name in function_markers:
        # Extract the base name (without test_ prefix)
        base_name = func_name.replace("test_", "")
        if "." in base_name:
            # For class methods, use the method name
            base_name = base_name.split(".")[-1]

        # Group by the first part of the name (before any underscores)
        group_name = base_name.split("_")[0]
        if group_name not in function_groups:
            function_groups[group_name] = []
        function_groups[group_name].append(func_name)

    # Check for inconsistent markers within groups
    for group_name, funcs in function_groups.items():
        if len(funcs) > 1:
            markers = {
                function_markers.get(func, None)
                for func in funcs
                if func in function_markers
            }
            if len(markers) > 1 and None not in markers:
                issues["inconsistent_markers"].append(
                    {"group": group_name, "functions": funcs, "markers": list(markers)}
                )

    return issues


def fix_misaligned_markers(
    file_path: Path,
    structure: dict[str, Any],
    issues: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """
    Fix misaligned markers in a test file.

    Args:
        file_path: Path to the test file
        structure: Dictionary containing the file structure
        issues: Dictionary containing marker issues
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about changes

    Returns:
        Tuple containing counts of (fixed, removed, unchanged) markers
    """
    fixed = 0
    removed = 0
    unchanged = 0

    if not issues["misaligned_markers"]:
        if verbose:
            print(f"No misaligned markers found in {file_path}")
        return fixed, removed, unchanged

    lines = structure["lines"].copy()

    # Process misaligned markers
    for issue in issues["misaligned_markers"]:
        line_num = issue["line"]
        marker_type = issue["marker"]

        # Find the next test function after this marker
        next_func_line = None
        next_func_name = None

        for i in range(line_num + 1, min(line_num + 20, len(lines))):
            func_match = FUNCTION_PATTERN.search(lines[i])
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
                        f"Removing misaligned marker at {file_path}:{line_num+1} - {issue['text']}"
                    )

                if not dry_run:
                    lines[line_num] = ""
                removed += 1
            else:
                # Move the marker to just before the function
                if verbose:
                    print(
                        f"Moving marker from {file_path}:{line_num+1} to {file_path}:{next_func_line}"
                    )

                if not dry_run:
                    # Remove the original marker
                    lines[line_num] = ""

                    # Add the marker before the function
                    indent = re.match(r"(\s*)", lines[next_func_line]).group(1)
                    lines.insert(
                        next_func_line, f"{indent}@pytest.mark.{marker_type}\n"
                    )

                    # Update line numbers for subsequent issues
                    for other_issue in issues["misaligned_markers"]:
                        if other_issue["line"] > line_num:
                            other_issue["line"] += 1
                fixed += 1
        else:
            # No function found after this marker, remove it
            if verbose:
                print(
                    f"Removing orphaned marker at {file_path}:{line_num+1} - {issue['text']}"
                )

            if not dry_run:
                lines[line_num] = ""
            removed += 1

    # Write changes back to the file
    if not dry_run and (fixed > 0 or removed > 0):
        with open(file_path, "w") as f:
            f.writelines(lines)

    return fixed, removed, unchanged


def fix_all_marker_issues(
    file_path: Path,
    structure: dict[str, Any],
    issues: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int, int]:
    """
    Fix all marker issues in a test file.

    Args:
        file_path: Path to the test file
        structure: Dictionary containing the file structure
        issues: Dictionary containing marker issues
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about changes

    Returns:
        Tuple containing counts of (fixed_misaligned, fixed_duplicates, fixed_inconsistent, added_missing)
    """
    # First fix misaligned markers
    fixed_misaligned, removed, unchanged = fix_misaligned_markers(
        file_path, structure, issues, dry_run, verbose
    )

    # Reload the file structure after fixing misaligned markers
    if fixed_misaligned > 0 and not dry_run:
        structure = analyze_test_file_structure(file_path)
        issues = identify_marker_issues(file_path, structure)

    lines = structure["lines"].copy()
    fixed_duplicates = 0
    fixed_inconsistent = 0
    added_missing = 0

    # Fix duplicate markers
    for issue in issues["duplicate_markers"]:
        line_num = issue["line"]
        func_name = issue["function"]
        markers = issue["markers"]

        if verbose:
            print(
                f"Fixing duplicate markers for {func_name} at {file_path}:{line_num+1} - {markers}"
            )

        # Find all decorator lines for this function
        decorator_lines = []
        if "." in func_name:
            # Class method
            class_name, method_name = func_name.split(".")
            if (
                class_name in structure["classes"]
                and method_name in structure["classes"][class_name]["functions"]
            ):
                decorator_lines = structure["classes"][class_name]["functions"][
                    method_name
                ]["decorators"]
        else:
            # Module function
            if func_name in structure["functions"]:
                decorator_lines = structure["functions"][func_name]["decorators"]

        # Keep only the first speed marker
        kept_marker = None
        for i, decorator_line in enumerate(decorator_lines):
            marker_match = MARKER_PATTERN.search(lines[decorator_line])
            if marker_match:
                if kept_marker is None:
                    kept_marker = marker_match.group(1)
                else:
                    # Remove this duplicate marker
                    if verbose:
                        print(
                            f"Removing duplicate marker at {file_path}:{decorator_line+1} - {lines[decorator_line].strip()}"
                        )

                    if not dry_run:
                        lines[decorator_line] = ""
                    fixed_duplicates += 1

    # Fix inconsistent markers (optional, as this might require more context)
    # For now, we'll just report them

    # Add missing markers (optional, as this requires determining the appropriate marker)
    # For now, we'll just report them

    # Write changes back to the file
    if not dry_run and fixed_duplicates > 0:
        with open(file_path, "w") as f:
            f.writelines(lines)

    return fixed_misaligned, fixed_duplicates, fixed_inconsistent, added_missing


def generate_report(
    issues_by_file: dict[str, dict[str, Any]],
    output_file: str = "test_marker_issues_report.json",
):
    """
    Generate a report of marker issues.

    Args:
        issues_by_file: Dictionary mapping file paths to issues
        output_file: Path to the output file
    """
    report = {
        "summary": {
            "total_files": len(issues_by_file),
            "files_with_issues": sum(
                1
                for issues in issues_by_file.values()
                if any(len(v) > 0 for v in issues.values())
            ),
            "total_issues": sum(
                sum(len(v) for v in issues.values())
                for issues in issues_by_file.values()
            ),
            "misaligned_markers": sum(
                len(issues["misaligned_markers"]) for issues in issues_by_file.values()
            ),
            "missing_markers": sum(
                len(issues["missing_markers"]) for issues in issues_by_file.values()
            ),
            "duplicate_markers": sum(
                len(issues["duplicate_markers"]) for issues in issues_by_file.values()
            ),
            "inconsistent_markers": sum(
                len(issues["inconsistent_markers"])
                for issues in issues_by_file.values()
            ),
        },
        "issues_by_file": {
            str(file_path): issues
            for file_path, issues in issues_by_file.items()
            if any(len(v) > 0 for v in issues.values())
        },
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total files analyzed: {report['summary']['total_files']}")
    print(f"  Files with issues: {report['summary']['files_with_issues']}")
    print(f"  Total issues: {report['summary']['total_issues']}")
    print(f"  Misaligned markers: {report['summary']['misaligned_markers']}")
    print(f"  Missing markers: {report['summary']['missing_markers']}")
    print(f"  Duplicate markers: {report['summary']['duplicate_markers']}")
    print(f"  Inconsistent markers: {report['summary']['inconsistent_markers']}")


def main():
    """Main function."""
    args = parse_args()

    # Determine the directory to analyze
    directory = args.module if args.module else args.directory

    print(f"Analyzing test files in {directory}...")

    # Find test files
    test_files = find_test_files(directory)
    print(f"Found {len(test_files)} test files")

    # Analyze test files
    issues_by_file = {}
    total_misaligned = 0
    total_missing = 0
    total_duplicate = 0
    total_inconsistent = 0

    for file_path in test_files:
        structure = analyze_test_file_structure(file_path)
        issues = identify_marker_issues(file_path, structure)

        misaligned = len(issues["misaligned_markers"])
        missing = len(issues["missing_markers"])
        duplicate = len(issues["duplicate_markers"])
        inconsistent = len(issues["inconsistent_markers"])

        total_misaligned += misaligned
        total_missing += missing
        total_duplicate += duplicate
        total_inconsistent += inconsistent

        if misaligned > 0 or missing > 0 or duplicate > 0 or inconsistent > 0:
            issues_by_file[file_path] = issues

            if args.verbose:
                print(f"\nIssues in {file_path}:")
                if misaligned > 0:
                    print(f"  Misaligned markers: {misaligned}")
                if missing > 0:
                    print(f"  Missing markers: {missing}")
                if duplicate > 0:
                    print(f"  Duplicate markers: {duplicate}")
                if inconsistent > 0:
                    print(f"  Inconsistent markers: {inconsistent}")

    print(f"\nSummary:")
    print(f"  Files with issues: {len(issues_by_file)} out of {len(test_files)}")
    print(f"  Misaligned markers: {total_misaligned}")
    print(f"  Missing markers: {total_missing}")
    print(f"  Duplicate markers: {total_duplicate}")
    print(f"  Inconsistent markers: {total_inconsistent}")

    # Fix issues
    if args.fix_all:
        print("\nFixing all marker issues...")

        total_fixed_misaligned = 0
        total_fixed_duplicates = 0
        total_fixed_inconsistent = 0
        total_added_missing = 0

        for file_path, issues in issues_by_file.items():
            structure = analyze_test_file_structure(file_path)
            fixed_misaligned, fixed_duplicates, fixed_inconsistent, added_missing = (
                fix_all_marker_issues(
                    file_path, structure, issues, args.dry_run, args.verbose
                )
            )

            total_fixed_misaligned += fixed_misaligned
            total_fixed_duplicates += fixed_duplicates
            total_fixed_inconsistent += fixed_inconsistent
            total_added_missing += added_missing

        action = "Would " if args.dry_run else ""
        print(f"\n{action}Fix {total_fixed_misaligned} misaligned markers")
        print(f"{action}Fix {total_fixed_duplicates} duplicate markers")
        print(f"{action}Fix {total_fixed_inconsistent} inconsistent markers")
        print(f"{action}Add {total_added_missing} missing markers")
    else:
        print("\nFixing misaligned markers...")

        total_fixed = 0
        total_removed = 0
        total_unchanged = 0

        for file_path, issues in issues_by_file.items():
            structure = analyze_test_file_structure(file_path)
            fixed, removed, unchanged = fix_misaligned_markers(
                file_path, structure, issues, args.dry_run, args.verbose
            )

            total_fixed += fixed
            total_removed += removed
            total_unchanged += unchanged

        action = "Would " if args.dry_run else ""
        print(f"\n{action}Fix {total_fixed} misaligned markers")
        print(f"{action}Remove {total_removed} orphaned markers")
        print(f"{action}Leave {total_unchanged} markers unchanged")

    # Generate report
    if args.report:
        generate_report(issues_by_file)

    print("\nDone!")


if __name__ == "__main__":
    main()
