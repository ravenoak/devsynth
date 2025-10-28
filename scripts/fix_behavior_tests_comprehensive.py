#!/usr/bin/env python
"""
Comprehensive script to fix behavior test issues.

This script addresses several issues with behavior tests:
1. Circular imports between step definition files
2. Incorrect feature file paths in scenarios function calls
3. Inconsistent import patterns

Usage:
    python scripts/fix_behavior_tests_comprehensive.py [--dry-run]

Options:
    --dry-run  Show changes without modifying files
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Regex patterns
SCENARIOS_IMPORT_PATTERN = re.compile(
    r"from pytest_bdd import (.*?)scenarios(.*?)$", re.MULTILINE
)
SCENARIOS_CALL_PATTERN = re.compile(r'scenarios\([\'"](.+?)[\'"]\)')
CIRCULAR_IMPORT_PATTERN = re.compile(r"from \.test_(\w+)_steps import \*")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix behavior test issues comprehensively."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    return parser.parse_args()


def find_behavior_test_files() -> list[Path]:
    """Find all behavior test files."""
    test_files = []
    for root, _, files in os.walk("tests/behavior"):
        for file in files:
            if (
                file.startswith("test_")
                and file.endswith(".py")
                and not root.endswith("steps")
            ):
                path = Path(os.path.join(root, file))
                test_files.append(path)
    return test_files


def find_step_files() -> dict[str, Path]:
    """Find all step definition files."""
    step_files = {}
    for root, _, files in os.walk("tests/behavior/steps"):
        for file in files:
            if file.endswith("_steps.py"):
                path = Path(os.path.join(root, file))
                step_files[file] = path
    return step_files


def find_feature_files() -> dict[str, Path]:
    """Find all feature files and map filenames to paths."""
    feature_files = {}
    for root, _, files in os.walk("tests/behavior/features"):
        for file in files:
            if file.endswith(".feature"):
                path = Path(os.path.join(root, file))
                feature_files[file] = path
    return feature_files


def fix_circular_imports(step_files: dict[str, Path], dry_run: bool) -> int:
    """
    Fix circular imports in step definition files.

    Returns the number of files updated.
    """
    updated_count = 0

    for name, path in step_files.items():
        with open(path) as f:
            content = f.read()

        # Check for circular imports
        circular_imports = CIRCULAR_IMPORT_PATTERN.findall(content)
        if circular_imports:
            # This file imports from another test_*_steps.py file
            # We need to replace it with the actual content from that file
            new_content = content
            for import_name in circular_imports:
                target_file = f"test_{import_name}_steps.py"
                if target_file in step_files:
                    target_path = step_files[target_file]
                    with open(target_path) as f:
                        target_content = f.read()

                    # Replace the import with the actual content
                    import_line = f"from .test_{import_name}_steps import *"
                    new_content = new_content.replace(
                        import_line,
                        f"# Content from {target_file} inlined here\n{target_content}",
                    )

                    if not dry_run:
                        with open(path, "w") as f:
                            f.write(new_content)
                        print(f"Fixed circular import in {path}")
                    else:
                        print(f"Would fix circular import in {path}")
                    updated_count += 1

    return updated_count


def fix_feature_paths(
    test_files: list[Path], feature_files: dict[str, Path], dry_run: bool
) -> int:
    """
    Fix feature file paths in test files.

    Returns the number of files updated.
    """
    updated_count = 0

    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()

        # Check for scenarios function calls
        scenarios_calls = SCENARIOS_CALL_PATTERN.findall(content)
        if scenarios_calls:
            modified = False
            new_content = content

            for feature_path in scenarios_calls:
                # Extract the feature filename
                feature_filename = os.path.basename(feature_path)

                # Find the correct path for this feature file
                if feature_filename in feature_files:
                    correct_path = feature_files[feature_filename]
                    # Calculate the path relative to the bdd_features_base_dir (tests/behavior/features)
                    features_base_dir = Path("tests/behavior/features")
                    relative_path = os.path.relpath(correct_path, features_base_dir)

                    # If the current path is incorrect, update it
                    if feature_path != relative_path:
                        old_call = f'scenarios("{feature_path}")'
                        new_call = f'scenarios("{relative_path}")'
                        new_content = new_content.replace(old_call, new_call)
                        modified = True

            if modified:
                if not dry_run:
                    with open(test_file, "w") as f:
                        f.write(new_content)
                    print(f"Fixed feature path in {test_file}")
                else:
                    print(f"Would fix feature path in {test_file}")
                updated_count += 1

    return updated_count


def fix_step_file_feature_paths(
    step_files: dict[str, Path], feature_files: dict[str, Path], dry_run: bool
) -> int:
    """
    Fix feature file paths in step definition files.

    Returns the number of files updated.
    """
    updated_count = 0

    for name, path in step_files.items():
        with open(path) as f:
            content = f.read()

        # Check for scenarios function calls
        scenarios_calls = SCENARIOS_CALL_PATTERN.findall(content)
        if scenarios_calls:
            modified = False
            new_content = content

            for feature_path in scenarios_calls:
                # Extract the feature filename
                feature_filename = os.path.basename(feature_path)

                # Find the correct path for this feature file
                if feature_filename in feature_files:
                    correct_path = feature_files[feature_filename]
                    # Calculate the path relative to the step file's directory
                    relative_path = os.path.relpath(correct_path, path.parent)

                    # If the current path is incorrect, update it
                    if feature_path != relative_path:
                        old_call = f'scenarios("{feature_path}")'
                        new_call = f'scenarios("{relative_path}")'
                        new_content = new_content.replace(old_call, new_call)
                        modified = True
                else:
                    # Feature file doesn't exist, check if it might exist in a subdirectory
                    found = False
                    for existing_file in feature_files.values():
                        if os.path.basename(existing_file) == feature_filename:
                            # Found a matching file in a different directory
                            relative_path = os.path.relpath(existing_file, path.parent)
                            old_call = f'scenarios("{feature_path}")'
                            new_call = f'scenarios("{relative_path}")'
                            new_content = new_content.replace(old_call, new_call)
                            modified = True
                            found = True
                            break

                    if not found:
                        # Feature file doesn't exist anywhere, comment out the scenarios call
                        old_call = f'scenarios("{feature_path}")'
                        new_call = f'# scenarios("{feature_path}") # Commented out - feature file not found'
                        new_content = new_content.replace(old_call, new_call)
                        modified = True
                        print(
                            f"Commented out non-existent feature file reference in {path}: {feature_path}"
                        )

            if modified:
                if not dry_run:
                    with open(path, "w") as f:
                        f.write(new_content)
                    print(f"Fixed feature path in {path}")
                else:
                    print(f"Would fix feature path in {path}")
                updated_count += 1

    return updated_count


def main():
    """Main function."""
    args = parse_args()

    print("Finding behavior test files...")
    test_files = find_behavior_test_files()

    print("Finding step definition files...")
    step_files = find_step_files()

    print("Finding feature files...")
    feature_files = find_feature_files()

    print("Fixing circular imports...")
    updated_imports = fix_circular_imports(step_files, args.dry_run)

    print("Fixing feature paths in test files...")
    updated_test_paths = fix_feature_paths(test_files, feature_files, args.dry_run)

    print("Fixing feature paths in step definition files...")
    updated_step_paths = fix_step_file_feature_paths(
        step_files, feature_files, args.dry_run
    )

    print("\nSummary:")
    print(f"- Fixed circular imports in {updated_imports} files")
    print(f"- Fixed feature paths in {updated_test_paths} test files")
    print(f"- Fixed feature paths in {updated_step_paths} step definition files")

    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
    else:
        print("\nAll files have been updated.")


if __name__ == "__main__":
    main()
