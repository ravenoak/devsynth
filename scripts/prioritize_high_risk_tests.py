#!/usr/bin/env python3
"""
Test Prioritization and Filtering Script

This script identifies and runs high-risk tests based on multiple factors:
1. Historical failure rates (tests that failed recently are more likely to fail again)
2. Code complexity (more complex tests are more likely to fail)
3. Recent changes (tests affected by recent code changes are more likely to fail)
4. Dependencies (tests that depend on components with high failure rates are more likely to fail)

Usage:
    python scripts/prioritize_high_risk_tests.py [options]

Options:
    --category CATEGORY   Test category to analyze (unit, integration, behavior, all)
    --module MODULE       Specific module to analyze (e.g., tests/unit/interface)
    --limit N             Maximum number of tests to run
    --min-risk SCORE      Minimum risk score (0-100) for tests to run
    --update-history      Update test history with new results
    --processes N         Number of processes to use for test execution
    --timeout SECONDS     Timeout for each test in seconds
    --report              Generate a detailed risk report
    --dry-run             Show tests that would be run without running them
    --verbose             Show detailed information
    --no-cache            Don't use cached test collection results
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        collect_tests,
        collect_tests_by_category,
        get_marker_counts,
        get_test_counts,
    )
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

# History file
HISTORY_DIR = Path(".test_history")
HISTORY_DIR.mkdir(exist_ok=True)

# Risk factors weights (must sum to 1.0)
WEIGHTS = {
    "failure_history": 0.4,
    "code_complexity": 0.2,
    "recent_changes": 0.3,
    "dependencies": 0.1,
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test prioritization and filtering script."
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to analyze (default: all)",
    )
    parser.add_argument(
        "--module", help="Specific module to analyze (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of tests to run (default: 100)",
    )
    parser.add_argument(
        "--min-risk",
        type=float,
        default=0.0,
        help="Minimum risk score (0-100) for tests to run (default: 0)",
    )
    parser.add_argument(
        "--update-history",
        action="store_true",
        help="Update test history with new results",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=0,
        help="Number of processes to use for test execution (default: auto)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for each test in seconds (default: 60)",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a detailed risk report"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show tests that would be run without running them",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached test collection results",
    )
    return parser.parse_args()


def collect_all_tests(
    category: str = "all", module: str = None, use_cache: bool = True
) -> list[str]:
    """
    Collect all tests.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to collect tests from
        use_cache: Whether to use cached test collection results

    Returns:
        List of test paths
    """
    print("Collecting tests...")

    # Determine which categories to collect
    categories = [category] if category != "all" else list(TEST_CATEGORIES.keys())

    # Collect all tests
    all_tests = []
    for cat in categories:
        if module:
            # If module is specified, collect tests from that module
            if os.path.exists(module):
                tests = collect_tests_by_category(cat, use_cache=use_cache)
                tests = [t for t in tests if t.startswith(module)]
                all_tests.extend(tests)
        else:
            # Otherwise, collect all tests for the category
            tests = collect_tests_by_category(cat, use_cache=use_cache)
            all_tests.extend(tests)

    print(f"Found {len(all_tests)} tests")
    return all_tests


def get_test_hash(test_path: str) -> str:
    """
    Generate a hash for a test path to use as a file name.

    Args:
        test_path: Path to the test

    Returns:
        Hash string for the test path
    """
    import hashlib

    # Generate a hash of the test path
    hash_obj = hashlib.md5(test_path.encode())
    hash_str = hash_obj.hexdigest()

    # Store a mapping of hash to test path for debugging
    hash_mapping_file = HISTORY_DIR / "hash_mapping.json"
    mapping = {}
    if hash_mapping_file.exists():
        try:
            with open(hash_mapping_file) as f:
                mapping = json.load(f)
        except (json.JSONDecodeError, OSError):
            mapping = {}

    mapping[hash_str] = test_path

    try:
        with open(hash_mapping_file, "w") as f:
            json.dump(mapping, f, indent=2)
    except OSError:
        pass

    return hash_str


def load_test_history(test_path: str) -> dict[str, Any]:
    """
    Load test execution history.

    Args:
        test_path: Path to the test

    Returns:
        Dictionary with test history
    """
    hash_str = get_test_hash(test_path)
    history_file = HISTORY_DIR / f"{hash_str}_history.json"
    if history_file.exists():
        try:
            with open(history_file) as f:
                history = json.load(f)
                # Add test_path to history if not present
                if "test_path" not in history:
                    history["test_path"] = test_path
                return history
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading history file for {test_path}: {e}")
            return {"executions": [], "test_path": test_path}
    return {"executions": [], "test_path": test_path}


def save_test_history(test_path: str, history: dict[str, Any]):
    """
    Save test execution history.

    Args:
        test_path: Path to the test
        history: Dictionary with test history
    """
    hash_str = get_test_hash(test_path)
    history_file = HISTORY_DIR / f"{hash_str}_history.json"

    # Ensure test_path is in the history
    history["test_path"] = test_path

    try:
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        print(f"Error saving history file for {test_path}: {e}")


def update_test_history(test_path: str, passed: bool, execution_time: float):
    """
    Update test execution history.

    Args:
        test_path: Path to the test
        passed: Whether the test passed
        execution_time: Test execution time in seconds
    """
    # Load existing history
    history = load_test_history(test_path)

    # Add new execution
    history["executions"].append(
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "passed": passed,
            "execution_time": execution_time,
        }
    )

    # Keep only the last 10 executions
    if len(history["executions"]) > 10:
        history["executions"] = history["executions"][-10:]

    # Update statistics
    pass_count = sum(1 for e in history["executions"] if e["passed"])
    history["pass_rate"] = (
        pass_count / len(history["executions"]) if history["executions"] else 0.0
    )
    history["average_time"] = (
        sum(e["execution_time"] for e in history["executions"])
        / len(history["executions"])
        if history["executions"]
        else 0.0
    )

    # Save updated history
    save_test_history(test_path, history)


def calculate_failure_risk(test_path: str) -> float:
    """
    Calculate risk based on failure history.

    Args:
        test_path: Path to the test

    Returns:
        Risk score (0-1)
    """
    history = load_test_history(test_path)

    # If no history, assume medium risk
    if not history["executions"]:
        return 0.5

    # Calculate failure rate with higher weight for recent failures
    executions = history["executions"]
    total_weight = 0
    weighted_failures = 0

    for i, execution in enumerate(executions):
        # More recent executions have higher weight
        weight = (i + 1) / sum(range(1, len(executions) + 1))
        total_weight += weight

        if not execution["passed"]:
            weighted_failures += weight

    failure_rate = weighted_failures / total_weight if total_weight > 0 else 0

    return failure_rate


def calculate_complexity_risk(test_path: str) -> float:
    """
    Calculate risk based on code complexity.

    Args:
        test_path: Path to the test

    Returns:
        Risk score (0-1)
    """
    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
    else:
        file_path = test_path

    # Check if the file exists
    if not os.path.exists(file_path):
        return 0.5

    try:
        # Count lines of code as a simple complexity metric
        with open(file_path) as f:
            lines = f.readlines()

        # Count non-empty, non-comment lines
        code_lines = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                code_lines += 1

        # Normalize complexity (assuming 500+ lines is high complexity)
        complexity = min(code_lines / 500, 1.0)

        return complexity
    except Exception as e:
        print(f"Error calculating complexity for {file_path}: {e}")
        return 0.5


def get_git_changes(days: int = 7) -> set[str]:
    """
    Get files changed in the last N days.

    Args:
        days: Number of days to look back

    Returns:
        Set of changed file paths
    """
    try:
        # Get files changed in the last N days
        cmd = [
            "git",
            "log",
            f"--since={days} days ago",
            "--name-only",
            "--pretty=format:",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse the output
        changed_files = set()
        for line in result.stdout.split("\n"):
            if line.strip():
                changed_files.add(line.strip())

        return changed_files
    except Exception as e:
        print(f"Error getting git changes: {e}")
        return set()


def calculate_change_risk(test_path: str, changed_files: set[str]) -> float:
    """
    Calculate risk based on recent changes.

    Args:
        test_path: Path to the test
        changed_files: Set of recently changed files

    Returns:
        Risk score (0-1)
    """
    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
    else:
        file_path = test_path

    # Check if the test file itself has changed
    if file_path in changed_files:
        return 1.0

    # Check if related files have changed
    # This is a simplified approach - a more sophisticated approach would analyze imports
    test_dir = os.path.dirname(file_path)
    related_changes = sum(1 for f in changed_files if f.startswith(test_dir))

    # Normalize (assuming 5+ related changes is high risk)
    change_risk = min(related_changes / 5, 1.0)

    return change_risk


def calculate_dependency_risk(test_path: str) -> float:
    """
    Calculate risk based on dependencies.

    Args:
        test_path: Path to the test

    Returns:
        Risk score (0-1)
    """
    # Extract file path from test path
    if "::" in test_path:
        file_path = test_path.split("::")[0]
    else:
        file_path = test_path

    # Check if the file exists
    if not os.path.exists(file_path):
        return 0.5

    try:
        # Analyze imports as a simple dependency metric
        with open(file_path) as f:
            content = f.read()

        # Count imports
        import_count = len(re.findall(r"import\s+\w+|from\s+\w+\s+import", content))

        # Normalize (assuming 20+ imports is high risk)
        dependency_risk = min(import_count / 20, 1.0)

        return dependency_risk
    except Exception as e:
        print(f"Error calculating dependency risk for {file_path}: {e}")
        return 0.5


def calculate_overall_risk(test_path: str, changed_files: set[str]) -> float:
    """
    Calculate overall risk score.

    Args:
        test_path: Path to the test
        changed_files: Set of recently changed files

    Returns:
        Risk score (0-100)
    """
    # Calculate individual risk factors
    failure_risk = calculate_failure_risk(test_path)
    complexity_risk = calculate_complexity_risk(test_path)
    change_risk = calculate_change_risk(test_path, changed_files)
    dependency_risk = calculate_dependency_risk(test_path)

    # Calculate weighted average
    overall_risk = (
        failure_risk * WEIGHTS["failure_history"]
        + complexity_risk * WEIGHTS["code_complexity"]
        + change_risk * WEIGHTS["recent_changes"]
        + dependency_risk * WEIGHTS["dependencies"]
    )

    # Convert to 0-100 scale
    return overall_risk * 100


def run_test(test_path: str, timeout: int = 60) -> dict[str, Any]:
    """
    Run a single test.

    Args:
        test_path: Path to the test
        timeout: Timeout in seconds

    Returns:
        Dictionary with test results
    """
    print(f"Running test: {test_path}")

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]

    # Run the test and measure execution time
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        execution_time = time.time() - start_time

        # Determine if the test passed
        passed = result.returncode == 0

        # Print result
        status = "PASSED" if passed else "FAILED"
        print(f"  {status} in {execution_time:.2f}s")

        return {
            "test_path": test_path,
            "passed": passed,
            "execution_time": execution_time,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"  TIMEOUT after {timeout}s")

        return {
            "test_path": test_path,
            "passed": False,
            "execution_time": execution_time,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
        }
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"  ERROR: {e}")

        return {
            "test_path": test_path,
            "passed": False,
            "execution_time": execution_time,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


def run_tests_parallel(
    tests: list[str], num_processes: int, timeout: int
) -> list[dict[str, Any]]:
    """
    Run tests in parallel.

    Args:
        tests: List of test paths
        num_processes: Number of processes to use
        timeout: Timeout for each test in seconds

    Returns:
        List of test results
    """
    if num_processes <= 0:
        # Auto-detect number of processes
        num_processes = os.cpu_count() or 1

    print(f"Running {len(tests)} tests with {num_processes} processes")

    results = []

    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tests
        future_to_test = {
            executor.submit(run_test, test, timeout): test for test in tests
        }

        # Process results as they complete
        for future in as_completed(future_to_test):
            test = future_to_test[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error running test {test}: {e}")
                results.append(
                    {
                        "test_path": test,
                        "passed": False,
                        "execution_time": 0,
                        "returncode": -1,
                        "stdout": "",
                        "stderr": str(e),
                    }
                )

    return results


def generate_risk_report(
    tests_with_risk: list[tuple[str, float]],
    results: list[dict[str, Any]] = None,
    output_file: str = "test_risk_report.json",
):
    """
    Generate a risk report.

    Args:
        tests_with_risk: List of (test_path, risk_score) tuples
        results: List of test results (optional)
        output_file: Path to the output file
    """
    print("Generating risk report...")

    # Create results lookup
    results_lookup = {}
    if results:
        for result in results:
            results_lookup[result["test_path"]] = result

    # Create the report
    report = {"timestamp": datetime.datetime.now().isoformat(), "tests": []}

    for test_path, risk_score in tests_with_risk:
        test_report = {
            "test_path": test_path,
            "risk_score": risk_score,
            "risk_factors": {
                "failure_history": calculate_failure_risk(test_path),
                "code_complexity": calculate_complexity_risk(test_path),
                "recent_changes": calculate_change_risk(test_path, get_git_changes()),
                "dependencies": calculate_dependency_risk(test_path),
            },
        }

        if test_path in results_lookup:
            test_report["result"] = {
                "passed": results_lookup[test_path]["passed"],
                "execution_time": results_lookup[test_path]["execution_time"],
            }

        report["tests"].append(test_report)

    # Calculate summary statistics
    report["summary"] = {
        "total_tests": len(tests_with_risk),
        "high_risk_tests": sum(1 for _, risk in tests_with_risk if risk >= 70),
        "medium_risk_tests": sum(1 for _, risk in tests_with_risk if 30 <= risk < 70),
        "low_risk_tests": sum(1 for _, risk in tests_with_risk if risk < 30),
    }

    if results:
        report["summary"]["passed_tests"] = sum(1 for r in results if r["passed"])
        report["summary"]["failed_tests"] = sum(1 for r in results if not r["passed"])
        report["summary"]["pass_rate"] = (
            report["summary"]["passed_tests"] / len(results) if results else 0
        )

    # Write the report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total tests: {report['summary']['total_tests']}")
    print(f"  High risk tests: {report['summary']['high_risk_tests']}")
    print(f"  Medium risk tests: {report['summary']['medium_risk_tests']}")
    print(f"  Low risk tests: {report['summary']['low_risk_tests']}")

    if results:
        print(f"  Passed tests: {report['summary']['passed_tests']}")
        print(f"  Failed tests: {report['summary']['failed_tests']}")
        print(f"  Pass rate: {report['summary']['pass_rate']:.2%}")


def main():
    """Main function."""
    args = parse_args()

    # Collect all tests
    all_tests = collect_all_tests(
        category=args.category, module=args.module, use_cache=not args.no_cache
    )

    # Get recently changed files
    changed_files = get_git_changes(days=7)

    # Calculate risk scores for all tests
    print("Calculating risk scores...")
    tests_with_risk = []
    for test in all_tests:
        risk_score = calculate_overall_risk(test, changed_files)
        tests_with_risk.append((test, risk_score))

    # Sort tests by risk score (descending)
    tests_with_risk.sort(key=lambda x: x[1], reverse=True)

    # Filter tests by minimum risk score
    if args.min_risk > 0:
        tests_with_risk = [
            (test, risk) for test, risk in tests_with_risk if risk >= args.min_risk
        ]

    # Limit the number of tests
    if args.limit > 0 and len(tests_with_risk) > args.limit:
        tests_with_risk = tests_with_risk[: args.limit]

    # Print tests with risk scores
    print("\nHigh-risk tests:")
    for i, (test, risk) in enumerate(tests_with_risk[:10]):
        print(f"{i+1}. {test} (Risk: {risk:.2f})")

    if len(tests_with_risk) > 10:
        print(f"... and {len(tests_with_risk) - 10} more tests")

    # Run tests if not in dry-run mode
    results = None
    if not args.dry_run:
        tests_to_run = [test for test, _ in tests_with_risk]
        results = run_tests_parallel(tests_to_run, args.processes, args.timeout)

        # Update test history if requested
        if args.update_history:
            print("Updating test history...")
            for result in results:
                update_test_history(
                    result["test_path"], result["passed"], result["execution_time"]
                )

    # Generate risk report if requested
    if args.report:
        generate_risk_report(tests_with_risk, results)

    # Print summary
    print("\nSummary:")
    print(f"  Total tests analyzed: {len(all_tests)}")
    print(f"  High-risk tests identified: {len(tests_with_risk)}")

    if results:
        passed_tests = sum(1 for r in results if r["passed"])
        failed_tests = sum(1 for r in results if not r["passed"])

        print(f"  Tests run: {len(results)}")
        print(f"  Tests passed: {passed_tests}")
        print(f"  Tests failed: {failed_tests}")
        print(f"  Pass rate: {passed_tests / len(results):.2%}")

    print("\nDone!")


if __name__ == "__main__":
    main()
