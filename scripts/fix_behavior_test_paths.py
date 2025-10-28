#!/usr/bin/env python
"""
Script to fix behavior test file paths.

This script addresses the issue where behavior test files are using just the filename
to reference feature files, but the feature files are actually in subdirectories.

Usage:
    python scripts/fix_behavior_test_paths.py [--dry-run]

Options:
    --dry-run  Show changes without modifying files
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Regex pattern for scenarios function call
SCENARIOS_PATTERN = re.compile(r'scenarios\([\'"](.+?)[\'"]\)')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fix behavior test file paths.")
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


def find_feature_files() -> dict[str, Path]:
    """Find all feature files and map filenames to paths."""
    feature_files = {}
    for root, _, files in os.walk("tests/behavior/features"):
        for file in files:
            if file.endswith(".feature"):
                path = Path(os.path.join(root, file))
                feature_files[file] = path
    return feature_files


def extract_feature_filename(test_file: Path) -> str:
    """Extract the feature filename from a test file."""
    with open(test_file) as f:
        content = f.read()

    match = SCENARIOS_PATTERN.search(content)
    if match:
        feature_path = match.group(1)
        # If it's already a path, extract just the filename
        return os.path.basename(feature_path)

    return None


def update_test_file(test_file: Path, feature_file: Path, dry_run: bool) -> bool:
    """
    Update a test file to use the correct path to the feature file.

    Returns:
        bool: True if the file was updated, False otherwise
    """
    with open(test_file) as f:
        content = f.read()

    match = SCENARIOS_PATTERN.search(content)
    if not match:
        return False

    old_path = match.group(1)
    # If the path already contains a directory separator and starts with 'general/', it might already be correct
    if "/" in old_path and old_path.startswith("general/"):
        return False

    # Calculate the path relative to the bdd_features_base_dir (tests/behavior/features)
    # The path should be relative to tests/behavior/features, not to the test file's directory
    features_base_dir = Path("tests/behavior/features")
    relative_path = os.path.relpath(feature_file, features_base_dir)

    # Replace the old path with the new path
    new_content = SCENARIOS_PATTERN.sub(f'scenarios("{relative_path}")', content)

    if new_content != content:
        if not dry_run:
            with open(test_file, "w") as f:
                f.write(new_content)
            print(f"Updated {test_file}")
        else:
            print(f"Would update {test_file}: {old_path} -> {relative_path}")
        return True

    return False


def main():
    """Main function."""
    args = parse_args()

    print("Finding behavior test files...")
    test_files = find_behavior_test_files()

    print("Finding feature files...")
    feature_files = find_feature_files()

    print("Updating test files...")
    updated_count = 0
    for test_file in test_files:
        feature_filename = extract_feature_filename(test_file)
        if feature_filename and feature_filename in feature_files:
            if update_test_file(
                test_file, feature_files[feature_filename], args.dry_run
            ):
                updated_count += 1

    print(f"\nUpdated {updated_count} test files")

    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
    else:
        print("\nAll files have been updated.")


if __name__ == "__main__":
    main()
