#!/usr/bin/env python3
"""
Script to automate the full marker fixing process for all test files.

This script:
1. Fixes syntax errors in test files
2. Uses fix_test_markers.py to fix misaligned markers
3. Uses incremental_test_categorization.py with --force to add missing markers
4. Uses common_test_collector.py with --no-cache to verify marker detection

Usage:
    python scripts/fix_all_test_markers.py [options]

Options:
    --directory DIR       Directory containing tests to analyze (default: tests)
    --module MODULE       Specific module to analyze (e.g., tests/unit/interface)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed output
    --batch-size N        Number of tests to run in each batch (default: 20)
    --max-tests N         Maximum number of tests to analyze in this run (default: 100)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automate the full marker fixing process for all test files."
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
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of tests to run in each batch (default: 20)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=100,
        help="Maximum number of tests to analyze in this run (default: 100)",
    )
    return parser.parse_args()


def run_command(command: list[str], verbose: bool = False) -> tuple[int, str, str]:
    """
    Run a command and return its exit code, stdout, and stderr.

    Args:
        command: Command to run
        verbose: Whether to print the command and its output

    Returns:
        Tuple containing exit code, stdout, and stderr
    """
    if verbose:
        print(f"Running command: {' '.join(command)}")

    process = subprocess.run(command, capture_output=True, text=True)

    if verbose:
        print(f"Exit code: {process.returncode}")
        print(f"stdout: {process.stdout}")
        print(f"stderr: {process.stderr}")

    return process.returncode, process.stdout, process.stderr


def fix_syntax_errors(directory: str, verbose: bool = False) -> dict[str, Any]:
    """
    Fix syntax errors in test files.

    Args:
        directory: Directory containing tests to analyze
        verbose: Whether to show detailed output

    Returns:
        Dictionary containing results
    """
    print(f"\n=== Step 1: Fixing syntax errors in {directory} ===")

    # Run pytest to collect tests and identify files with syntax errors
    command = [sys.executable, "-m", "pytest", directory, "--collect-only", "-v"]

    exit_code, stdout, stderr = run_command(command, verbose)

    # Parse the output to identify files with syntax errors
    files_with_errors = []
    for line in stderr.split("\n"):
        if "SyntaxError" in line or "IndentationError" in line:
            # Extract file path from error message
            parts = line.split(":")
            if len(parts) >= 2:
                file_path = parts[0]
                if file_path.endswith(".py") and os.path.exists(file_path):
                    files_with_errors.append(file_path)

    # Remove duplicates
    files_with_errors = list(set(files_with_errors))

    print(f"Found {len(files_with_errors)} files with syntax errors")

    # Fix common syntax errors in each file
    fixed_files = []
    for file_path in files_with_errors:
        if verbose:
            print(f"\nFixing syntax errors in {file_path}")

        with open(file_path) as f:
            content = f.read()

        # Fix common syntax errors

        # 1. Fix indentation errors with import statements
        lines = content.split("\n")
        fixed_lines = []
        in_function = False
        current_indent = ""

        for line in lines:
            # Check if line starts a function definition
            if line.strip().startswith("def "):
                in_function = True
                current_indent = line[: line.index("def")]

            # Check if line is an import statement inside a function
            if in_function and (
                line.strip().startswith("import ") or line.strip().startswith("from ")
            ):
                # If indented, unindent it
                if line.startswith(current_indent + "    "):
                    fixed_lines.append(line[len(current_indent) + 4 :])
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        fixed_content = "\n".join(fixed_lines)

        # 2. Fix missing pytest imports
        if "pytest.mark" in fixed_content and "import pytest" not in fixed_content:
            # Add pytest import after other imports
            import_lines = []
            non_import_lines = []

            for line in fixed_lines:
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    import_lines.append(line)
                else:
                    non_import_lines.append(line)

            # Add pytest import after other imports
            import_lines.append("import pytest")

            fixed_content = "\n".join(import_lines + non_import_lines)

        # Write fixed content back to the file
        if fixed_content != content:
            if not args.dry_run:
                with open(file_path, "w") as f:
                    f.write(fixed_content)
            fixed_files.append(file_path)

    print(f"Fixed syntax errors in {len(fixed_files)} files")

    return {"files_with_errors": files_with_errors, "fixed_files": fixed_files}


def fix_misaligned_markers(
    directory: str, dry_run: bool = False, verbose: bool = False
) -> dict[str, Any]:
    """
    Fix misaligned markers in test files.

    Args:
        directory: Directory containing tests to analyze
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed output

    Returns:
        Dictionary containing results
    """
    print(f"\n=== Step 2: Fixing misaligned markers in {directory} ===")

    # Run fix_test_markers.py to fix misaligned markers
    command = [
        sys.executable,
        "scripts/fix_test_markers.py",
        "--directory",
        directory,
        "--fix-all",
    ]

    if dry_run:
        command.append("--dry-run")

    if verbose:
        command.append("--verbose")

    exit_code, stdout, stderr = run_command(command, verbose)

    # Parse the output to get the results
    fixed_misaligned = 0
    fixed_duplicates = 0
    fixed_inconsistent = 0
    added_missing = 0

    for line in stdout.split("\n"):
        if "Fix " in line and "misaligned markers" in line:
            try:
                fixed_misaligned = int(line.split("Fix ")[1].split(" misaligned")[0])
            except (IndexError, ValueError):
                pass

        if "Fix " in line and "duplicate markers" in line:
            try:
                fixed_duplicates = int(line.split("Fix ")[1].split(" duplicate")[0])
            except (IndexError, ValueError):
                pass

        if "Fix " in line and "inconsistent markers" in line:
            try:
                fixed_inconsistent = int(
                    line.split("Fix ")[1].split(" inconsistent")[0]
                )
            except (IndexError, ValueError):
                pass

        if "Add " in line and "missing markers" in line:
            try:
                added_missing = int(line.split("Add ")[1].split(" missing")[0])
            except (IndexError, ValueError):
                pass

    print(f"Fixed {fixed_misaligned} misaligned markers")
    print(f"Fixed {fixed_duplicates} duplicate markers")
    print(f"Fixed {fixed_inconsistent} inconsistent markers")
    print(f"Added {added_missing} missing markers")

    return {
        "fixed_misaligned": fixed_misaligned,
        "fixed_duplicates": fixed_duplicates,
        "fixed_inconsistent": fixed_inconsistent,
        "added_missing": added_missing,
    }


def add_missing_markers(
    directory: str,
    batch_size: int = 20,
    max_tests: int = 100,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Add missing markers to test files.

    Args:
        directory: Directory containing tests to analyze
        batch_size: Number of tests to run in each batch
        max_tests: Maximum number of tests to analyze in this run
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed output

    Returns:
        Dictionary containing results
    """
    print(f"\n=== Step 3: Adding missing markers in {directory} ===")

    # Run incremental_test_categorization.py to add missing markers
    command = [
        sys.executable,
        "scripts/incremental_test_categorization.py",
        "--directory",
        directory,
        "--batch-size",
        str(batch_size),
        "--max-tests",
        str(max_tests),
        "--force",
    ]

    if not dry_run:
        command.append("--update")

    exit_code, stdout, stderr = run_command(command, verbose)

    # Parse the output to get the results
    added = 0
    updated = 0
    unchanged = 0

    for line in stdout.split("\n"):
        if "Add " in line and "markers, update " in line and "markers, leave " in line:
            try:
                parts = line.split("Add ")[1].split(" markers, update ")
                added = int(parts[0])
                parts = parts[1].split(" markers, leave ")
                updated = int(parts[0])
                unchanged = int(parts[1].split(" markers")[0])
            except (IndexError, ValueError):
                pass

    print(f"Added {added} markers")
    print(f"Updated {updated} markers")
    print(f"Left {unchanged} markers unchanged")

    return {"added": added, "updated": updated, "unchanged": unchanged}


def verify_marker_detection(verbose: bool = False) -> dict[str, Any]:
    """
    Verify marker detection by common_test_collector.py.

    Args:
        verbose: Whether to show detailed output

    Returns:
        Dictionary containing results
    """
    print("\n=== Step 4: Verifying marker detection ===")

    # Run common_test_collector.py to verify marker detection
    command = [
        sys.executable,
        "scripts/common_test_collector.py",
        "--marker-counts",
        "--no-cache",
    ]

    exit_code, stdout, stderr = run_command(command, verbose)

    # Parse the output to get the marker counts
    marker_counts = {
        "unit": {"fast": 0, "medium": 0, "slow": 0},
        "integration": {"fast": 0, "medium": 0, "slow": 0},
        "behavior": {"fast": 0, "medium": 0, "slow": 0},
        "performance": {"fast": 0, "medium": 0, "slow": 0},
        "property": {"fast": 0, "medium": 0, "slow": 0},
        "total": {"fast": 0, "medium": 0, "slow": 0},
    }

    current_category = None

    for line in stdout.split("\n"):
        line = line.strip()

        if line.endswith(":"):
            current_category = line[:-1]
        elif current_category and ":" in line:
            marker_type, count = line.split(":")
            marker_type = marker_type.strip()
            count = int(count.strip())

            if (
                current_category in marker_counts
                and marker_type in marker_counts[current_category]
            ):
                marker_counts[current_category][marker_type] = count

    # Print marker counts
    print("Marker counts:")
    for category, counts in marker_counts.items():
        print(f"  {category}:")
        for marker_type, count in counts.items():
            print(f"    {marker_type}: {count}")

    return marker_counts


def main():
    """Main function."""
    global args
    args = parse_args()

    # Determine the directory to analyze
    directory = args.module if args.module else args.directory

    print(f"Analyzing tests in {directory}...")

    # Step 1: Fix syntax errors
    syntax_results = fix_syntax_errors(directory, args.verbose)

    # Step 2: Fix misaligned markers
    marker_results = fix_misaligned_markers(directory, args.dry_run, args.verbose)

    # Step 3: Add missing markers
    categorization_results = add_missing_markers(
        directory, args.batch_size, args.max_tests, args.dry_run, args.verbose
    )

    # Step 4: Verify marker detection
    detection_results = verify_marker_detection(args.verbose)

    # Print summary
    print("\n=== Summary ===")
    print(f"Fixed syntax errors in {len(syntax_results['fixed_files'])} files")
    print(f"Fixed {marker_results['fixed_misaligned']} misaligned markers")
    print(f"Fixed {marker_results['fixed_duplicates']} duplicate markers")
    print(f"Fixed {marker_results['fixed_inconsistent']} inconsistent markers")
    print(f"Added {categorization_results['added']} markers")
    print(f"Updated {categorization_results['updated']} markers")
    print(f"Left {categorization_results['unchanged']} markers unchanged")
    print(f"Detected {sum(detection_results['total'].values())} markers in total")

    print("\nDone!")


if __name__ == "__main__":
    main()
