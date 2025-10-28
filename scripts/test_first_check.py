#!/usr/bin/env python
"""
Pre-commit hook to enforce test-first development.

This script checks if new or modified Python files have corresponding test files.
It enforces the TDD/BDD approach by requiring tests to be written before implementation.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple


def get_staged_files() -> list[str]:
    """Get a list of staged files from git."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().split("\n")


def get_modified_python_files(staged_files: list[str]) -> list[str]:
    """Filter the list of staged files to only include Python files in src/."""
    return [
        file
        for file in staged_files
        if file.endswith(".py")
        and file.startswith("src/")
        and not file.endswith("__init__.py")
    ]


def get_expected_test_files(python_files: list[str]) -> list[str]:
    """Get the expected test files for the given Python files."""
    expected_test_files = []
    for file in python_files:
        # Convert src/devsynth/module/file.py to tests/unit/test_file.py
        parts = file.split("/")
        if len(parts) < 3:
            continue

        # Skip __init__.py files
        if parts[-1] == "__init__.py":
            continue

        # Get the file name without extension
        file_name = os.path.splitext(parts[-1])[0]

        # Check for unit tests
        unit_test_path = f"tests/unit/test_{file_name}.py"
        expected_test_files.append(unit_test_path)

        # Check for behavior tests if it's a user-facing feature
        if "adapters" in file or "cli" in file:
            behavior_test_path = f"tests/behavior/features/{file_name}.feature"
            expected_test_files.append(behavior_test_path)

    return expected_test_files


def check_test_files_exist(
    expected_test_files: list[str], staged_files: list[str]
) -> tuple[bool, list[str]]:
    """Check if the expected test files exist or are staged."""
    missing_tests = []
    for test_file in expected_test_files:
        # Check if the test file exists in the repository
        if not os.path.exists(test_file) and test_file not in staged_files:
            missing_tests.append(test_file)

    return len(missing_tests) == 0, missing_tests


def main(filenames: list[str]) -> int:
    """Main function to check if tests exist for the given files."""
    if not filenames:
        return 0

    # Get all staged files
    staged_files = get_staged_files()

    # Filter to only include Python files in src/
    python_files = get_modified_python_files(filenames)
    if not python_files:
        return 0

    # Get the expected test files
    expected_test_files = get_expected_test_files(python_files)

    # Check if the test files exist or are staged
    tests_exist, missing_tests = check_test_files_exist(
        expected_test_files, staged_files
    )

    if not tests_exist:
        print("Error: The following test files are missing:")
        for test_file in missing_tests:
            print(f"  - {test_file}")
        print(
            "\nPlease write tests before implementing functionality (TDD/BDD approach)."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
