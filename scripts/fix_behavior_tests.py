#!/usr/bin/env python
"""
Script to fix behavior test collection issues.

This script addresses several issues with behavior test collection:
1. Duplicate feature files in different locations
2. Inconsistent scenario loading approaches
3. Missing scenario imports in step definition files

Usage:
    python scripts/fix_behavior_tests.py [--dry-run]

Options:
    --dry-run  Show changes without modifying files
"""

import argparse
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Regex patterns
SCENARIOS_IMPORT_PATTERN = re.compile(
    r"from pytest_bdd import (.*?)scenarios(.*?)$", re.MULTILINE
)
SCENARIOS_CALL_PATTERN = re.compile(r'scenarios\([\'"](.+?)[\'"]\)')
SCENARIO_DECORATOR_PATTERN = re.compile(r'@scenario\((.+?),\s*[\'"](.+?)[\'"]\)')
FEATURE_PATH_PATTERN = re.compile(r'([\'"])(.+?)([\'"])')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fix behavior test collection issues.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    return parser.parse_args()


def find_feature_files() -> dict[str, list[Path]]:
    """Find all feature files and group them by name."""
    feature_files = {}
    for root, _, files in os.walk("tests/behavior/features"):
        for file in files:
            if file.endswith(".feature"):
                path = Path(os.path.join(root, file))
                if file not in feature_files:
                    feature_files[file] = []
                feature_files[file].append(path)
    return feature_files


def find_step_files() -> dict[str, Path]:
    """Find all step definition files."""
    step_files = {}
    for root, _, files in os.walk("tests/behavior/steps"):
        for file in files:
            if file.endswith("_steps.py"):
                path = Path(os.path.join(root, file))
                step_files[file] = path
    return step_files


def find_test_files() -> list[Path]:
    """Find all test files in the behavior directory."""
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


def standardize_feature_files(
    feature_files: dict[str, list[Path]], dry_run: bool
) -> dict[str, Path]:
    """
    Standardize feature file locations.

    If a feature file exists in both the root features directory and a subdirectory,
    keep the one in the subdirectory and remove the one in the root directory.

    Returns a dictionary mapping feature file names to their standardized paths.
    """
    standardized_paths = {}

    for name, paths in feature_files.items():
        if len(paths) > 1:
            # Sort paths by depth (deeper paths first)
            sorted_paths = sorted(paths, key=lambda p: len(p.parts), reverse=True)

            # Keep the deepest path
            keep_path = sorted_paths[0]
            standardized_paths[name] = keep_path

            # Remove duplicate files
            for path in sorted_paths[1:]:
                if not dry_run:
                    print(f"Removing duplicate feature file: {path}")
                    os.remove(path)
                else:
                    print(f"Would remove duplicate feature file: {path}")
        else:
            standardized_paths[name] = paths[0]

    return standardized_paths


def update_step_files(
    step_files: dict[str, Path],
    standardized_feature_paths: dict[str, Path],
    dry_run: bool,
) -> int:
    """
    Update step definition files to ensure they import scenarios correctly.

    Returns the number of files updated.
    """
    updated_count = 0

    for name, path in step_files.items():
        with open(path) as f:
            content = f.read()

        # Check if the file imports scenarios
        import_match = SCENARIOS_IMPORT_PATTERN.search(content)
        if not import_match:
            continue

        # Check if the file calls scenarios
        scenarios_calls = SCENARIOS_CALL_PATTERN.findall(content)
        if not scenarios_calls:
            # Add scenarios call for the corresponding feature file
            feature_name = name.replace("_steps.py", ".feature")
            if feature_name in standardized_feature_paths:
                feature_path = standardized_feature_paths[feature_name]
                relative_path = os.path.relpath(feature_path, path.parent)

                # Add scenarios call after the import
                new_content = content
                if "scenarios(" not in content:
                    import_line = import_match.group(0)
                    scenarios_call = f"\nscenarios('{relative_path}')\n"
                    new_content = content.replace(
                        import_line, import_line + scenarios_call
                    )

                if new_content != content:
                    if not dry_run:
                        with open(path, "w") as f:
                            f.write(new_content)
                        print(f"Updated step file: {path}")
                    else:
                        print(f"Would update step file: {path}")
                    updated_count += 1
        else:
            # Update existing scenarios calls
            modified = False
            new_content = content

            for scenarios_call in scenarios_calls:
                feature_path_match = FEATURE_PATH_PATTERN.search(scenarios_call)
                if feature_path_match:
                    feature_path = feature_path_match.group(2)
                    feature_name = os.path.basename(feature_path)

                    if feature_name in standardized_feature_paths:
                        std_path = standardized_feature_paths[feature_name]
                        relative_path = os.path.relpath(std_path, path.parent)

                        if relative_path != feature_path:
                            old_call = f"scenarios('{feature_path}')"
                            new_call = f"scenarios('{relative_path}')"
                            new_content = new_content.replace(old_call, new_call)
                            modified = True

            if modified:
                if not dry_run:
                    with open(path, "w") as f:
                        f.write(new_content)
                    print(f"Updated scenarios path in: {path}")
                else:
                    print(f"Would update scenarios path in: {path}")
                updated_count += 1

    return updated_count


def update_test_files(
    test_files: list[Path], standardized_feature_paths: dict[str, Path], dry_run: bool
) -> int:
    """
    Update test files to ensure they load scenarios correctly.

    Returns the number of files updated.
    """
    updated_count = 0

    for path in test_files:
        with open(path) as f:
            content = f.read()

        # Check for scenario decorators
        scenario_decorators = SCENARIO_DECORATOR_PATTERN.findall(content)

        if scenario_decorators:
            # File uses @scenario decorators
            modified = False
            new_content = content

            for var_name, scenario_name in scenario_decorators:
                # Find the variable definition
                var_pattern = re.compile(f"{var_name}\\s*=\\s*(.+?)$", re.MULTILINE)
                var_match = var_pattern.search(content)

                if var_match:
                    var_def = var_match.group(1)
                    feature_path_match = FEATURE_PATH_PATTERN.search(var_def)

                    if feature_path_match:
                        feature_path = feature_path_match.group(2)
                        feature_name = os.path.basename(feature_path)

                        if feature_name in standardized_feature_paths:
                            std_path = standardized_feature_paths[feature_name]
                            relative_path = os.path.relpath(std_path, path.parent)

                            if os.path.basename(relative_path) != os.path.basename(
                                feature_path
                            ):
                                old_def = var_match.group(0)
                                new_def = old_def.replace(feature_path, relative_path)
                                new_content = new_content.replace(old_def, new_def)
                                modified = True

            if modified:
                if not dry_run:
                    with open(path, "w") as f:
                        f.write(new_content)
                    print(f"Updated feature path in: {path}")
                else:
                    print(f"Would update feature path in: {path}")
                updated_count += 1
        else:
            # Check for scenarios function
            scenarios_calls = SCENARIOS_CALL_PATTERN.findall(content)

            if scenarios_calls:
                # File uses scenarios function
                modified = False
                new_content = content

                for scenarios_call in scenarios_calls:
                    feature_path_match = FEATURE_PATH_PATTERN.search(scenarios_call)
                    if feature_path_match:
                        feature_path = feature_path_match.group(2)
                        feature_name = os.path.basename(feature_path)

                        if feature_name in standardized_feature_paths:
                            std_path = standardized_feature_paths[feature_name]
                            relative_path = os.path.relpath(std_path, path.parent)

                            if relative_path != feature_path:
                                old_call = f"scenarios('{feature_path}')"
                                new_call = f"scenarios('{relative_path}')"
                                new_content = new_content.replace(old_call, new_call)
                                modified = True

                if modified:
                    if not dry_run:
                        with open(path, "w") as f:
                            f.write(new_content)
                        print(f"Updated scenarios path in: {path}")
                    else:
                        print(f"Would update scenarios path in: {path}")
                    updated_count += 1

    return updated_count


def main():
    """Main function."""
    args = parse_args()

    print("Finding feature files...")
    feature_files = find_feature_files()

    print("Standardizing feature file locations...")
    standardized_paths = standardize_feature_files(feature_files, args.dry_run)

    print("Finding step definition files...")
    step_files = find_step_files()

    print("Updating step definition files...")
    updated_step_files = update_step_files(step_files, standardized_paths, args.dry_run)

    print("Finding test files...")
    test_files = find_test_files()

    print("Updating test files...")
    updated_test_files = update_test_files(test_files, standardized_paths, args.dry_run)

    print("\nSummary:")
    print(f"- Standardized {len(standardized_paths)} feature files")
    print(f"- Updated {updated_step_files} step definition files")
    print(f"- Updated {updated_test_files} test files")

    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
    else:
        print("\nAll files have been updated.")


if __name__ == "__main__":
    main()
