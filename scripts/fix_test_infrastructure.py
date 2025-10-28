#!/usr/bin/env python3
"""
Fix Test Infrastructure

This script addresses critical issues in the test infrastructure:
1. Resolves test count discrepancies between different collection methods
2. Fixes marker detection discrepancies between files and pytest
3. Provides a reliable test verification system
4. Adds markers to tests without running them

Usage:
    python scripts/fix_test_infrastructure.py [options]

Options:
    --verify                Verify test counts and marker detection
    --fix-markers           Fix marker detection issues
    --add-markers           Add markers to tests without running them
    --module MODULE         Specific module to process (e.g., tests/unit/interface)
    --category CATEGORY     Test category to process (unit, integration, behavior, all)
    --report                Generate a detailed report
    --verbose               Show detailed information
"""

import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import common_test_collector
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fix test infrastructure issues.")
    parser.add_argument(
        "--verify", action="store_true", help="Verify test counts and marker detection"
    )
    parser.add_argument(
        "--fix-markers", action="store_true", help="Fix marker detection issues"
    )
    parser.add_argument(
        "--add-markers",
        action="store_true",
        help="Add markers to tests without running them",
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
        "--report", action="store_true", help="Generate a detailed report"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes without confirmation (use with caution)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files (default for --add-markers)",
    )
    return parser.parse_args()


def verify_test_counts(
    category: str = "all", module: str = None, verbose: bool = False
) -> dict[str, Any]:
    """
    Verify test counts between different collection methods.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to verify
        verbose: Whether to show detailed information

    Returns:
        Dictionary with verification results
    """
    print("Verifying test counts...")

    # Determine which categories to verify
    categories = [category] if category != "all" else list(TEST_CATEGORIES.keys())

    # Initialize results
    results = {
        "categories": {},
        "total": {"pytest_count": 0, "file_count": 0, "discrepancy": 0},
    }

    # Verify each category
    for cat in categories:
        if verbose:
            print(f"Verifying {cat} tests...")

        # Get directory for this category
        directory = TEST_CATEGORIES[cat]

        # Apply module filter if specified
        if module:
            if not module.startswith(directory):
                continue
            directory = module

        # Collect tests using pytest
        pytest_tests = collect_tests_with_pytest(directory)
        pytest_count = len(pytest_tests)

        # Collect tests by parsing files
        file_tests = collect_tests_from_files(directory)
        file_count = len(file_tests)

        # Calculate discrepancy
        discrepancy = abs(pytest_count - file_count)

        # Store results
        results["categories"][cat] = {
            "pytest_count": pytest_count,
            "file_count": file_count,
            "discrepancy": discrepancy,
        }

        # Update totals
        results["total"]["pytest_count"] += pytest_count
        results["total"]["file_count"] += file_count
        results["total"]["discrepancy"] += discrepancy

        if verbose:
            print(
                f"  {cat}: {pytest_count} tests (pytest), {file_count} tests (files), discrepancy: {discrepancy}"
            )

    # Print summary
    print(
        f"Total: {results['total']['pytest_count']} tests (pytest), {results['total']['file_count']} tests (files)"
    )
    print(f"Total discrepancy: {results['total']['discrepancy']}")

    return results


def collect_tests_with_pytest(directory: str) -> list[str]:
    """
    Collect tests from a directory using pytest.

    Args:
        directory: Directory to collect tests from

    Returns:
        List of test paths
    """
    cmd = [sys.executable, "-m", "pytest", directory, "--collect-only", "-v"]

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Extract test paths from output
        tests = []
        for line in result.stdout.split("\n"):
            if (
                line.strip()
                and not line.startswith("=")
                and not line.startswith("collecting")
            ):
                # Clean up the line to get just the test path
                test_path = line.strip()
                if " " in test_path:
                    test_path = test_path.split(" ")[0]
                tests.append(test_path)

        return tests
    except Exception as e:
        print(f"Error collecting tests with pytest: {e}")
        return []


def collect_tests_from_files(directory: str) -> list[str]:
    """
    Collect tests by parsing Python files.

    Args:
        directory: Directory to collect tests from

    Returns:
        List of test paths
    """
    tests = []

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Parse the file to find test functions and methods
                file_tests = parse_test_file(file_path)
                tests.extend(file_tests)

    return tests


def parse_test_file(file_path: str) -> list[str]:
    """
    Parse a test file to find test functions and methods using AST.

    Args:
        file_path: Path to the test file

    Returns:
        List of test paths
    """
    tests = []

    try:
        with open(file_path) as f:
            content = f.read()

        # Parse the file using AST
        tree = ast.parse(content, filename=file_path)

        # Find test functions and methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Function-based test
                tests.append(f"{file_path}::{node.name}")
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                # Class-based test
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name.startswith(
                        "test_"
                    ):
                        tests.append(f"{file_path}::{node.name}::{child.name}")

    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")

    return tests


def verify_marker_detection(
    category: str = "all", module: str = None, verbose: bool = False
) -> dict[str, Any]:
    """
    Verify marker detection between files and pytest.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to verify
        verbose: Whether to show detailed information

    Returns:
        Dictionary with verification results
    """
    print("Verifying marker detection...")

    # Determine which categories to verify
    categories = [category] if category != "all" else list(TEST_CATEGORIES.keys())

    # Initialize results
    results = {
        "markers": {
            "fast": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
            "medium": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
            "slow": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
        },
        "categories": {},
    }

    # Verify each category
    for cat in categories:
        if verbose:
            print(f"Verifying {cat} tests...")

        # Get directory for this category
        directory = TEST_CATEGORIES[cat]

        # Apply module filter if specified
        if module:
            if not module.startswith(directory):
                continue
            directory = module

        # Initialize category results
        results["categories"][cat] = {
            "markers": {
                "fast": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
                "medium": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
                "slow": {"file_count": 0, "pytest_count": 0, "discrepancy": 0},
            }
        }

        # Get markers from files
        file_markers = get_markers_from_files(directory)

        # Get markers from pytest
        pytest_markers = get_markers_from_pytest(directory)

        # Count markers
        for marker in ["fast", "medium", "slow"]:
            file_count = len(file_markers.get(marker, []))
            pytest_count = len(pytest_markers.get(marker, []))
            discrepancy = abs(pytest_count - file_count)

            # Update category results
            results["categories"][cat]["markers"][marker] = {
                "file_count": file_count,
                "pytest_count": pytest_count,
                "discrepancy": discrepancy,
            }

            # Update total results
            results["markers"][marker]["file_count"] += file_count
            results["markers"][marker]["pytest_count"] += pytest_count
            results["markers"][marker]["discrepancy"] += discrepancy

            if verbose:
                print(
                    f"  {marker}: {pytest_count} tests (pytest), {file_count} tests (files), discrepancy: {discrepancy}"
                )

    # Print summary
    for marker in ["fast", "medium", "slow"]:
        print(
            f"{marker}: {results['markers'][marker]['pytest_count']} tests (pytest), {results['markers'][marker]['file_count']} tests (files), discrepancy: {results['markers'][marker]['discrepancy']}"
        )

    return results


def get_markers_from_files(directory: str) -> dict[str, list[str]]:
    """
    Get markers from files using AST parsing.

    Args:
        directory: Directory to collect markers from

    Returns:
        Dictionary mapping marker types to lists of test paths
    """
    markers = {"fast": [], "medium": [], "slow": []}

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Parse the file to find markers
                file_markers = parse_markers_from_file(file_path)

                # Add to results
                for marker_type, tests in file_markers.items():
                    markers[marker_type].extend(tests)

    return markers


def parse_markers_from_file(file_path: str) -> dict[str, list[str]]:
    """
    Parse markers from a test file using AST.

    Args:
        file_path: Path to the test file

    Returns:
        Dictionary mapping marker types to lists of test paths
    """
    markers = {"fast": [], "medium": [], "slow": []}

    try:
        with open(file_path) as f:
            content = f.read()

        # Parse the file using AST
        tree = ast.parse(content, filename=file_path)

        # Find decorated functions and methods
        for node in ast.walk(tree):
            # Check function definitions
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Check for decorators
                for decorator in node.decorator_list:
                    marker_type = get_marker_type_from_decorator(decorator)
                    if marker_type:
                        markers[marker_type].append(f"{file_path}::{node.name}")

            # Check class definitions
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                # Check for class-level decorators that apply to all methods
                class_markers = []
                for decorator in node.decorator_list:
                    marker_type = get_marker_type_from_decorator(decorator)
                    if marker_type:
                        class_markers.append(marker_type)

                # Check methods within the class
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name.startswith(
                        "test_"
                    ):
                        # Check for method-level decorators
                        method_marker = None
                        for decorator in child.decorator_list:
                            marker_type = get_marker_type_from_decorator(decorator)
                            if marker_type:
                                method_marker = marker_type
                                break

                        # Use method-level marker if available, otherwise use class-level marker
                        if method_marker:
                            markers[method_marker].append(
                                f"{file_path}::{node.name}::{child.name}"
                            )
                        elif class_markers:
                            # Use the last class-level marker (most specific)
                            markers[class_markers[-1]].append(
                                f"{file_path}::{node.name}::{child.name}"
                            )

    except Exception as e:
        print(f"Error parsing markers from {file_path}: {e}")

    return markers


def get_marker_type_from_decorator(decorator: ast.expr) -> str | None:
    """
    Get marker type from a decorator node.

    Args:
        decorator: AST decorator node

    Returns:
        Marker type (fast, medium, slow) or None
    """
    # Check for @pytest.mark.fast, @pytest.mark.medium, @pytest.mark.slow
    if isinstance(decorator, ast.Attribute) and isinstance(
        decorator.value, ast.Attribute
    ):
        if (
            decorator.value.attr == "mark"
            and isinstance(decorator.value.value, ast.Name)
            and decorator.value.value.id == "pytest"
        ):
            if decorator.attr in ["fast", "medium", "slow"]:
                return decorator.attr

    # Check for @pytest.mark.fast(), @pytest.mark.medium(), @pytest.mark.slow()
    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        if (
            decorator.func.attr in ["fast", "medium", "slow"]
            and isinstance(decorator.func.value, ast.Attribute)
            and decorator.func.value.attr == "mark"
            and isinstance(decorator.func.value.value, ast.Name)
            and decorator.func.value.value.id == "pytest"
        ):
            return decorator.func.attr

    return None


def get_markers_from_pytest(directory: str) -> dict[str, list[str]]:
    """
    Get markers from pytest.

    Args:
        directory: Directory to collect markers from

    Returns:
        Dictionary mapping marker types to lists of test paths
    """
    markers = {"fast": [], "medium": [], "slow": []}

    # Collect markers for each type
    for marker_type in markers.keys():
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            directory,
            f"-m={marker_type}",
            "--collect-only",
            "-v",
        ]

        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)

            # Extract test paths from output
            for line in result.stdout.split("\n"):
                if (
                    line.strip()
                    and not line.startswith("=")
                    and not line.startswith("collecting")
                ):
                    # Clean up the line to get just the test path
                    test_path = line.strip()
                    if " " in test_path:
                        test_path = test_path.split(" ")[0]
                    markers[marker_type].append(test_path)

        except Exception as e:
            print(f"Error collecting {marker_type} markers with pytest: {e}")

    return markers


def add_markers_to_tests(
    tests: list[str], marker: str, dry_run: bool = True, verbose: bool = False
) -> dict[str, Any]:
    """
    Add markers to tests without running them.

    Args:
        tests: List of test paths
        marker: Marker to add (fast, medium, slow)
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information

    Returns:
        Dictionary with results
    """
    results = {
        "total": len(tests),
        "processed": 0,
        "modified": 0,
        "errors": 0,
        "skipped": 0,
        "behavior_tests": 0,
    }

    # Group tests by file
    tests_by_file = {}
    behavior_tests = []

    for test in tests:
        if "::" in test:
            file_path = test.split("::")[0]

            # Check if this is a behavior test (feature file)
            if file_path.endswith(".feature"):
                behavior_tests.append(test)
                continue

            if file_path not in tests_by_file:
                tests_by_file[file_path] = []
            tests_by_file[file_path].append(test)
        else:
            # Skip tests without a specific test name
            results["skipped"] += 1

    # Process regular pytest tests
    for file_path, file_tests in tests_by_file.items():
        if verbose:
            print(f"Processing {file_path}...")

        try:
            # Read the file
            with open(file_path) as f:
                content = f.read()

            # Parse the file using AST
            tree = ast.parse(content, filename=file_path)

            # Track modifications
            modified = False

            # Process each test in the file
            for test in file_tests:
                results["processed"] += 1

                # Extract test name from test path
                if "::" in test:
                    parts = test.split("::")
                    if len(parts) > 2:  # Class-based test
                        class_name = parts[1]
                        test_name = parts[2]

                        # Find the class and method
                        for node in ast.walk(tree):
                            if (
                                isinstance(node, ast.ClassDef)
                                and node.name == class_name
                            ):
                                for child in node.body:
                                    if (
                                        isinstance(child, ast.FunctionDef)
                                        and child.name == test_name
                                    ):
                                        # Check if the method already has the marker
                                        has_marker = False
                                        for decorator in child.decorator_list:
                                            if (
                                                get_marker_type_from_decorator(
                                                    decorator
                                                )
                                                == marker
                                            ):
                                                has_marker = True
                                                break

                                        if not has_marker:
                                            # Add the marker
                                            if verbose:
                                                print(
                                                    f"  Adding {marker} marker to {class_name}::{test_name}"
                                                )

                                            # Create a new decorator node
                                            decorator_attr = ast.Attribute(
                                                value=ast.Attribute(
                                                    value=ast.Name(
                                                        id="pytest", ctx=ast.Load()
                                                    ),
                                                    attr="mark",
                                                    ctx=ast.Load(),
                                                ),
                                                attr=marker,
                                                ctx=ast.Load(),
                                            )

                                            # Add the decorator to the function
                                            child.decorator_list.insert(
                                                0, decorator_attr
                                            )
                                            modified = True
                    else:  # Function-based test
                        test_name = parts[1]

                        # Find the function
                        for node in ast.walk(tree):
                            if (
                                isinstance(node, ast.FunctionDef)
                                and node.name == test_name
                            ):
                                # Check if the function already has the marker
                                has_marker = False
                                for decorator in node.decorator_list:
                                    if (
                                        get_marker_type_from_decorator(decorator)
                                        == marker
                                    ):
                                        has_marker = True
                                        break

                                if not has_marker:
                                    # Add the marker
                                    if verbose:
                                        print(
                                            f"  Adding {marker} marker to {test_name}"
                                        )

                                    # Create a new decorator node
                                    decorator_attr = ast.Attribute(
                                        value=ast.Attribute(
                                            value=ast.Name(id="pytest", ctx=ast.Load()),
                                            attr="mark",
                                            ctx=ast.Load(),
                                        ),
                                        attr=marker,
                                        ctx=ast.Load(),
                                    )

                                    # Add the decorator to the function
                                    node.decorator_list.insert(0, decorator_attr)
                                    modified = True

            # Write the modified file
            if modified and not dry_run:
                # Add import if needed
                has_pytest_import = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import) and any(
                        name.name == "pytest" for name in node.names
                    ):
                        has_pytest_import = True
                        break
                    elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
                        has_pytest_import = True
                        break

                if not has_pytest_import:
                    # Add pytest import at the beginning of the file
                    import_node = ast.Import(
                        names=[ast.alias(name="pytest", asname=None)]
                    )
                    tree.body.insert(0, import_node)

                # Generate the modified code
                modified_code = ast.unparse(tree)

                # Write the modified code back to the file
                with open(file_path, "w") as f:
                    f.write(modified_code)

                results["modified"] += 1
                if verbose:
                    print(f"  Modified {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            results["errors"] += 1

    # Process behavior tests
    if behavior_tests:
        results["behavior_tests"] = len(behavior_tests)
        if verbose:
            print(f"Processing {len(behavior_tests)} behavior tests...")

        # Call the specialized function for adding markers to behavior tests
        behavior_results = add_markers_to_behavior_tests(
            behavior_tests, marker, dry_run, verbose
        )

        # Update the overall results
        results["processed"] += behavior_results["processed"]
        results["modified"] += behavior_results["modified"]
        results["errors"] += behavior_results["errors"]
        results["skipped"] += behavior_results["skipped"]

    # Print summary
    print(f"Total tests: {results['total']}")
    print(f"Processed: {results['processed']}")
    print(f"Modified: {results['modified']}")
    print(f"Errors: {results['errors']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Behavior tests: {results['behavior_tests']}")

    if dry_run:
        print("\nNote: This was a dry run. Use without --dry-run to apply changes.")

    return results


def add_markers_to_behavior_tests(
    tests: list[str], marker: str, dry_run: bool = True, verbose: bool = False
) -> dict[str, Any]:
    """
    Add markers to pytest-bdd generated tests.

    Args:
        tests: List of behavior test paths
        marker: Marker to add (fast, medium, slow)
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information

    Returns:
        Dictionary with results
    """
    results = {
        "total": len(tests),
        "processed": 0,
        "modified": 0,
        "errors": 0,
        "skipped": 0,
    }

    # Group tests by feature file
    tests_by_feature = {}
    for test in tests:
        if "::" in test:
            feature_path = test.split("::")[0]
            if feature_path not in tests_by_feature:
                tests_by_feature[feature_path] = []
            tests_by_feature[feature_path].append(test)
        else:
            # Skip tests without a specific scenario name
            results["skipped"] += 1

    # Find all test files that import scenarios from feature files
    test_files_by_feature = find_test_files_for_features(
        list(tests_by_feature.keys()), verbose
    )

    # Process each feature file and its corresponding test files
    for feature_path, feature_tests in tests_by_feature.items():
        if verbose:
            print(f"Processing feature file: {feature_path}")

        # Get the test files that import scenarios from this feature file
        test_files = test_files_by_feature.get(feature_path, [])

        if not test_files:
            if verbose:
                print(f"  No test files found for feature {feature_path}")
            results["skipped"] += len(feature_tests)
            continue

        # Process each test file
        for test_file in test_files:
            if verbose:
                print(f"  Processing test file: {test_file}")

            try:
                # Read the file
                with open(test_file) as f:
                    content = f.read()

                # Check if the file already has the marker
                if f"@pytest.mark.{marker}" in content:
                    if verbose:
                        print(f"    File already has {marker} marker")
                    continue

                # Find the scenarios function call
                scenarios_match = re.search(
                    r'scenarios\([\'"]([^\'"]+)[\'"]\)', content
                )
                if not scenarios_match:
                    if verbose:
                        print(f"    No scenarios function call found in {test_file}")
                    continue

                # Add the marker to all step functions
                modified_content = content

                # Add markers to @given, @when, @then functions
                for step_type in ["given", "when", "then"]:
                    # Find all step functions
                    step_matches = re.finditer(
                        rf"@(?:pytest_bdd\.)?{step_type}\([^\)]+\)\s*\n(?:@[^\n]+\s*\n)*def\s+([a-zA-Z0-9_]+)\(",
                        content,
                    )

                    for match in step_matches:
                        func_name = match.group(1)

                        # Check if the function already has the marker
                        marker_pattern = rf"@pytest\.mark\.{marker}\s*\n[^@]*@(?:pytest_bdd\.)?{step_type}"
                        if re.search(
                            marker_pattern,
                            content[match.start() - 50 : match.start() + 50],
                        ):
                            if verbose:
                                print(
                                    f"    Step function {func_name} already has {marker} marker"
                                )
                            continue

                        # Add the marker before the step decorator
                        step_decorator = match.group(0)
                        replacement = f"@pytest.mark.{marker}\n{step_decorator}"
                        modified_content = modified_content.replace(
                            step_decorator, replacement
                        )

                        if verbose:
                            print(
                                f"    Added {marker} marker to step function {func_name}"
                            )

                # Check if we need to add pytest import
                if (
                    "@pytest.mark." in modified_content
                    and "import pytest" not in modified_content
                ):
                    # Add pytest import at the beginning of the file
                    import_match = re.search(r"import\s+[^\n]+\n", modified_content)
                    if import_match:
                        # Add after the first import
                        modified_content = (
                            modified_content[: import_match.end()]
                            + "import pytest\n"
                            + modified_content[import_match.end() :]
                        )
                    else:
                        # Add at the beginning of the file
                        modified_content = "import pytest\n" + modified_content

                # Write the modified content back to the file
                if modified_content != content and not dry_run:
                    with open(test_file, "w") as f:
                        f.write(modified_content)

                    results["modified"] += 1
                    if verbose:
                        print(f"    Modified {test_file}")

                # Count all tests as processed
                results["processed"] += len(feature_tests)

            except Exception as e:
                print(f"Error processing {test_file}: {e}")
                results["errors"] += 1

    return results


def find_test_files_for_features(
    feature_paths: list[str], verbose: bool = False
) -> dict[str, list[str]]:
    """
    Find test files that import scenarios from feature files.

    Args:
        feature_paths: List of feature file paths
        verbose: Whether to show detailed information

    Returns:
        Dictionary mapping feature paths to lists of test file paths
    """
    result = {feature_path: [] for feature_path in feature_paths}

    # Get the behavior tests directory
    behavior_dir = (
        os.path.dirname(os.path.dirname(feature_paths[0]))
        if feature_paths
        else "tests/behavior"
    )

    # Find all Python files in the behavior tests directory
    python_files = []
    for root, _, files in os.walk(behavior_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    # Check each Python file for scenarios imports
    for python_file in python_files:
        try:
            with open(python_file) as f:
                content = f.read()

            # Check for scenarios function calls
            for feature_path in feature_paths:
                # Try different path formats (absolute, relative)
                feature_name = os.path.basename(feature_path)
                feature_rel_path = os.path.relpath(feature_path, behavior_dir)

                # Check for various ways to reference the feature file
                patterns = [
                    rf'scenarios\([\'"](?:.*?{feature_name})[\'"]',  # scenarios("...feature_name")
                    rf'scenarios\([\'"](?:.*?{feature_rel_path})[\'"]',  # scenarios("...relative_path")
                    rf"scenarios\({feature_path}",  # scenarios(feature_path)
                    rf"scenarios\(feature_file\).*?{feature_name}",  # scenarios(feature_file) with feature_name nearby
                ]

                for pattern in patterns:
                    if re.search(pattern, content):
                        result[feature_path].append(python_file)
                        if verbose:
                            print(
                                f"Found test file {python_file} for feature {feature_path}"
                            )
                        break

        except Exception as e:
            if verbose:
                print(f"Error checking {python_file}: {e}")

    return result


def main():
    """Main function."""
    args = parse_args()

    if args.verify:
        # Verify test counts
        count_results = verify_test_counts(
            category=args.category, module=args.module, verbose=args.verbose
        )

        # Verify marker detection
        marker_results = verify_marker_detection(
            category=args.category, module=args.module, verbose=args.verbose
        )

        if args.report:
            # Generate a detailed report
            report = {
                "test_counts": count_results,
                "marker_detection": marker_results,
                "timestamp": datetime.datetime.now().isoformat(),
            }

            report_file = "test_infrastructure_report.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report generated: {report_file}")

    elif args.fix_markers:
        # Verify marker detection first
        marker_results = verify_marker_detection(
            category=args.category, module=args.module, verbose=args.verbose
        )

        # Implement marker fixing logic
        print("Fixing marker detection issues...")

        # Find tests with marker discrepancies
        discrepancy_tests = {}

        # Process each marker type
        for marker in ["fast", "medium", "slow"]:
            # Find tests that are detected in files but not by pytest
            file_markers = set()
            pytest_markers = set()

            # Determine which categories to process
            categories = (
                [args.category]
                if args.category != "all"
                else list(TEST_CATEGORIES.keys())
            )

            for cat in categories:
                directory = TEST_CATEGORIES[cat]

                # Apply module filter if specified
                if args.module:
                    if not args.module.startswith(directory):
                        continue
                    directory = args.module

                # Get markers from files
                cat_file_markers = get_markers_from_files(directory)
                file_markers.update(cat_file_markers.get(marker, []))

                # Get markers from pytest
                cat_pytest_markers = get_markers_from_pytest(directory)
                pytest_markers.update(cat_pytest_markers.get(marker, []))

            # Find discrepancies
            file_only = file_markers - pytest_markers
            pytest_only = pytest_markers - file_markers

            if file_only:
                print(
                    f"Found {len(file_only)} tests with {marker} marker in files but not detected by pytest"
                )
                discrepancy_tests[f"{marker}_file_only"] = list(file_only)

            if pytest_only:
                print(
                    f"Found {len(pytest_only)} tests with {marker} marker detected by pytest but not in files"
                )
                discrepancy_tests[f"{marker}_pytest_only"] = list(pytest_only)

        # Generate a report of discrepancies
        if args.report:
            report_file = "marker_discrepancy_report.json"
            with open(report_file, "w") as f:
                json.dump(discrepancy_tests, f, indent=2)
            print(f"Discrepancy report generated: {report_file}")

        # Fix discrepancies
        fixed_count = 0

        # Fix tests that have markers in files but not detected by pytest
        for marker in ["fast", "medium", "slow"]:
            file_only_key = f"{marker}_file_only"
            if file_only_key in discrepancy_tests:
                tests = discrepancy_tests[file_only_key]
                if tests:
                    print(
                        f"Fixing {len(tests)} tests with {marker} marker in files but not detected by pytest"
                    )

                    # For each test, check the marker format and fix if needed
                    for test in tests:
                        if "::" in test:
                            file_path = test.split("::")[0]
                            try:
                                with open(file_path) as f:
                                    content = f.read()

                                # Check if the file contains the marker but in an incorrect format
                                if f"@pytest.mark.{marker}" in content:
                                    # The marker exists but might be in the wrong format or position
                                    # We'll remove it and add it again in the correct format
                                    print(f"  Fixing marker format for {test}")

                                    # Parse the file
                                    tree = ast.parse(content, filename=file_path)

                                    # Extract test name from test path
                                    parts = test.split("::")
                                    if len(parts) > 2:  # Class-based test
                                        class_name = parts[1]
                                        test_name = parts[2]

                                        # Find the class and method
                                        for node in ast.walk(tree):
                                            if (
                                                isinstance(node, ast.ClassDef)
                                                and node.name == class_name
                                            ):
                                                for child in node.body:
                                                    if (
                                                        isinstance(
                                                            child, ast.FunctionDef
                                                        )
                                                        and child.name == test_name
                                                    ):
                                                        # Remove existing marker
                                                        child.decorator_list = [
                                                            d
                                                            for d in child.decorator_list
                                                            if not (
                                                                get_marker_type_from_decorator(
                                                                    d
                                                                )
                                                                == marker
                                                            )
                                                        ]

                                                        # Add the marker in the correct format
                                                        decorator_attr = ast.Attribute(
                                                            value=ast.Attribute(
                                                                value=ast.Name(
                                                                    id="pytest",
                                                                    ctx=ast.Load(),
                                                                ),
                                                                attr="mark",
                                                                ctx=ast.Load(),
                                                            ),
                                                            attr=marker,
                                                            ctx=ast.Load(),
                                                        )

                                                        # Add the decorator to the function
                                                        child.decorator_list.insert(
                                                            0, decorator_attr
                                                        )
                                                        fixed_count += 1
                                    else:  # Function-based test
                                        test_name = parts[1]

                                        # Find the function
                                        for node in ast.walk(tree):
                                            if (
                                                isinstance(node, ast.FunctionDef)
                                                and node.name == test_name
                                            ):
                                                # Remove existing marker
                                                node.decorator_list = [
                                                    d
                                                    for d in node.decorator_list
                                                    if not (
                                                        get_marker_type_from_decorator(
                                                            d
                                                        )
                                                        == marker
                                                    )
                                                ]

                                                # Add the marker in the correct format
                                                decorator_attr = ast.Attribute(
                                                    value=ast.Attribute(
                                                        value=ast.Name(
                                                            id="pytest", ctx=ast.Load()
                                                        ),
                                                        attr="mark",
                                                        ctx=ast.Load(),
                                                    ),
                                                    attr=marker,
                                                    ctx=ast.Load(),
                                                )

                                                # Add the decorator to the function
                                                node.decorator_list.insert(
                                                    0, decorator_attr
                                                )
                                                fixed_count += 1

                                    # Generate the modified code
                                    modified_code = ast.unparse(tree)

                                    # Write the modified code back to the file
                                    with open(file_path, "w") as f:
                                        f.write(modified_code)

                            except Exception as e:
                                print(f"Error fixing marker for {test}: {e}")

        print(f"Fixed {fixed_count} marker issues")

    elif args.add_markers:
        # Collect tests without markers
        unmarked_tests = []

        # Determine which categories to process
        categories = (
            [args.category] if args.category != "all" else list(TEST_CATEGORIES.keys())
        )

        for cat in categories:
            directory = TEST_CATEGORIES[cat]

            # Apply module filter if specified
            if args.module:
                if not args.module.startswith(directory):
                    continue
                directory = args.module

            # Collect tests using the appropriate method based on category
            if cat == "behavior":
                # Use the enhanced behavior test collection for behavior tests
                from common_test_collector import collect_behavior_tests

                tests = collect_behavior_tests(directory, use_cache=False)
            else:
                # Use the regular file parsing for other test types
                tests = collect_tests_from_files(directory)

            # Filter out tests that already have markers
            for test in tests:
                file_path = test.split("::")[0] if "::" in test else test
                has_marker = False

                # Check if the test has a marker
                try:
                    with open(file_path) as f:
                        content = f.read()

                    # Parse the file using AST
                    tree = ast.parse(content, filename=file_path)

                    # Extract test name from test path
                    if "::" in test:
                        parts = test.split("::")
                        if len(parts) > 2:  # Class-based test
                            class_name = parts[1]
                            test_name = parts[2]

                            # Find the class and method
                            for node in ast.walk(tree):
                                if (
                                    isinstance(node, ast.ClassDef)
                                    and node.name == class_name
                                ):
                                    for child in node.body:
                                        if (
                                            isinstance(child, ast.FunctionDef)
                                            and child.name == test_name
                                        ):
                                            # Check if the method has a marker
                                            for decorator in child.decorator_list:
                                                if get_marker_type_from_decorator(
                                                    decorator
                                                ):
                                                    has_marker = True
                                                    break
                        else:  # Function-based test
                            test_name = parts[1]

                            # Find the function
                            for node in ast.walk(tree):
                                if (
                                    isinstance(node, ast.FunctionDef)
                                    and node.name == test_name
                                ):
                                    # Check if the function has a marker
                                    for decorator in node.decorator_list:
                                        if get_marker_type_from_decorator(decorator):
                                            has_marker = True
                                            break

                except Exception as e:
                    print(f"Error checking markers for {test}: {e}")
                    continue

                if not has_marker:
                    unmarked_tests.append(test)

        print(f"Found {len(unmarked_tests)} unmarked tests")

        # Determine if we should run in dry-run mode
        dry_run = True

        if args.apply:
            # Apply changes without confirmation
            dry_run = False
            print("Applying changes without confirmation (--apply specified)...")
        elif args.dry_run:
            # Explicitly specified dry-run mode
            print("Running in dry-run mode (--dry-run specified)...")
        else:
            # Interactive mode - ask for confirmation
            if not args.verbose:
                print("\nThis will add 'medium' markers to all unmarked tests.")
                print("Use --verbose to see which tests will be modified.")

            response = (
                input("\nDo you want to apply these changes? (y/n): ").strip().lower()
            )
            if response == "y":
                dry_run = False
                print("Applying changes...")
            else:
                print("Running in dry-run mode (no changes will be made)...")

        # Add markers to unmarked tests
        # For simplicity, we'll add medium markers to all unmarked tests
        # In a real implementation, we might use heuristics to determine the appropriate marker
        add_markers_to_tests(
            unmarked_tests, "medium", dry_run=dry_run, verbose=args.verbose
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
