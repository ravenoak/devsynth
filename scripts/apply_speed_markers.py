#!/usr/bin/env python
"""
Script to apply speed markers to tests using existing timing data.

This script reads timing data from the .test_timing_cache directory and applies
appropriate speed markers (fast, medium, slow) to test files without running the tests again.

Usage:
    python scripts/apply_speed_markers.py [options]

Options:
    --dry-run             Show changes without modifying files
    --fast-threshold N    Threshold for fast tests in seconds (default: 1.0)
    --medium-threshold N  Threshold for medium tests in seconds (default: 5.0)
    --category CAT        Only apply markers to tests in the specified category (unit, integration, behavior, all)
    --no-cache-update     Don't update the test collection cache after modifying files
    --verbose             Show verbose output
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector for cache invalidation
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import clear_cache, invalidate_cache_for_files
except ImportError:
    print(
        "Warning: common_test_collector.py not found. Cache invalidation will be skipped."
    )

    # Define dummy functions if import fails
    def invalidate_cache_for_files(file_paths, verbose=False):
        if verbose:
            print("Cache invalidation skipped (common_test_collector.py not found)")

    def clear_cache(selective=False):
        print("Cache clearing skipped (common_test_collector.py not found)")


# Thresholds for categorizing tests (in seconds)
FAST_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 5.0

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")

# Cache directory for test timing data
CACHE_DIR = ".test_timing_cache"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Apply speed markers to tests using existing timing data."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--fast-threshold",
        type=float,
        default=1.0,
        help="Threshold for fast tests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--medium-threshold",
        type=float,
        default=5.0,
        help="Threshold for medium tests in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="all",
        help="Only apply markers to tests in the specified category",
    )
    parser.add_argument(
        "--no-cache-update",
        action="store_true",
        help="Don't update the test collection cache after modifying files",
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    return parser.parse_args()


def load_timing_data() -> (
    tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]
):
    """
    Load timing data from cache files.

    Returns:
        Tuple containing:
        - Dictionary mapping test names to timing data
        - Dictionary mapping test file paths to test functions and their timing data
    """
    timing_data = {}
    file_test_map = {}  # Maps test file paths to test functions

    if not os.path.exists(CACHE_DIR):
        print(f"Cache directory {CACHE_DIR} not found.")
        return timing_data, file_test_map

    # Find all timing cache files
    cache_files = [f for f in os.listdir(CACHE_DIR) if f.endswith("_timing.json")]
    print(f"Found {len(cache_files)} timing cache files.")

    for cache_file in cache_files:
        try:
            with open(os.path.join(CACHE_DIR, cache_file)) as f:
                data = json.load(f)

            # Parse the cache file name to extract test file path and test function name
            # Format: tests_unit_adapters_cli_test_typer_adapter.py__test_build_app_returns_expected_result_timing.json
            if "__" in cache_file:
                # Split on double underscore to separate file path from test name
                parts = cache_file.split("__")
                if len(parts) >= 2:
                    # First part is the file path with underscores instead of slashes
                    file_path_part = parts[0]
                    # Second part is the test function name followed by _timing.json
                    test_name_part = parts[1].replace("_timing.json", "")

                    # Reconstruct the original file path
                    # We need to be careful about how we convert underscores back to slashes
                    # Format is typically: tests_unit_adapters_cli_test_typer_adapter.py
                    # We want: tests/unit/adapters/cli/test_typer_adapter.py

                    # First, identify the components of the path
                    path_components = []
                    current_component = ""

                    # Split by underscore, but be careful about test file names
                    for component in file_path_part.split("_"):
                        if component in [
                            "tests",
                            "unit",
                            "integration",
                            "behavior",
                            "property",
                            "adapters",
                            "application",
                            "domain",
                            "interface",
                        ]:
                            # This is a directory component
                            if current_component:
                                path_components.append(current_component)
                                current_component = ""
                            path_components.append(component)
                        else:
                            # This is part of a file name or subdirectory
                            if current_component:
                                current_component += "_"
                            current_component += component

                    # Add the last component if there is one
                    if current_component:
                        path_components.append(current_component)

                    # Join the components with slashes
                    file_path = "/".join(path_components)

                    # Store the test function name
                    test_name = test_name_part

                    # Add to the file_test_map
                    if file_path not in file_test_map:
                        file_test_map[file_path] = {}

                    # Store timing data for this test
                    file_test_map[file_path][test_name] = {
                        "execution_time": data.get("execution_time", 0.0),
                        "passed": data.get("passed", False),
                        "skipped": data.get("skipped", False),
                    }

                    # Determine marker based on execution time
                    if data.get("skipped", False):
                        marker = "unknown"
                    elif data.get("execution_time", 0.0) < FAST_THRESHOLD:
                        marker = "fast"
                    elif data.get("execution_time", 0.0) < MEDIUM_THRESHOLD:
                        marker = "medium"
                    else:
                        marker = "slow"

                    file_test_map[file_path][test_name]["marker"] = marker

                    # Also store in the flat timing_data dictionary for backward compatibility
                    timing_data[test_name] = {
                        "execution_time": data.get("execution_time", 0.0),
                        "passed": data.get("passed", False),
                        "skipped": data.get("skipped", False),
                        "marker": marker,
                        "file_path": file_path,
                    }

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading {cache_file}: {e}")

    print(
        f"Loaded timing data for {len(timing_data)} tests across {len(file_test_map)} files."
    )
    return timing_data, file_test_map


def find_test_files(directory: str) -> list[Path]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file(
    file_path: Path,
) -> tuple[dict[str, list[str]], dict[int, str], list[str], dict[str, list[str]]]:
    """
    Analyze a test file to extract existing markers and test functions.

    Returns:
        Tuple containing:
        - Dictionary mapping test names to their existing markers
        - Dictionary mapping line numbers to test names
        - List of module-level markers
        - Dictionary mapping class names to their markers
    """
    existing_markers = {}
    test_line_numbers = {}
    module_markers = []
    class_markers = {}

    with open(file_path) as f:
        lines = f.readlines()

    # Add pattern for class definitions
    CLASS_PATTERN = re.compile(r"class\s+(\w+)\s*\(")

    current_markers = []
    current_class = None
    in_class = False
    class_indent = ""

    # First pass: collect module-level markers (those before any class or function)
    for i, line in enumerate(lines):
        # Skip empty lines and imports
        if not line.strip() or line.strip().startswith(("import ", "from ")):
            continue

        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            module_markers.append(marker_match.group(1))
            continue

        # If we hit a class or function definition, stop collecting module-level markers
        if line.strip().startswith(("class ", "def ")):
            break

    # Second pass: collect class and function markers
    current_markers = []
    for i, line in enumerate(lines):
        # Check for class definitions
        class_match = CLASS_PATTERN.search(line)
        if class_match:
            # If we have markers before the class, they belong to the class
            if current_markers:
                class_name = class_match.group(1)
                class_markers[class_name] = current_markers.copy()
                current_markers = []

            current_class = class_match.group(1)
            in_class = True
            # Get the indentation level of the class
            class_indent = line[: line.find("class")]
            continue

        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))
            continue

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)

            # If we're in a class, check the indentation to confirm it's a method
            if in_class:
                # Get the indentation level of the function
                func_indent = line[: line.find("def")]
                # If the function is more indented than the class, it's a method
                if len(func_indent) > len(class_indent):
                    # For class methods, store the full name (class::method)
                    full_test_name = f"{current_class}::{test_name}"
                    test_line_numbers[i] = full_test_name

                    # If the function has its own markers, use those
                    if current_markers:
                        existing_markers[full_test_name] = current_markers.copy()
                    # Otherwise, if the class has markers, inherit them
                    elif current_class in class_markers:
                        existing_markers[full_test_name] = class_markers[
                            current_class
                        ].copy()
                    # Otherwise, if there are module-level markers, inherit those
                    elif module_markers:
                        existing_markers[full_test_name] = module_markers.copy()

                    current_markers = []
                    continue

            # For standalone functions or if indentation doesn't match class method
            test_line_numbers[i] = test_name

            # If the function has its own markers, use those
            if current_markers:
                existing_markers[test_name] = current_markers.copy()
            # Otherwise, if there are module-level markers, inherit those
            elif module_markers:
                existing_markers[test_name] = module_markers.copy()

            current_markers = []

    return existing_markers, test_line_numbers, module_markers, class_markers


def update_test_file_with_markers(
    file_path: Path,
    test_markers: dict[str, str],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int, bool]:
    """
    Update a test file with appropriate markers.

    Args:
        file_path: Path to the test file
        test_markers: Mapping from test function names to their speed markers
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show verbose output

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers and whether the file was modified
    """
    added = 0
    updated = 0
    unchanged = 0
    file_modified = False

    # Analyze the file
    existing_markers, test_line_numbers, module_markers, class_markers = (
        analyze_test_file(file_path)
    )

    if not test_line_numbers:
        return added, updated, unchanged, file_modified

    with open(file_path) as f:
        lines = f.readlines()

    # Create a dictionary to track which tests need markers
    tests_needing_markers = {}

    # Process each test function
    for line_num, test_name in test_line_numbers.items():
        # Check if this is a class-based test
        is_class_based = "::" in test_name

        # For class-based tests, we need to check both the full name and the method name
        if is_class_based:
            class_name, method_name = test_name.split("::")
            # Check if either the full name or just the method name is in test_markers
            if test_name in test_markers:
                marker_key = test_name
                new_marker = test_markers[marker_key]
            elif method_name in test_markers:
                marker_key = method_name
                new_marker = test_markers[marker_key]
            # If not in test_markers, check if the class has markers
            elif class_name in class_markers:
                # Use the first marker from the class (assuming there's only one speed marker)
                for marker in class_markers[class_name]:
                    if marker in ("fast", "medium", "slow"):
                        new_marker = marker
                        break
                else:
                    continue  # No speed marker found
            # If class doesn't have markers, check if there are module-level markers
            elif module_markers:
                # Use the first marker from the module (assuming there's only one speed marker)
                for marker in module_markers:
                    if marker in ("fast", "medium", "slow"):
                        new_marker = marker
                        break
                else:
                    continue  # No speed marker found
            else:
                continue  # No marker found for this test
        else:
            # For standalone functions, check the name
            if test_name in test_markers:
                marker_key = test_name
                new_marker = test_markers[marker_key]
            # If not in test_markers, check if there are module-level markers
            elif module_markers:
                # Use the first marker from the module (assuming there's only one speed marker)
                for marker in module_markers:
                    if marker in ("fast", "medium", "slow"):
                        new_marker = marker
                        break
                else:
                    continue  # No speed marker found
            else:
                continue  # No marker found for this test

        # Skip unknown markers (from skipped tests)
        if new_marker == "unknown":
            continue

        # Check if the test already has the correct marker
        if test_name in existing_markers and new_marker in existing_markers[test_name]:
            unchanged += 1
            if verbose:
                print(f"Test {test_name} already has {new_marker} marker")
            continue

        # Store the test and its needed marker
        tests_needing_markers[line_num] = (test_name, new_marker)

    # Apply markers to tests that need them
    # Process in reverse order to avoid line number shifting issues
    for line_num, (test_name, new_marker) in sorted(
        tests_needing_markers.items(), reverse=True
    ):
        # Check if we need to update an existing marker or add a new one
        if test_name in existing_markers and any(
            m in ("fast", "medium", "slow") for m in existing_markers[test_name]
        ):
            # Update existing marker
            for i in range(
                line_num - 5, line_num
            ):  # Look at a few lines before the test
                if (
                    i >= 0
                    and i < len(lines)
                    and any(
                        f"@pytest.mark.{m}" in lines[i]
                        for m in ("fast", "medium", "slow")
                    )
                ):
                    old_line = lines[i]
                    lines[i] = old_line.replace(
                        f'@pytest.mark.{next(m for m in ("fast", "medium", "slow") if f"@pytest.mark.{m}" in old_line)}',
                        f"@pytest.mark.{new_marker}",
                    )
                    if dry_run:
                        print(
                            f"Would update {file_path}:{i+1} - {old_line.strip()} -> {lines[i].strip()}"
                        )
                    elif verbose:
                        print(
                            f"Updated {file_path}:{i+1} - {old_line.strip()} -> {lines[i].strip()}"
                        )
                    updated += 1
                    file_modified = True
                    break
        else:
            # Add new marker
            # Determine the indentation level
            indentation = ""
            if line_num < len(lines):
                # Extract indentation from the function definition line
                match = re.match(r"^(\s*)", lines[line_num])
                if match:
                    indentation = match.group(1)

            marker_line = f"{indentation}@pytest.mark.{new_marker}\n"
            lines.insert(line_num, marker_line)

            if dry_run:
                print(f"Would add to {file_path}:{line_num+1} - {marker_line.strip()}")
            elif verbose:
                print(f"Added to {file_path}:{line_num+1} - {marker_line.strip()}")
            added += 1
            file_modified = True

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0):
        with open(file_path, "w") as f:
            f.writelines(lines)

    return added, updated, unchanged, file_modified


def main():
    """Main function."""
    args = parse_args()

    # Set global thresholds based on command-line arguments
    global FAST_THRESHOLD, MEDIUM_THRESHOLD
    FAST_THRESHOLD = args.fast_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    print(f"Fast threshold: {FAST_THRESHOLD}s, Medium threshold: {MEDIUM_THRESHOLD}s")

    # Load timing data from cache files
    timing_data, file_test_map = load_timing_data()

    if not timing_data:
        print("No timing data found. Please run tests first to generate timing data.")
        return

    # Create a flat dictionary mapping test function names to their speed markers
    test_markers = {
        name: data["marker"] for name, data in timing_data.items() if "marker" in data
    }

    # Count tests by speed category
    fast_tests = sum(1 for marker in test_markers.values() if marker == "fast")
    medium_tests = sum(1 for marker in test_markers.values() if marker == "medium")
    slow_tests = sum(1 for marker in test_markers.values() if marker == "slow")
    unknown_tests = sum(1 for marker in test_markers.values() if marker == "unknown")

    print(f"Test counts by speed category:")
    print(f"  - Fast tests: {fast_tests}")
    print(f"  - Medium tests: {medium_tests}")
    print(f"  - Slow tests: {slow_tests}")
    print(f"  - Unknown tests: {unknown_tests}")

    # Determine the directory to analyze
    if args.category == "all":
        directory = "tests"
    else:
        directory = f"tests/{args.category}"

    print(f"Analyzing tests in {directory}...")

    # Find all test files
    test_files = find_test_files(directory)
    print(f"Found {len(test_files)} test files.")

    # Update test files with markers
    total_added = 0
    total_updated = 0
    total_unchanged = 0
    modified_files = []  # Track which files were modified

    for file_path in test_files:
        # Analyze the file to find test functions
        existing_markers, test_line_numbers, module_markers, class_markers = (
            analyze_test_file(file_path)
        )

        # Check if any of the test functions in this file have timing data
        file_test_markers = {}
        for line_num, test_name in test_line_numbers.items():
            if test_name in test_markers:
                file_test_markers[test_name] = test_markers[test_name]
            # For class-based tests, also check the method name
            elif "::" in test_name:
                class_name, method_name = test_name.split("::")
                if method_name in test_markers:
                    file_test_markers[test_name] = test_markers[method_name]

        # If we have file_test_map data for this file, add those markers too
        file_path_str = str(file_path)
        if file_path_str in file_test_map:
            for test_name, test_data in file_test_map[file_path_str].items():
                if "marker" in test_data and test_data["marker"] != "unknown":
                    # For standalone functions, use the name directly
                    if test_name in test_line_numbers.values():
                        file_test_markers[test_name] = test_data["marker"]
                    # For class-based tests, find the full name
                    else:
                        for full_name in test_line_numbers.values():
                            if (
                                "::" in full_name
                                and full_name.split("::")[1] == test_name
                            ):
                                file_test_markers[full_name] = test_data["marker"]
                                break

        if file_test_markers or module_markers or any(class_markers.values()):
            # Update the file with markers
            added, updated, unchanged, file_modified = update_test_file_with_markers(
                file_path, file_test_markers, args.dry_run, args.verbose
            )
            total_added += added
            total_updated += updated
            total_unchanged += unchanged

            # Track modified files for cache invalidation
            if file_modified and not args.dry_run:
                modified_files.append(str(file_path))

    action = "Would " if args.dry_run else ""
    print(
        f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
    )

    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
    else:
        print(f"\n{len(modified_files)} files have been updated.")

        # Invalidate cache for modified files
        if not args.no_cache_update and modified_files:
            print("\nInvalidating cache for modified files...")
            try:
                invalidate_cache_for_files(modified_files, args.verbose)
                print(f"Cache invalidated for {len(modified_files)} files")
            except Exception as e:
                print(f"Error invalidating cache: {e}")
                print(
                    "You may need to manually clear the cache with: python -m pytest --cache-clear"
                )

    # Generate a report of the applied markers
    report = {
        "fast_threshold": FAST_THRESHOLD,
        "medium_threshold": MEDIUM_THRESHOLD,
        "test_count": len(test_markers),
        "fast_tests": fast_tests,
        "medium_tests": medium_tests,
        "slow_tests": slow_tests,
        "unknown_tests": unknown_tests,
        "markers_added": total_added,
        "markers_updated": total_updated,
        "markers_unchanged": total_unchanged,
        "files_modified": len(modified_files),
    }

    with open("test_markers_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Marker report saved to test_markers_report.json")


if __name__ == "__main__":
    main()
