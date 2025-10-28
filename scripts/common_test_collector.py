#!/usr/bin/env python3
"""
Common Test Collector

This module provides a unified interface for collecting tests across the project.
It ensures consistent test counts across different tools and scripts.

Usage:
    from scripts.common_test_collector import collect_tests, collect_tests_by_category, get_test_counts

    # Collect all tests
    all_tests = collect_tests()

    # Collect tests by category
    unit_tests = collect_tests_by_category("unit")

    # Get test counts
    counts = get_test_counts()
    print(f"Total tests: {counts['total']}")
    print(f"Unit tests: {counts['unit']}")
"""

import datetime
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import code analysis tools
try:
    from devsynth.application.code_analysis.analyzer import CodeAnalyzer
    from devsynth.application.code_analysis.ast_workflow_integration import (
        AstWorkflowIntegration,
    )
    from devsynth.application.memory.memory_manager import MemoryManager

    HAS_CODE_ANALYSIS = True
except ImportError:
    HAS_CODE_ANALYSIS = False

# Define test categories and their directories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}

# Define cache file paths
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
TEST_CACHE_FILE = os.path.join(CACHE_DIR, "test_collection_cache.json")
COMPLEXITY_CACHE_FILE = os.path.join(CACHE_DIR, "test_complexity_cache.json")
FAILURE_HISTORY_FILE = os.path.join(CACHE_DIR, "test_failure_history.json")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize code analyzer if available
code_analyzer = None
ast_workflow = None
if HAS_CODE_ANALYSIS:
    try:
        code_analyzer = CodeAnalyzer()
        # Create a simple memory manager for the AST workflow
        memory_manager = MemoryManager()
        ast_workflow = AstWorkflowIntegration(memory_manager)
    except Exception as e:
        print(f"Error initializing code analysis tools: {e}")
        HAS_CODE_ANALYSIS = False


def load_cache() -> dict[str, Any]:
    """Load the test collection cache."""
    if os.path.exists(TEST_CACHE_FILE):
        try:
            with open(TEST_CACHE_FILE) as f:
                cache = json.load(f)
                # Add cache metadata if not present
                if "metadata" not in cache:
                    cache["metadata"] = {
                        "last_updated": datetime.datetime.now().isoformat(),
                        "file_timestamps": {},
                    }
                return cache
        except (json.JSONDecodeError, OSError):
            return {
                "metadata": {
                    "last_updated": datetime.datetime.now().isoformat(),
                    "file_timestamps": {},
                }
            }
    return {
        "metadata": {
            "last_updated": datetime.datetime.now().isoformat(),
            "file_timestamps": {},
        }
    }


def save_cache(cache: dict[str, Any]) -> None:
    """Save the test collection cache."""
    with open(TEST_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def load_complexity_cache() -> dict[str, Any]:
    """Load the test complexity cache."""
    if os.path.exists(COMPLEXITY_CACHE_FILE):
        try:
            with open(COMPLEXITY_CACHE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_complexity_cache(cache: dict[str, Any]) -> None:
    """Save the test complexity cache."""
    with open(COMPLEXITY_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def load_failure_history() -> dict[str, Any]:
    """
    Load the test failure history.

    Returns:
        Dictionary with test failure history
    """
    if os.path.exists(FAILURE_HISTORY_FILE):
        try:
            with open(FAILURE_HISTORY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"tests": {}, "runs": []}
    return {"tests": {}, "runs": []}


def save_failure_history(history: dict[str, Any]) -> None:
    """
    Save the test failure history.

    Args:
        history: Dictionary with test failure history
    """
    with open(FAILURE_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def record_test_run(test_results: dict[str, bool], run_id: str | None = None) -> str:
    """
    Record the results of a test run.

    Args:
        test_results: Dictionary mapping test paths to boolean results (True for pass, False for fail)
        run_id: Optional identifier for the test run (defaults to timestamp)

    Returns:
        The run ID
    """
    # Load existing history
    history = load_failure_history()

    # Generate run ID if not provided
    if run_id is None:
        import datetime

        run_id = datetime.datetime.now().isoformat()

    # Add run to history
    run_info = {
        "id": run_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tests": len(test_results),
        "failed_tests": sum(1 for result in test_results.values() if not result),
    }
    history["runs"].append(run_info)

    # Update test failure history
    for test_path, result in test_results.items():
        if test_path not in history["tests"]:
            history["tests"][test_path] = {
                "total_runs": 0,
                "failures": 0,
                "last_run": None,
                "last_result": None,
                "failure_runs": [],
            }

        test_history = history["tests"][test_path]
        test_history["total_runs"] += 1
        test_history["last_run"] = run_id
        test_history["last_result"] = result

        if not result:
            test_history["failures"] += 1
            test_history["failure_runs"].append(run_id)

    # Save updated history
    save_failure_history(history)

    return run_id


def get_test_failure_rates(use_cache: bool = True) -> dict[str, float]:
    """
    Get failure rates for all tests.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping test paths to failure rates (0-1)
    """
    # Load failure history
    history = load_failure_history()

    # Calculate failure rates
    failure_rates = {}
    for test_path, test_history in history["tests"].items():
        if test_history["total_runs"] > 0:
            failure_rates[test_path] = (
                test_history["failures"] / test_history["total_runs"]
            )
        else:
            failure_rates[test_path] = 0.0

    return failure_rates


def get_frequently_failing_tests(
    threshold: float = 0.1, min_runs: int = 3, use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Get tests that fail frequently.

    Args:
        threshold: Failure rate threshold (0-1)
        min_runs: Minimum number of runs required
        use_cache: Whether to use cached results

    Returns:
        List of dictionaries with test path and failure information
    """
    # Load failure history
    history = load_failure_history()

    # Find frequently failing tests
    frequently_failing = []
    for test_path, test_history in history["tests"].items():
        if test_history["total_runs"] >= min_runs:
            failure_rate = test_history["failures"] / test_history["total_runs"]
            if failure_rate >= threshold:
                frequently_failing.append(
                    {
                        "path": test_path,
                        "failure_rate": failure_rate,
                        "total_runs": test_history["total_runs"],
                        "failures": test_history["failures"],
                        "last_result": test_history["last_result"],
                    }
                )

    # Sort by failure rate (highest first)
    frequently_failing.sort(key=lambda x: x["failure_rate"], reverse=True)

    return frequently_failing


def clear_cache(selective: bool = False) -> None:
    """
    Clear all cache files or selectively invalidate cache.

    Args:
        selective: If True, don't remove cache files but invalidate their content
                  This preserves structure but forces recollection of data
    """
    if selective:
        # Selectively invalidate cache by updating metadata
        if os.path.exists(TEST_CACHE_FILE):
            try:
                cache = load_cache()
                # Set last_updated to a past time to force invalidation
                cache["metadata"]["last_updated"] = "2000-01-01T00:00:00"
                # Clear file timestamps to force rechecking
                cache["metadata"]["file_timestamps"] = {}
                save_cache(cache)
                print("Test cache selectively invalidated")
            except Exception as e:
                print(f"Error selectively invalidating test cache: {e}")
                # Fall back to complete removal
                os.remove(TEST_CACHE_FILE)

        # Selectively invalidate complexity cache
        if os.path.exists(COMPLEXITY_CACHE_FILE):
            try:
                complexity_cache = load_complexity_cache()
                # Clear the cache but keep the file
                save_complexity_cache({})
                print("Complexity cache selectively invalidated")
            except Exception as e:
                print(f"Error selectively invalidating complexity cache: {e}")
                # Fall back to complete removal
                os.remove(COMPLEXITY_CACHE_FILE)

        # Failure history is kept intact as it's valuable historical data
    else:
        # Complete cache removal
        if os.path.exists(TEST_CACHE_FILE):
            os.remove(TEST_CACHE_FILE)
        if os.path.exists(COMPLEXITY_CACHE_FILE):
            os.remove(COMPLEXITY_CACHE_FILE)
        if os.path.exists(FAILURE_HISTORY_FILE):
            os.remove(FAILURE_HISTORY_FILE)


def invalidate_cache_for_files(file_paths: list[str], verbose: bool = False) -> None:
    """
    Invalidate cache for specific files.

    This function updates the file timestamps in the cache to force recollection
    of data for the specified files, without invalidating the entire cache.

    Args:
        file_paths: List of file paths to invalidate in the cache
        verbose: Whether to print verbose output
    """
    if not file_paths:
        if verbose:
            print("No files to invalidate")
        return

    if verbose:
        print(f"Invalidating cache for {len(file_paths)} files")

    # Load the cache
    if os.path.exists(TEST_CACHE_FILE):
        try:
            cache = load_cache()

            # Get the file timestamps
            if "file_timestamps" not in cache["metadata"]:
                cache["metadata"]["file_timestamps"] = {}

            # Update timestamps for the specified files
            # Setting to 0 forces rechecking as any current timestamp will be greater
            updated_count = 0
            for file_path in file_paths:
                if os.path.exists(file_path):
                    cache["metadata"]["file_timestamps"][file_path] = 0
                    updated_count += 1

            # Save the updated cache
            save_cache(cache)

            if verbose:
                print(f"Updated timestamps for {updated_count} files in cache")

            # Also invalidate any cached marker data
            if "markers_fast,medium,slow" in cache:
                del cache["markers_fast,medium,slow"]
                save_cache(cache)
                if verbose:
                    print("Invalidated cached marker data")
        except Exception as e:
            print(f"Error invalidating cache for files: {e}")
    elif verbose:
        print("Cache file does not exist, nothing to invalidate")


def calculate_test_complexity(test_path: str, use_cache: bool = True) -> dict[str, Any]:
    """
    Calculate complexity metrics for a test file or specific test.

    Args:
        test_path: Path to the test file or specific test
        use_cache: Whether to use cached results

    Returns:
        Dictionary with complexity metrics
    """
    if not HAS_CODE_ANALYSIS or not code_analyzer or not ast_workflow:
        return {"error": "Code analysis tools not available"}

    # Load complexity cache
    cache = load_complexity_cache() if use_cache else {}

    # Check if we have cached results
    if use_cache and test_path in cache:
        return cache[test_path]

    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
        test_name = test_path.split("::")[-1]
        if "(" in test_name:  # Handle parameterized tests
            test_name = test_name.split("(")[0]
    else:
        file_path = test_path
        test_name = None

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        # Analyze the file
        file_analysis = code_analyzer.analyze_file(file_path)

        # If we're analyzing a specific test, extract just that function
        if test_name:
            # Find the test function
            test_function = None
            for func in file_analysis.get_functions():
                if func["name"] == test_name:
                    test_function = func
                    break

            if not test_function:
                return {"error": f"Test function not found: {test_name}"}

            # Calculate complexity metrics for this test
            metrics = {
                "lines_of_code": 0,  # We don't have this information for individual functions
                "parameter_count": len(test_function.get("params", [])),
                "has_docstring": bool(test_function.get("docstring")),
            }

            # Use ast_workflow to calculate more advanced metrics
            # We need to read the function code to do this
            with open(file_path) as f:
                code = f.read()

            # This is a simplified approach - in a real implementation,
            # we would extract just the function code
            complexity_metrics = ast_workflow._calculate_complexity(file_analysis)
            readability_metrics = ast_workflow._calculate_readability(file_analysis)
            maintainability_metrics = ast_workflow._calculate_maintainability(
                file_analysis
            )

            metrics.update(
                {
                    "complexity": complexity_metrics,
                    "readability": readability_metrics,
                    "maintainability": maintainability_metrics,
                    "risk_score": 1.0
                    - (
                        (
                            complexity_metrics
                            + readability_metrics
                            + maintainability_metrics
                        )
                        / 3.0
                    ),
                }
            )
        else:
            # Calculate complexity metrics for the entire file
            metrics = file_analysis.get_metrics()

            # Add more advanced metrics
            complexity_metrics = ast_workflow._calculate_complexity(file_analysis)
            readability_metrics = ast_workflow._calculate_readability(file_analysis)
            maintainability_metrics = ast_workflow._calculate_maintainability(
                file_analysis
            )

            metrics.update(
                {
                    "complexity": complexity_metrics,
                    "readability": readability_metrics,
                    "maintainability": maintainability_metrics,
                    "risk_score": 1.0
                    - (
                        (
                            complexity_metrics
                            + readability_metrics
                            + maintainability_metrics
                        )
                        / 3.0
                    ),
                }
            )

        # Cache the results
        if use_cache:
            cache[test_path] = metrics
            save_complexity_cache(cache)

        return metrics
    except Exception as e:
        return {"error": f"Error calculating complexity: {str(e)}"}


def collect_tests_with_pytest(directory: str, use_cache: bool = True) -> list[str]:
    """
    Collect tests from a directory using pytest.

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    cache = load_cache() if use_cache else {}
    cache_key = f"pytest_{directory}"

    if use_cache and cache_key in cache:
        return cache[cache_key]

    cmd = [sys.executable, "-m", "pytest", directory, "--collect-only", "-q"]

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Extract test paths from output
        tests = []
        for line in result.stdout.split("\n"):
            if line.strip() and not line.startswith("="):
                tests.append(line.strip())

        if use_cache:
            cache[cache_key] = tests
            save_cache(cache)

        return tests
    except Exception as e:
        print(f"Error collecting tests with pytest: {e}")
        return []


def collect_behavior_tests(directory: str, use_cache: bool = True) -> list[str]:
    """
    Collect behavior tests from a directory.

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    cache = load_cache() if use_cache else {}
    cache_key = f"behavior_{directory}"

    if use_cache and cache_key in cache:
        return cache[cache_key]

    # Use the enhanced Gherkin parser
    try:
        # Import the enhanced Gherkin parser
        from enhanced_gherkin_parser import generate_test_paths, parse_feature_directory

        # Parse all feature files in the directory
        features = parse_feature_directory(directory)

        # Generate test paths for all scenarios and examples
        test_paths = generate_test_paths(features)

        if use_cache:
            cache[cache_key] = test_paths
            save_cache(cache)

        return test_paths

    except ImportError:
        # Fall back to the original implementation if the enhanced parser is not available
        print(
            "Warning: enhanced_gherkin_parser not found, falling back to basic parser"
        )

        # Find all feature files
        feature_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".feature"):
                    feature_files.append(os.path.join(root, file))

        # Find all step definition files
        step_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    step_files.append(os.path.join(root, file))

        # Extract scenarios from feature files
        scenarios = []
        for feature_file in feature_files:
            with open(feature_file) as f:
                content = f.read()

                # Extract regular scenarios
                scenario_matches = re.finditer(
                    r"^\s*Scenario:(.+)$", content, re.MULTILINE
                )
                for match in scenario_matches:
                    scenario_name = match.group(1).strip()
                    scenarios.append(f"{feature_file}::{scenario_name}")

                # Extract scenario outlines (basic support)
                outline_matches = re.finditer(
                    r"^\s*Scenario Outline:(.+)$", content, re.MULTILINE
                )
                for match in outline_matches:
                    scenario_name = match.group(1).strip()
                    scenarios.append(f"{feature_file}::{scenario_name}")

        if use_cache:
            cache[cache_key] = scenarios
            save_cache(cache)

        return scenarios


@lru_cache(maxsize=None)
def collect_tests_by_category(category: str, use_cache: bool = True) -> list[str]:
    """
    Collect tests for a specific category.

    Args:
        category: Test category (unit, integration, behavior, performance, property)
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    if category not in TEST_CATEGORIES:
        raise ValueError(f"Unknown test category: {category}")

    directory = TEST_CATEGORIES[category]

    if category == "behavior":
        return collect_behavior_tests(directory, use_cache)
    else:
        return collect_tests_with_pytest(directory, use_cache)


def collect_tests(use_cache: bool = True) -> list[str]:
    """
    Collect all tests across all categories.

    Args:
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    all_tests = []
    for category in TEST_CATEGORIES:
        all_tests.extend(collect_tests_by_category(category, use_cache))
    return all_tests


def get_tests_with_complexity(
    tests: list[str], use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Get tests with their complexity metrics.

    Args:
        tests: List of test paths
        use_cache: Whether to use cached results

    Returns:
        List of dictionaries with test path and complexity metrics
    """
    result = []
    for test_path in tests:
        complexity = calculate_test_complexity(test_path, use_cache)
        result.append({"path": test_path, "complexity": complexity})
    return result


def get_high_risk_tests(
    tests: list[str], threshold: float = 0.5, use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Get tests with risk score above the threshold.

    Args:
        tests: List of test paths
        threshold: Risk score threshold (0-1, higher means more risky)
        use_cache: Whether to use cached results

    Returns:
        List of dictionaries with test path and complexity metrics, sorted by risk score
    """
    tests_with_complexity = get_tests_with_complexity(tests, use_cache)
    high_risk_tests = []

    for test in tests_with_complexity:
        complexity = test["complexity"]
        if "error" not in complexity and complexity.get("risk_score", 0) >= threshold:
            high_risk_tests.append(test)

    # Sort by risk score (highest first)
    high_risk_tests.sort(
        key=lambda x: x["complexity"].get("risk_score", 0), reverse=True
    )

    return high_risk_tests


def analyze_test_dependencies(
    test_paths: list[str], use_cache: bool = True
) -> dict[str, list[str]]:
    """
    Analyze dependencies between tests.

    Args:
        test_paths: List of test paths
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping test paths to lists of dependent test paths
    """
    if not HAS_CODE_ANALYSIS or not code_analyzer:
        return {"error": "Code analysis tools not available"}

    # Create a cache key for dependencies
    cache_key = "dependencies"
    cache = load_cache() if use_cache else {}

    # Check if we have cached results
    if use_cache and cache_key in cache:
        return cache[cache_key]

    # Extract file paths from test paths
    file_paths = []
    for test_path in test_paths:
        if "::" in test_path:
            file_path = test_path.split("::")[0]
        else:
            file_path = test_path
        if file_path not in file_paths:
            file_paths.append(file_path)

    # Analyze each file
    file_analyses = {}
    for file_path in file_paths:
        if os.path.exists(file_path):
            file_analyses[file_path] = code_analyzer.analyze_file(file_path)

    # Build a map of imports
    import_map = {}
    for file_path, analysis in file_analyses.items():
        imports = []
        for import_info in analysis.get_imports():
            if "from_module" in import_info:
                imports.append(import_info["from_module"])
            else:
                imports.append(import_info["name"].split(".")[0])
        import_map[file_path] = imports

    # Build a map of test files to module names
    module_map = {}
    for file_path in file_paths:
        if os.path.exists(file_path):
            # Extract module name from file path
            rel_path = os.path.relpath(file_path)
            module_path = os.path.splitext(rel_path)[0]
            module_name = module_path.replace(os.path.sep, ".")
            module_map[file_path] = module_name

    # Build dependency graph
    dependencies = {}
    for test_path in test_paths:
        dependencies[test_path] = []

    # For each test, find other tests that import its module
    for test_path in test_paths:
        if "::" in test_path:
            file_path = test_path.split("::")[0]
        else:
            file_path = test_path

        if file_path in module_map:
            module_name = module_map[file_path]

            # Find other tests that import this module
            for other_file_path, imports in import_map.items():
                if other_file_path != file_path:
                    # Check if this module is imported by the other file
                    for import_name in imports:
                        if module_name.startswith(
                            import_name
                        ) or import_name.startswith(module_name):
                            # Find all tests in the other file
                            for other_test_path in test_paths:
                                if other_test_path.startswith(other_file_path):
                                    dependencies[test_path].append(other_test_path)

    # Cache the results
    if use_cache:
        cache[cache_key] = dependencies
        save_cache(cache)

    return dependencies


def get_dependent_tests(
    test_path: str, dependencies: dict[str, list[str]]
) -> list[str]:
    """
    Get tests that depend on the given test.

    Args:
        test_path: Path to the test
        dependencies: Dictionary mapping test paths to lists of dependent test paths

    Returns:
        List of test paths that depend on the given test
    """
    if test_path in dependencies:
        return dependencies[test_path]
    return []


def filter_tests_by_pattern(tests: list[str], pattern: str) -> list[str]:
    """
    Filter tests by name pattern.

    Args:
        tests: List of test paths
        pattern: Pattern to match (supports * and ? wildcards)

    Returns:
        List of test paths that match the pattern
    """
    import fnmatch

    # Convert pattern to lowercase for case-insensitive matching
    pattern = pattern.lower()

    # Filter tests that match the pattern
    matched_tests = []
    for test_path in tests:
        # Convert to lowercase for case-insensitive matching
        test_path_lower = test_path.lower()

        # Check if the pattern matches any part of the test path
        if fnmatch.fnmatch(test_path_lower, f"*{pattern}*"):
            matched_tests.append(test_path)

    return matched_tests


def filter_tests_by_module(tests: list[str], module: str) -> list[str]:
    """
    Filter tests by module name.

    Args:
        tests: List of test paths
        module: Module name to match

    Returns:
        List of test paths that belong to the specified module
    """
    # Convert module to lowercase for case-insensitive matching
    module = module.lower()

    # Filter tests that belong to the specified module
    matched_tests = []
    for test_path in tests:
        # Convert to lowercase for case-insensitive matching
        test_path_lower = test_path.lower()

        # Check if the test path contains the module name
        if module in test_path_lower:
            matched_tests.append(test_path)

    return matched_tests


def apply_filters(tests: list[str], args) -> list[str]:
    """
    Apply all filters to the list of tests.

    Args:
        tests: List of test paths
        args: Command-line arguments

    Returns:
        Filtered list of test paths
    """
    filtered_tests = tests.copy()

    # Apply inclusion filters
    if args.pattern:
        filtered_tests = filter_tests_by_pattern(filtered_tests, args.pattern)

    if args.module:
        filtered_tests = filter_tests_by_module(filtered_tests, args.module)

    # Apply exclusion filters
    if args.exclude_pattern:
        exclude_tests = filter_tests_by_pattern(filtered_tests, args.exclude_pattern)
        filtered_tests = [t for t in filtered_tests if t not in exclude_tests]

    if args.exclude_module:
        exclude_tests = filter_tests_by_module(filtered_tests, args.exclude_module)
        filtered_tests = [t for t in filtered_tests if t not in exclude_tests]

    return filtered_tests


def generate_junit_xml_report(
    tests: list[str],
    test_results: dict[str, bool] | None = None,
    output_file: str = "test_report.xml",
) -> None:
    """
    Generate a JUnit XML report for the tests.

    Args:
        tests: List of test paths
        test_results: Optional dictionary mapping test paths to boolean results (True for pass, False for fail)
        output_file: Path to the output file
    """
    # Create the root element
    test_suite = ET.Element("testsuite")
    test_suite.set("name", "DevSynth Tests")
    test_suite.set("tests", str(len(tests)))

    # Set timestamp
    timestamp = datetime.datetime.now().isoformat()
    test_suite.set("timestamp", timestamp)

    # If test results are provided, calculate failures
    failures = 0
    if test_results:
        for test_path, result in test_results.items():
            if not result and test_path in tests:
                failures += 1
    test_suite.set("failures", str(failures))

    # Add test cases
    for test_path in tests:
        test_case = ET.SubElement(test_suite, "testcase")

        # Extract class name and test name from test path
        if "::" in test_path:
            parts = test_path.split("::")
            if len(parts) > 2:  # Class-based test
                file_path = parts[0]
                class_name = parts[1]
                test_name = parts[2]
                test_case.set("classname", f"{file_path}::{class_name}")
                test_case.set("name", test_name)
            else:  # Function-based test
                file_path = parts[0]
                test_name = parts[1]
                test_case.set("classname", file_path)
                test_case.set("name", test_name)
        else:
            # For file paths without specific test names
            test_case.set("classname", os.path.dirname(test_path))
            test_case.set("name", os.path.basename(test_path))

        # Add failure information if available
        if test_results and test_path in test_results and not test_results[test_path]:
            failure = ET.SubElement(test_case, "failure")
            failure.set("message", "Test failed")
            failure.set("type", "failure")
            failure.text = f"Test {test_path} failed"

    # Create the XML tree and write to file
    tree = ET.ElementTree(test_suite)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    print(f"JUnit XML report written to {output_file}")


def generate_json_report(
    tests: list[str],
    test_results: dict[str, bool] | None = None,
    complexity_metrics: dict[str, dict[str, Any]] | None = None,
    dependencies: dict[str, list[str]] | None = None,
    failure_rates: dict[str, float] | None = None,
    output_file: str = "test_report.json",
) -> None:
    """
    Generate a JSON report for the tests.

    Args:
        tests: List of test paths
        test_results: Optional dictionary mapping test paths to boolean results (True for pass, False for fail)
        complexity_metrics: Optional dictionary mapping test paths to complexity metrics
        dependencies: Optional dictionary mapping test paths to lists of dependent test paths
        failure_rates: Optional dictionary mapping test paths to failure rates
        output_file: Path to the output file
    """
    # Create the report structure
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tests": len(tests),
        "tests": {},
    }

    # If test results are provided, calculate summary statistics
    if test_results:
        passed = sum(1 for result in test_results.values() if result)
        failed = sum(1 for result in test_results.values() if not result)
        report["summary"] = {
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(test_results) if test_results else 0,
        }

    # Add test details
    for test_path in tests:
        test_info = {}

        # Add test results if available
        if test_results and test_path in test_results:
            test_info["result"] = "pass" if test_results[test_path] else "fail"

        # Add complexity metrics if available
        if complexity_metrics and test_path in complexity_metrics:
            test_info["complexity"] = complexity_metrics[test_path]

        # Add dependencies if available
        if dependencies and test_path in dependencies:
            test_info["dependents"] = dependencies[test_path]

        # Add failure rate if available
        if failure_rates and test_path in failure_rates:
            test_info["failure_rate"] = failure_rates[test_path]

        report["tests"][test_path] = test_info

    # Write the report to file
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"JSON report written to {output_file}")


def get_test_counts(use_cache: bool = True) -> dict[str, int]:
    """
    Get counts of tests by category.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary with test counts by category
    """
    counts = {}
    for category in TEST_CATEGORIES:
        tests = collect_tests_by_category(category, use_cache)
        counts[category] = len(tests)

    counts["total"] = sum(counts.values())
    return counts


def check_test_has_marker(
    test_path: str,
    marker_types: list[str] = ["fast", "medium", "slow"],
    record_timestamp: bool = True,
) -> tuple[bool, str | None]:
    """
    Check if a test has a speed marker.

    Args:
        test_path: Path to the test
        marker_types: List of marker types to check for
        record_timestamp: Whether to record the file modification time

    Returns:
        Tuple of (has_marker, marker_type)

    Note:
        This function uses an aggressive approach to marker detection:
        1. First, it tries to find markers specifically associated with the test function
        2. If that fails, it searches the entire file for any marker
        3. It handles various edge cases:
           - Markers on the same line as the function definition
           - Markers on a separate line before the function definition
           - Markers after the function definition (incorrectly placed)
           - Markers with or without trailing whitespace/parentheses
    """
    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
    else:
        file_path = test_path

    # Check if the file exists
    if not os.path.exists(file_path):
        return False, None

    # Get file modification time if requested
    if record_timestamp:
        # Load cache to update file timestamp
        cache = load_cache()
        mtime = os.path.getmtime(file_path)
        cache["metadata"]["file_timestamps"][file_path] = mtime
        save_cache(cache)

    # Read the file content
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False, None

    # Extract test name from test path
    test_name = None
    class_name = None

    if "::" in test_path:
        parts = test_path.split("::")
        if len(parts) > 2:  # Class-based test
            file_path = parts[0]
            class_name = parts[1]
            test_name = parts[2]
        else:  # Function-based test
            file_path = parts[0]
            test_name = parts[1]

        # Handle parameterized tests
        if test_name and "(" in test_name:
            test_name = test_name.split("(")[0]

    # If test name is provided, check for markers for that specific test
    if test_name:
        # Different patterns for class-based and function-based tests
        if class_name:
            # Find the class definition
            class_pattern = re.compile(rf"class\s+{re.escape(class_name)}\s*\(")
            class_match = class_pattern.search(content)

            if class_match:
                # Find the test method within the class
                # Look from class definition to the end of the file
                class_content = content[class_match.start() :]
                test_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
                test_match = test_pattern.search(class_content)

                if test_match:
                    # Adjust position to be relative to the entire file
                    test_pos = class_match.start() + test_match.start()

                    # Look for markers before the test method (within the class)
                    # Increase search context to 1000 chars to better handle class-based tests
                    start_pos = max(class_match.start(), test_pos - 1000)
                    test_context_before = content[start_pos:test_pos]

                    # Also look for markers after the test method (incorrectly placed)
                    # Look at the next 10 lines after the test method
                    end_pos = test_pos + 500  # Approximately 10 lines
                    end_pos = min(end_pos, len(content))
                    test_context_after = content[test_pos:end_pos]

                    for marker_type in marker_types:
                        # More flexible pattern to handle different formatting styles
                        # Match both with and without trailing whitespace/parentheses
                        marker_pattern = re.compile(
                            rf"@pytest\.mark\.{marker_type}($|[\s\(])"
                        )
                        if marker_pattern.search(
                            test_context_before
                        ) or marker_pattern.search(test_context_after):
                            return True, marker_type
        else:
            # Find the test function
            test_pattern = re.compile(rf"def\s+{re.escape(test_name)}\s*\(")
            test_match = test_pattern.search(content)

            if test_match:
                # Look for markers before the test function
                # Increase search context to 1000 chars to better handle decorators
                start_pos = max(0, test_match.start() - 1000)
                test_context_before = content[start_pos : test_match.start()]

                # Also look for markers after the test function (incorrectly placed)
                # Look at the next 10 lines after the test function
                end_pos = test_match.start() + 500  # Approximately 10 lines
                end_pos = min(end_pos, len(content))
                test_context_after = content[test_match.start() : end_pos]

                for marker_type in marker_types:
                    # More flexible pattern to handle different formatting styles
                    # Match both with and without trailing whitespace/parentheses
                    marker_pattern = re.compile(
                        rf"@pytest\.mark\.{marker_type}($|[\s\(])"
                    )
                    if marker_pattern.search(
                        test_context_before
                    ) or marker_pattern.search(test_context_after):
                        return True, marker_type

    # If we have a specific test name but didn't find a marker specifically for it,
    # we'll be more aggressive and check for any marker in the file
    if test_name:
        # Count how many markers of each type exist in the file
        marker_counts = {}
        for marker_type in marker_types:
            marker_pattern = re.compile(rf"@pytest\.mark\.{marker_type}($|[\s\(])")
            matches = marker_pattern.findall(content)
            marker_counts[marker_type] = len(matches)

        # If there's only one type of marker in the file, assume it applies to all tests
        non_zero_markers = [m for m, count in marker_counts.items() if count > 0]
        if len(non_zero_markers) == 1:
            return True, non_zero_markers[0]

    # As a last resort, check for markers in the entire file
    for marker_type in marker_types:
        # More flexible pattern to handle different formatting styles
        # Match both with and without trailing whitespace/parentheses
        marker_pattern = re.compile(rf"@pytest\.mark\.{marker_type}($|[\s\(])")
        if marker_pattern.search(content):
            return True, marker_type

    return False, None


def get_tests_with_markers(
    marker_types: list[str] = ["fast", "medium", "slow"], use_cache: bool = True
) -> dict[str, dict[str, list[str]]]:
    """
    Get tests with specific markers across all categories.

    Args:
        marker_types: List of marker types to check for
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping categories to marker types to lists of test paths
    """
    cache = load_cache() if use_cache else {}
    cache_key = f"markers_{','.join(marker_types)}"

    # Always check if any files have been modified since the cache was created,
    # even when use_cache is True, to ensure we detect newly added markers
    cache_valid = False
    if use_cache and cache_key in cache:
        # Get the timestamp when the cache was last updated
        last_updated = cache["metadata"].get("last_updated", "")
        if last_updated:
            try:
                last_updated_time = datetime.datetime.fromisoformat(
                    last_updated
                ).timestamp()

                # Check if any test files have been modified since the cache was last updated
                cache_valid = True
                cached_timestamps = cache["metadata"].get("file_timestamps", {})

                # If we have no timestamps, the cache is invalid
                if not cached_timestamps:
                    cache_valid = False
                    print("No file timestamps in cache, invalidating cache")
                else:
                    # Check all test directories for modified files
                    for category in TEST_CATEGORIES:
                        test_dir = TEST_CATEGORIES[category]
                        if os.path.exists(test_dir):
                            for root, _, files in os.walk(test_dir):
                                for file in files:
                                    if file.endswith(".py"):
                                        file_path = os.path.join(root, file)
                                        if os.path.exists(file_path):
                                            current_mtime = os.path.getmtime(file_path)
                                            cached_mtime = cached_timestamps.get(
                                                file_path, 0
                                            )

                                            # If the file has been modified or is new, invalidate the cache
                                            if current_mtime > cached_mtime:
                                                print(
                                                    f"File {file_path} has been modified, invalidating cache"
                                                )
                                                cache_valid = False
                                                break
                                if not cache_valid:
                                    break
                        if not cache_valid:
                            break
            except (ValueError, TypeError):
                cache_valid = False
                print(
                    f"Invalid last_updated timestamp: {last_updated}, invalidating cache"
                )

    # Return cached results if they're valid
    if cache_valid:
        return cache[cache_key]

    # Otherwise, collect markers from scratch
    result = {}
    for category in TEST_CATEGORIES:
        result[category] = {}
        for marker_type in marker_types:
            result[category][marker_type] = []

        tests = collect_tests_by_category(category, use_cache)
        for test_path in tests:
            has_marker, marker_type = check_test_has_marker(test_path, marker_types)
            if has_marker and marker_type:
                result[category][marker_type].append(test_path)

    if use_cache:
        # Update cache with new results and current timestamp
        cache[cache_key] = result
        cache["metadata"]["last_updated"] = datetime.datetime.now().isoformat()

        # Update file timestamps for all test files
        if "file_timestamps" not in cache["metadata"]:
            cache["metadata"]["file_timestamps"] = {}

        for category in TEST_CATEGORIES:
            test_dir = TEST_CATEGORIES[category]
            if os.path.exists(test_dir):
                for root, _, files in os.walk(test_dir):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                cache["metadata"]["file_timestamps"][file_path] = (
                                    os.path.getmtime(file_path)
                                )

        save_cache(cache)

    return result


def get_marker_counts(use_cache: bool = True) -> dict[str, dict[str, int]]:
    """
    Get counts of tests with specific markers across all categories.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping categories to marker types to counts
    """
    tests_with_markers = get_tests_with_markers(use_cache=use_cache)

    result = {}
    for category in tests_with_markers:
        result[category] = {}
        for marker_type in tests_with_markers[category]:
            result[category][marker_type] = len(
                tests_with_markers[category][marker_type]
            )

    # Add totals
    result["total"] = {}
    for marker_type in ["fast", "medium", "slow"]:
        result["total"][marker_type] = sum(
            result[category][marker_type] for category in TEST_CATEGORIES
        )

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Common Test Collector")
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to collect",
    )
    parser.add_argument("--count", action="store_true", help="Show test counts")
    parser.add_argument(
        "--markers", action="store_true", help="Show tests with markers"
    )
    parser.add_argument(
        "--marker-counts", action="store_true", help="Show counts of tests with markers"
    )
    parser.add_argument(
        "--list-marked-tests", action="store_true", help="List all tests with markers"
    )
    parser.add_argument(
        "--marker-type",
        choices=["fast", "medium", "slow"],
        default="medium",
        help="Marker type to list",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Don't use cached results"
    )
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache")

    # Add complexity-related arguments
    complexity_group = parser.add_argument_group("Complexity Analysis")
    complexity_group.add_argument(
        "--complexity", action="store_true", help="Show complexity metrics for tests"
    )
    complexity_group.add_argument(
        "--high-risk", action="store_true", help="Show high-risk tests"
    )
    complexity_group.add_argument(
        "--risk-threshold",
        type=float,
        default=0.5,
        help="Risk score threshold (0-1, higher means more risky)",
    )
    complexity_group.add_argument(
        "--sort-by-risk",
        action="store_true",
        help="Sort tests by risk score (highest first)",
    )
    complexity_group.add_argument(
        "--limit", type=int, default=0, help="Limit the number of tests shown"
    )

    # Add dependency-related arguments
    dependency_group = parser.add_argument_group("Dependency Analysis")
    dependency_group.add_argument(
        "--dependencies", action="store_true", help="Show dependencies between tests"
    )
    dependency_group.add_argument(
        "--dependents",
        metavar="TEST_PATH",
        help="Show tests that depend on the specified test",
    )
    dependency_group.add_argument(
        "--sort-by-dependencies",
        action="store_true",
        help="Sort tests by number of dependents (highest first)",
    )
    dependency_group.add_argument(
        "--min-dependents",
        type=int,
        default=0,
        help="Show only tests with at least this many dependents",
    )

    # Add failure history-related arguments
    failure_group = parser.add_argument_group("Failure History")
    failure_group.add_argument(
        "--record-results",
        metavar="RESULTS_FILE",
        help='Record test results from a JSON file (format: {"test_path": true/false, ...})',
    )
    failure_group.add_argument(
        "--failure-rates", action="store_true", help="Show failure rates for tests"
    )
    failure_group.add_argument(
        "--frequently-failing",
        action="store_true",
        help="Show frequently failing tests",
    )
    failure_group.add_argument(
        "--failure-threshold",
        type=float,
        default=0.1,
        help="Failure rate threshold (0-1, higher means more failures)",
    )
    failure_group.add_argument(
        "--min-runs",
        type=int,
        default=3,
        help="Minimum number of runs required for failure analysis",
    )
    failure_group.add_argument(
        "--sort-by-failures",
        action="store_true",
        help="Sort tests by failure rate (highest first)",
    )

    # Add filtering-related arguments
    filter_group = parser.add_argument_group("Test Filtering")
    filter_group.add_argument(
        "--pattern",
        metavar="PATTERN",
        help="Filter tests by name pattern (supports * and ? wildcards)",
    )
    filter_group.add_argument(
        "--module", metavar="MODULE", help="Filter tests by module name"
    )
    filter_group.add_argument(
        "--exclude-pattern",
        metavar="PATTERN",
        help="Exclude tests matching the pattern",
    )
    filter_group.add_argument(
        "--exclude-module",
        metavar="MODULE",
        help="Exclude tests from the specified module",
    )

    # Add reporting-related arguments
    report_group = parser.add_argument_group("Reporting")
    report_group.add_argument(
        "--junit-xml", metavar="FILE", help="Generate a JUnit XML report"
    )
    report_group.add_argument(
        "--json-report", metavar="FILE", help="Generate a JSON report"
    )
    report_group.add_argument(
        "--include-complexity",
        action="store_true",
        help="Include complexity metrics in the JSON report",
    )
    report_group.add_argument(
        "--include-dependencies",
        action="store_true",
        help="Include dependencies in the JSON report",
    )
    report_group.add_argument(
        "--include-failure-rates",
        action="store_true",
        help="Include failure rates in the JSON report",
    )
    report_group.add_argument(
        "--use-test-results",
        metavar="RESULTS_FILE",
        help="Use test results from a JSON file for the report",
    )

    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()
        print("Cache cleared.")

    use_cache = not args.no_cache

    if args.count:
        counts = get_test_counts(use_cache=use_cache)
        print("Test counts:")
        for category, count in counts.items():
            print(f"  {category}: {count}")

    if args.markers:
        tests_with_markers = get_tests_with_markers(use_cache=use_cache)
        print("Tests with markers:")
        for category in tests_with_markers:
            print(f"  {category}:")
            for marker_type in tests_with_markers[category]:
                print(
                    f"    {marker_type}: {len(tests_with_markers[category][marker_type])}"
                )
                for test_path in tests_with_markers[category][marker_type]:
                    print(f"      {test_path}")

    if args.marker_counts:
        marker_counts = get_marker_counts(use_cache=use_cache)
        print("Marker counts:")
        for category in marker_counts:
            print(f"  {category}:")
            for marker_type, count in marker_counts[category].items():
                print(f"    {marker_type}: {count}")

    if args.list_marked_tests:
        tests_with_markers = get_tests_with_markers(use_cache=use_cache)
        marker_type = args.marker_type
        print(f"Tests with {marker_type} marker:")
        for category in tests_with_markers:
            if (
                marker_type in tests_with_markers[category]
                and tests_with_markers[category][marker_type]
            ):
                print(f"  {category}:")
                for test_path in tests_with_markers[category][marker_type]:
                    print(f"    {test_path}")
                    # Check if the file exists
                    if "::" in test_path:
                        file_path = test_path.split("::")[0]
                        if os.path.exists(file_path):
                            # Print the first 5 lines of the file
                            with open(file_path) as f:
                                first_lines = "".join(f.readlines()[:5])
                                print(
                                    f"      First 5 lines: {first_lines.strip().replace('\n', ' | ')}"
                                )

    # Handle record-results argument
    if args.record_results:
        if os.path.exists(args.record_results):
            try:
                with open(args.record_results) as f:
                    test_results = json.load(f)

                # Validate test results format
                if not isinstance(test_results, dict):
                    print(
                        f"Error: Results file must contain a JSON object mapping test paths to boolean results"
                    )
                    sys.exit(1)

                # Convert all values to boolean
                test_results = {k: bool(v) for k, v in test_results.items()}

                # Record the test run
                run_id = record_test_run(test_results)

                print(f"Recorded test run with ID: {run_id}")
                print(f"Total tests: {len(test_results)}")
                print(
                    f"Failed tests: {sum(1 for result in test_results.values() if not result)}"
                )
                print(
                    f"Pass rate: {sum(1 for result in test_results.values() if result) / len(test_results) * 100:.1f}%"
                )
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error reading results file: {e}")
                sys.exit(1)
        else:
            print(f"Error: Results file not found: {args.record_results}")
            sys.exit(1)

    # Handle reporting arguments
    if args.junit_xml or args.json_report:
        # Collect tests if not already done
        if "tests" not in locals():
            if args.category == "all":
                tests = collect_tests(use_cache=use_cache)
            else:
                tests = collect_tests_by_category(args.category, use_cache=use_cache)

            # Apply filters
            tests = apply_filters(tests, args)

        # Load test results if specified
        test_results = None
        if args.use_test_results:
            if os.path.exists(args.use_test_results):
                try:
                    with open(args.use_test_results) as f:
                        test_results = json.load(f)

                    # Validate test results format
                    if not isinstance(test_results, dict):
                        print(
                            f"Error: Results file must contain a JSON object mapping test paths to boolean results"
                        )
                        sys.exit(1)

                    # Convert all values to boolean
                    test_results = {k: bool(v) for k, v in test_results.items()}
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Error reading results file: {e}")
                    sys.exit(1)
            else:
                print(f"Error: Results file not found: {args.use_test_results}")
                sys.exit(1)

        # Generate JUnit XML report if requested
        if args.junit_xml:
            generate_junit_xml_report(tests, test_results, args.junit_xml)

        # Generate JSON report if requested
        if args.json_report:
            # Collect additional data if requested
            complexity_metrics = None
            dependencies = None
            failure_rates = None

            if args.include_complexity and HAS_CODE_ANALYSIS:
                print("Collecting complexity metrics...")
                complexity_metrics = {}
                for test_path in tests:
                    complexity = calculate_test_complexity(test_path, use_cache)
                    if "error" not in complexity:
                        complexity_metrics[test_path] = complexity

            if args.include_dependencies:
                print("Analyzing dependencies...")
                dependencies_result = analyze_test_dependencies(tests, use_cache)
                if (
                    not isinstance(dependencies_result, dict)
                    or "error" not in dependencies_result
                ):
                    dependencies = dependencies_result

            if args.include_failure_rates:
                print("Calculating failure rates...")
                failure_rates = get_test_failure_rates(use_cache)
                # Filter to only include tests in the current set
                failure_rates = {k: v for k, v in failure_rates.items() if k in tests}

            generate_json_report(
                tests,
                test_results,
                complexity_metrics,
                dependencies,
                failure_rates,
                args.json_report,
            )

    # Handle complexity-related arguments
    if (
        args.complexity
        or args.high_risk
        or args.sort_by_risk
        or args.dependencies
        or args.dependents
        or args.sort_by_dependencies
        or args.failure_rates
        or args.frequently_failing
        or args.sort_by_failures
    ):
        # Collect tests
        if args.category == "all":
            tests = collect_tests(use_cache=use_cache)
        else:
            tests = collect_tests_by_category(args.category, use_cache=use_cache)

        # Apply filters
        tests = apply_filters(tests, args)

        # Handle failure history analysis
        if args.failure_rates or args.frequently_failing or args.sort_by_failures:
            # Get failure rates
            failure_rates = get_test_failure_rates(use_cache)

            if args.frequently_failing:
                # Get frequently failing tests
                frequently_failing = get_frequently_failing_tests(
                    threshold=args.failure_threshold,
                    min_runs=args.min_runs,
                    use_cache=use_cache,
                )

                print(
                    f"Frequently failing tests (failure rate >= {args.failure_threshold * 100:.1f}%, min runs: {args.min_runs}):"
                )

                # Apply limit if specified
                if args.limit > 0:
                    frequently_failing = frequently_failing[: args.limit]

                for test in frequently_failing:
                    print(
                        f"  {test['path']} (failure rate: {test['failure_rate'] * 100:.1f}%, {test['failures']}/{test['total_runs']} runs)"
                    )

                print(f"\nTotal: {len(frequently_failing)} frequently failing tests")

            elif args.failure_rates:
                # Show failure rates for all tests
                # Filter tests with at least min_runs
                history = load_failure_history()
                tests_with_runs = [
                    test
                    for test in tests
                    if test in history["tests"]
                    and history["tests"][test]["total_runs"] >= args.min_runs
                ]

                # Sort by failure rate if requested
                if args.sort_by_failures:
                    tests_with_runs.sort(
                        key=lambda x: failure_rates.get(x, 0), reverse=True
                    )

                # Apply limit if specified
                if args.limit > 0:
                    tests_with_runs = tests_with_runs[: args.limit]

                print(f"Test failure rates (min runs: {args.min_runs}):")
                for test_path in tests_with_runs:
                    test_history = history["tests"][test_path]
                    failure_rate = failure_rates.get(test_path, 0)
                    print(
                        f"  {test_path} (failure rate: {failure_rate * 100:.1f}%, {test_history['failures']}/{test_history['total_runs']} runs)"
                    )

                print(f"\nTotal: {len(tests_with_runs)} tests")

            # If only sorting by failures without showing them
            elif args.sort_by_failures:
                # Filter tests with at least min_runs
                history = load_failure_history()
                tests_with_runs = [
                    test
                    for test in tests
                    if test in history["tests"]
                    and history["tests"][test]["total_runs"] >= args.min_runs
                ]

                # Sort tests by failure rate
                tests_with_runs.sort(
                    key=lambda x: failure_rates.get(x, 0), reverse=True
                )

                # Apply limit if specified
                if args.limit > 0:
                    tests_with_runs = tests_with_runs[: args.limit]

                print("Tests sorted by failure rate:")
                for test_path in tests_with_runs:
                    test_history = history["tests"].get(
                        test_path, {"total_runs": 0, "failures": 0}
                    )
                    failure_rate = failure_rates.get(test_path, 0)
                    print(
                        f"  {test_path} (failure rate: {failure_rate * 100:.1f}%, {test_history['failures']}/{test_history['total_runs']} runs)"
                    )

                print(f"\nTotal: {len(tests_with_runs)} tests")

        # Handle dependency analysis
        elif (
            args.dependencies
            or args.dependents
            or args.sort_by_dependencies
            or args.min_dependents > 0
        ):
            # Analyze dependencies
            dependencies = analyze_test_dependencies(tests, use_cache)

            if isinstance(dependencies, dict) and "error" in dependencies:
                print(f"Error analyzing dependencies: {dependencies['error']}")
            else:
                # Count dependents for each test
                dependent_counts = {}
                for test_path in tests:
                    dependent_counts[test_path] = len(dependencies.get(test_path, []))

                if args.dependents:
                    # Show tests that depend on the specified test
                    if args.dependents in dependencies:
                        dependents = dependencies[args.dependents]
                        print(f"Tests that depend on {args.dependents}:")
                        for dependent in dependents:
                            print(f"  {dependent}")
                        print(f"\nTotal: {len(dependents)} dependent tests")
                    else:
                        print(f"No dependencies found for {args.dependents}")

                elif args.dependencies:
                    # Show all dependencies
                    print("Test dependencies:")

                    # Sort by number of dependents if requested
                    if args.sort_by_dependencies:
                        sorted_tests = sorted(
                            tests,
                            key=lambda x: dependent_counts.get(x, 0),
                            reverse=True,
                        )
                    else:
                        sorted_tests = tests

                    # Filter by minimum number of dependents
                    if args.min_dependents > 0:
                        sorted_tests = [
                            t
                            for t in sorted_tests
                            if dependent_counts.get(t, 0) >= args.min_dependents
                        ]

                    # Apply limit if specified
                    if args.limit > 0:
                        sorted_tests = sorted_tests[: args.limit]

                    for test_path in sorted_tests:
                        dependents = dependencies.get(test_path, [])
                        print(f"  {test_path} ({len(dependents)} dependents)")
                        if len(dependents) > 0:
                            for dependent in dependents[
                                :5
                            ]:  # Show only first 5 dependents
                                print(f"    {dependent}")
                            if len(dependents) > 5:
                                print(f"    ... and {len(dependents) - 5} more")

                    print(f"\nTotal: {len(sorted_tests)} tests")

                # If only sorting by dependencies without showing them
                elif args.sort_by_dependencies:
                    # Sort tests by number of dependents
                    sorted_tests = sorted(
                        tests, key=lambda x: dependent_counts.get(x, 0), reverse=True
                    )

                    # Filter by minimum number of dependents
                    if args.min_dependents > 0:
                        sorted_tests = [
                            t
                            for t in sorted_tests
                            if dependent_counts.get(t, 0) >= args.min_dependents
                        ]

                    # Apply limit if specified
                    if args.limit > 0:
                        sorted_tests = sorted_tests[: args.limit]

                    print("Tests sorted by number of dependents:")
                    for test_path in sorted_tests:
                        print(
                            f"  {test_path} ({dependent_counts.get(test_path, 0)} dependents)"
                        )

                    print(f"\nTotal: {len(sorted_tests)} tests")

        # Handle high-risk tests
        elif args.high_risk:
            # Get high-risk tests
            high_risk_tests = get_high_risk_tests(tests, args.risk_threshold, use_cache)
            print(f"High-risk tests (risk score >= {args.risk_threshold}):")

            # Apply limit if specified
            if args.limit > 0:
                high_risk_tests = high_risk_tests[: args.limit]

            for test in high_risk_tests:
                risk_score = test["complexity"].get("risk_score", 0)
                print(f"  {test['path']} (risk score: {risk_score:.2f})")

                # Print additional metrics
                if args.complexity:
                    complexity = test["complexity"]
                    print(f"    Complexity: {complexity.get('complexity', 0):.2f}")
                    print(f"    Readability: {complexity.get('readability', 0):.2f}")
                    print(
                        f"    Maintainability: {complexity.get('maintainability', 0):.2f}"
                    )

            print(f"\nTotal: {len(high_risk_tests)} high-risk tests")

        # Handle complexity metrics
        elif args.complexity:
            # Get complexity metrics for all tests
            tests_with_complexity = get_tests_with_complexity(tests, use_cache)

            # Sort by risk score if requested
            if args.sort_by_risk:
                tests_with_complexity.sort(
                    key=lambda x: (
                        x["complexity"].get("risk_score", 0)
                        if "error" not in x["complexity"]
                        else 0
                    ),
                    reverse=True,
                )

            # Apply limit if specified
            if args.limit > 0:
                tests_with_complexity = tests_with_complexity[: args.limit]

            print("Tests with complexity metrics:")
            for test in tests_with_complexity:
                if "error" in test["complexity"]:
                    print(f"  {test['path']} (error: {test['complexity']['error']})")
                else:
                    risk_score = test["complexity"].get("risk_score", 0)
                    print(f"  {test['path']} (risk score: {risk_score:.2f})")
                    print(
                        f"    Complexity: {test['complexity'].get('complexity', 0):.2f}"
                    )
                    print(
                        f"    Readability: {test['complexity'].get('readability', 0):.2f}"
                    )
                    print(
                        f"    Maintainability: {test['complexity'].get('maintainability', 0):.2f}"
                    )

            print(f"\nTotal: {len(tests_with_complexity)} tests")

    elif (
        not args.count
        and not args.markers
        and not args.marker_counts
        and not args.list_marked_tests
        and not args.clear_cache
    ):
        if args.category == "all":
            tests = collect_tests(use_cache=use_cache)
        else:
            tests = collect_tests_by_category(args.category, use_cache=use_cache)

        # Apply filters
        tests = apply_filters(tests, args)

        # Sort by risk score if requested
        if args.sort_by_risk and HAS_CODE_ANALYSIS:
            tests_with_complexity = get_tests_with_complexity(tests, use_cache)
            tests_with_complexity.sort(
                key=lambda x: (
                    x["complexity"].get("risk_score", 0)
                    if "error" not in x["complexity"]
                    else 0
                ),
                reverse=True,
            )
            tests = [test["path"] for test in tests_with_complexity]

        # Apply limit if specified
        if args.limit > 0:
            tests = tests[: args.limit]

        # Print filter information if filters were applied
        filter_info = []
        if args.pattern:
            filter_info.append(f"pattern: '{args.pattern}'")
        if args.module:
            filter_info.append(f"module: '{args.module}'")
        if args.exclude_pattern:
            filter_info.append(f"exclude pattern: '{args.exclude_pattern}'")
        if args.exclude_module:
            filter_info.append(f"exclude module: '{args.exclude_module}'")

        if filter_info:
            print(f"Filters applied: {', '.join(filter_info)}")

        for test_path in tests:
            print(test_path)

        print(f"\nTotal: {len(tests)} tests")
