#!/usr/bin/env python
"""
High-Risk Test Identification System

This script analyzes test execution history to identify high-risk tests that are more likely
to fail. It uses various risk factors including:
- Historical failure rate
- Recent failures
- Test complexity
- Code churn in related files
- Test dependencies

Usage:
    python scripts/identify_high_risk_tests.py [options]

Options:
    --history-file FILE     Test execution history file (default: test_execution_history.json)
    --output FILE           Output file for high-risk tests (default: high_risk_tests.json)
    --risk-threshold N      Risk threshold for high-risk tests (default: 0.7)
    --max-tests N           Maximum number of high-risk tests to identify (default: 100)
    --consider-recent N     Number of recent executions to consider (default: 10)
    --git-history           Consider git history for risk calculation
    --complexity            Consider test complexity for risk calculation
    --dependencies          Consider test dependencies for risk calculation
"""

import argparse
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import enhanced test utilities if available
try:
    from . import test_utils_extended as test_utils_ext
    from .test_utils import get_cache_dir, setup_test_environment
except ImportError:
    try:
        from .test_utils import get_cache_dir, setup_test_environment

        test_utils_ext = None
    except ImportError:
        # Fallback implementation if test_utils.py is not available
        def setup_test_environment():
            """Set up the test environment."""
            os.environ["PYTHONPATH"] = os.getcwd()

        def get_cache_dir():
            """Get the cache directory."""
            cache_dir = Path(".test_history_cache")
            cache_dir.mkdir(exist_ok=True)
            return cache_dir

        test_utils_ext = None

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
    parser = argparse.ArgumentParser(
        description="Identify high-risk tests based on execution history."
    )
    parser.add_argument(
        "--history-file",
        default="test_execution_history.json",
        help="Test execution history file (default: test_execution_history.json)",
    )
    parser.add_argument(
        "--output",
        default="high_risk_tests.json",
        help="Output file for high-risk tests (default: high_risk_tests.json)",
    )
    parser.add_argument(
        "--risk-threshold",
        type=float,
        default=0.7,
        help="Risk threshold for high-risk tests (default: 0.7)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=100,
        help="Maximum number of high-risk tests to identify (default: 100)",
    )
    parser.add_argument(
        "--consider-recent",
        type=int,
        default=10,
        help="Number of recent executions to consider (default: 10)",
    )
    parser.add_argument(
        "--git-history",
        action="store_true",
        help="Consider git history for risk calculation",
    )
    parser.add_argument(
        "--complexity",
        action="store_true",
        help="Consider test complexity for risk calculation",
    )
    parser.add_argument(
        "--dependencies",
        action="store_true",
        help="Consider test dependencies for risk calculation",
    )
    parser.add_argument(
        "--update-history",
        action="store_true",
        help="Update test execution history with latest results",
    )
    parser.add_argument(
        "--results-file", help="Test results file to use for updating history"
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument(
        "--html-file",
        default="high_risk_tests.html",
        help="HTML report file (default: high_risk_tests.html)",
    )
    parser.add_argument(
        "--use-markers",
        action="store_true",
        help="Use test markers for complexity estimation",
    )
    parser.add_argument(
        "--cache", action="store_true", help="Use cached test collection results"
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear cache before running"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def load_test_history(history_file: str) -> dict[str, Any]:
    """
    Load test execution history from a file.

    Args:
        history_file: Path to the history file

    Returns:
        Test execution history
    """
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
            return history
        except json.JSONDecodeError:
            print(f"Error: {history_file} is not a valid JSON file")

    # Create a new history file if it doesn't exist
    history = {
        "last_updated": datetime.now().isoformat(),
        "tests": {},
        "executions": [],
    }
    return history


def update_test_history(history: dict[str, Any], results_file: str) -> dict[str, Any]:
    """
    Update test execution history with latest results.

    Args:
        history: Test execution history
        results_file: Path to the test results file

    Returns:
        Updated test execution history
    """
    if not os.path.exists(results_file):
        print(f"Error: {results_file} does not exist")
        return history

    try:
        with open(results_file) as f:
            results = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {results_file} is not a valid JSON file")
        return history

    # Create a new execution record
    execution = {
        "timestamp": results.get("timestamp", datetime.now().isoformat()),
        "passed": results.get("passed", []),
        "failed": results.get("failed", []),
        "skipped": results.get("skipped", []),
    }

    # Add the execution to the history
    history["executions"].append(execution)

    # Update test records
    for test in execution["passed"] + execution["failed"] + execution["skipped"]:
        if test not in history["tests"]:
            history["tests"][test] = {
                "total_executions": 0,
                "total_passed": 0,
                "total_failed": 0,
                "total_skipped": 0,
                "recent_results": [],
            }

        # Update test statistics
        history["tests"][test]["total_executions"] += 1

        if test in execution["passed"]:
            history["tests"][test]["total_passed"] += 1
            result = "passed"
        elif test in execution["failed"]:
            history["tests"][test]["total_failed"] += 1
            result = "failed"
        else:
            history["tests"][test]["total_skipped"] += 1
            result = "skipped"

        # Add to recent results
        history["tests"][test]["recent_results"].append(
            {
                "timestamp": execution["timestamp"],
                "result": result,
            }
        )

        # Keep only the most recent results
        history["tests"][test]["recent_results"] = history["tests"][test][
            "recent_results"
        ][-10:]

    # Update last updated timestamp
    history["last_updated"] = datetime.now().isoformat()

    return history


def save_test_history(history: dict[str, Any], history_file: str):
    """
    Save test execution history to a file.

    Args:
        history: Test execution history
        history_file: Path to the history file
    """
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Test execution history saved to {history_file}")


def calculate_failure_risk(test_record: dict[str, Any], consider_recent: int) -> float:
    """
    Calculate the failure risk for a test based on its execution history.

    Args:
        test_record: Test execution record
        consider_recent: Number of recent executions to consider

    Returns:
        Failure risk score (0.0 to 1.0)
    """
    # Calculate historical failure rate
    total_executions = test_record["total_executions"]
    if total_executions == 0:
        return 0.0

    historical_failure_rate = test_record["total_failed"] / total_executions

    # Calculate recent failure rate
    recent_results = test_record["recent_results"][-consider_recent:]
    recent_failures = sum(
        1 for result in recent_results if result["result"] == "failed"
    )
    recent_executions = len(recent_results)

    if recent_executions == 0:
        recent_failure_rate = 0.0
    else:
        recent_failure_rate = recent_failures / recent_executions

    # Weight recent failures more heavily
    failure_risk = (historical_failure_rate * 0.4) + (recent_failure_rate * 0.6)

    return failure_risk


def collect_all_tests(use_cache: bool = False) -> list[str]:
    """
    Collect all tests in the project.

    Args:
        use_cache: Whether to use cached test collection results

    Returns:
        List of test paths
    """
    # Use test_utils_extended if available
    if test_utils_ext is not None:
        print("Using test_utils_extended for test collection...")
        tests_by_category = test_utils_ext.collect_all_tests(use_cache)
        all_tests = []
        for category, tests in tests_by_category.items():
            all_tests.extend(tests)
        return all_tests

    # Fallback implementation
    print("Using fallback test collection method...")
    all_tests = []
    for category, test_dir in TEST_CATEGORIES.items():
        cmd = [
            "python",
            "-m",
            "pytest",
            test_dir,
            "--collect-only",
            "-q",
        ]
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if line.startswith(test_dir):
                    all_tests.append(line.strip())
        except Exception as e:
            print(f"Error collecting tests for {category}: {e}")

    return all_tests


def get_test_complexity(test_path: str, use_markers: bool = False) -> float:
    """
    Calculate the complexity of a test based on various factors.

    Args:
        test_path: Path to the test file
        use_markers: Whether to use test markers for complexity estimation

    Returns:
        Complexity score (0.0 to 1.0)
    """
    # Use test markers if requested and available
    if use_markers and test_utils_ext is not None:
        has_marker, marker_type = test_utils_ext.check_test_has_marker(test_path)
        if has_marker:
            if marker_type == "slow":
                return 0.8
            elif marker_type == "medium":
                return 0.5
            elif marker_type == "fast":
                return 0.2

    # Estimate complexity based on test category
    if test_path.startswith("tests/behavior"):
        return 0.7  # Behavior tests are complex
    elif test_path.startswith("tests/integration"):
        return 0.5  # Integration tests are moderately complex
    elif test_path.startswith("tests/performance"):
        return 0.8  # Performance tests are complex

    # Fallback to code analysis
    if not os.path.exists(test_path):
        return 0.3  # Default complexity for unit tests

    # Extract the test file path from the test path
    match = re.match(r"(.*?\.py)(?:::(.*))?", test_path)
    if not match:
        return 0.3

    test_file = match.group(1)

    try:
        # Count lines of code
        with open(test_file) as f:
            lines = f.readlines()

        code_lines = len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
        )

        # Count assertions
        assertion_count = sum(1 for line in lines if "assert" in line)

        # Count fixtures
        fixture_count = sum(1 for line in lines if "@pytest.fixture" in line)

        # Count parametrize decorators
        parametrize_count = sum(
            1 for line in lines if "@pytest.mark.parametrize" in line
        )

        # Calculate complexity score
        complexity = min(
            1.0,
            (code_lines / 500) * 0.4
            + (assertion_count / 20) * 0.3
            + (fixture_count / 5) * 0.2
            + (parametrize_count / 3) * 0.1,
        )

        return complexity
    except Exception:
        return 0.3


def get_git_churn(test_path: str) -> float:
    """
    Calculate the git churn for a test file.

    Args:
        test_path: Path to the test file

    Returns:
        Churn score (0.0 to 1.0)
    """
    # Extract the test file path from the test path
    match = re.match(r"(.*?\.py)(?:::(.*))?", test_path)
    if not match:
        return 0.0

    test_file = match.group(1)

    try:
        # Get the number of commits in the last 30 days
        cmd = ["git", "log", "--since=30.days", "--pretty=format:%H", "--", test_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Get the number of lines changed in the last 30 days
        cmd = [
            "git",
            "log",
            "--since=30.days",
            "--numstat",
            "--pretty=format:",
            "--",
            test_file,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        lines_changed = 0
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        lines_changed += int(parts[0]) + int(parts[1])
                    except ValueError:
                        pass

        # Calculate churn score
        churn = min(1.0, (commit_count / 10) * 0.5 + (lines_changed / 100) * 0.5)

        return churn
    except Exception:
        return 0.0


def get_test_dependencies(test_path: str) -> list[str]:
    """
    Identify dependencies for a test.

    Args:
        test_path: Path to the test file

    Returns:
        List of dependent test paths
    """
    # Extract the test file path from the test path
    match = re.match(r"(.*?\.py)(?:::(.*))?", test_path)
    if not match:
        return []

    test_file = match.group(1)
    test_name = match.group(2) if match.group(2) else ""

    try:
        # Run pytest with --collect-only to get dependencies
        cmd = [
            "python",
            "-m",
            "pytest",
            test_path,
            "--collect-only",
            "-v",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse the output to find dependencies
        dependencies = []
        for line in result.stdout.split("\n"):
            if "depends on" in line:
                match = re.search(r"depends on (.*?)$", line)
                if match:
                    dependency = match.group(1)
                    dependencies.append(dependency)

        return dependencies
    except Exception:
        return []


def calculate_dependency_risk(test_path: str, high_risk_tests: set[str]) -> float:
    """
    Calculate the risk based on dependencies.

    Args:
        test_path: Path to the test file
        high_risk_tests: Set of high-risk test paths

    Returns:
        Dependency risk score (0.0 to 1.0)
    """
    dependencies = get_test_dependencies(test_path)

    if not dependencies:
        return 0.0

    # Calculate the percentage of dependencies that are high-risk
    high_risk_dependencies = sum(1 for dep in dependencies if dep in high_risk_tests)
    dependency_risk = (
        high_risk_dependencies / len(dependencies) if dependencies else 0.0
    )

    return dependency_risk


def identify_high_risk_tests(
    history: dict[str, Any],
    risk_threshold: float,
    max_tests: int,
    consider_recent: int,
    use_git_history: bool,
    use_complexity: bool,
    use_dependencies: bool,
    verbose: bool,
) -> list[dict[str, Any]]:
    """
    Identify high-risk tests based on execution history and other factors.

    Args:
        history: Test execution history
        risk_threshold: Risk threshold for high-risk tests
        max_tests: Maximum number of high-risk tests to identify
        consider_recent: Number of recent executions to consider
        use_git_history: Whether to consider git history for risk calculation
        use_complexity: Whether to consider test complexity for risk calculation
        use_dependencies: Whether to consider test dependencies for risk calculation
        verbose: Whether to print verbose output

    Returns:
        List of high-risk tests with risk scores
    """
    # Calculate initial risk scores based on failure history
    risk_scores = {}
    for test_path, test_record in history["tests"].items():
        failure_risk = calculate_failure_risk(test_record, consider_recent)
        risk_scores[test_path] = {
            "test_path": test_path,
            "failure_risk": failure_risk,
            "complexity": 0.0,
            "git_churn": 0.0,
            "dependency_risk": 0.0,
            "total_risk": failure_risk,  # Initial risk is just the failure risk
        }

    # Sort tests by initial risk score
    sorted_tests = sorted(
        risk_scores.values(), key=lambda x: x["failure_risk"], reverse=True
    )

    # Get the top tests for further analysis
    top_tests = sorted_tests[: max_tests * 2]  # Analyze twice as many tests as we need
    high_risk_test_paths = {
        test["test_path"]
        for test in top_tests
        if test["failure_risk"] >= risk_threshold
    }

    # Calculate additional risk factors for top tests
    for test in top_tests:
        test_path = test["test_path"]

        if use_complexity:
            if verbose:
                print(f"Calculating complexity for {test_path}")
            test["complexity"] = get_test_complexity(test_path)

        if use_git_history:
            if verbose:
                print(f"Calculating git churn for {test_path}")
            test["git_churn"] = get_git_churn(test_path)

        if use_dependencies:
            if verbose:
                print(f"Calculating dependency risk for {test_path}")
            test["dependency_risk"] = calculate_dependency_risk(
                test_path, high_risk_test_paths
            )

        # Calculate total risk score with weights
        test["total_risk"] = (
            test["failure_risk"] * 0.6
            + test["complexity"] * 0.1
            + test["git_churn"] * 0.2
            + test["dependency_risk"] * 0.1
        )

    # Sort tests by total risk score
    sorted_tests = sorted(top_tests, key=lambda x: x["total_risk"], reverse=True)

    # Get the top high-risk tests
    high_risk_tests = [
        test for test in sorted_tests if test["total_risk"] >= risk_threshold
    ][:max_tests]

    return high_risk_tests


def save_high_risk_tests(high_risk_tests: list[dict[str, Any]], output_file: str):
    """
    Save high-risk tests to a file.

    Args:
        high_risk_tests: List of high-risk tests with risk scores
        output_file: Path to the output file
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "high_risk_tests": high_risk_tests,
    }

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"High-risk tests saved to {output_file}")


def generate_html_report(high_risk_tests: list[dict[str, Any]], html_file: str):
    """
    Generate an HTML report for high-risk tests.

    Args:
        high_risk_tests: List of high-risk tests with risk scores
        html_file: Path to the HTML file
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>High-Risk Test Analysis</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .risk-high {{ background-color: #ffcccc; }}
            .risk-medium {{ background-color: #ffffcc; }}
            .risk-low {{ background-color: #ccffcc; }}
            .timestamp {{ color: #666; font-size: 0.8em; margin-top: 30px; }}
            .risk-bar {{ width: 100px; height: 10px; background-color: #eee; display: inline-block; }}
            .risk-fill {{ height: 100%; background-color: #f44; }}
        </style>
    </head>
    <body>
        <h1>High-Risk Test Analysis</h1>

        <div class="summary">
            <h2>Summary</h2>
            <p>Identified {len(high_risk_tests)} high-risk tests.</p>
        </div>

        <h2>High-Risk Tests</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>Total Risk</th>
                <th>Failure Risk</th>
                <th>Complexity</th>
                <th>Git Churn</th>
                <th>Dependency Risk</th>
            </tr>
    """

    for test in high_risk_tests:
        risk_class = (
            "risk-high"
            if test["total_risk"] > 0.7
            else "risk-medium" if test["total_risk"] > 0.5 else "risk-low"
        )

        html += f"""
            <tr class="{risk_class}">
                <td>{test["test_path"]}</td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width: {test['total_risk']*100}%;"></div></div>
                    {test["total_risk"]:.2f}
                </td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width: {test['failure_risk']*100}%;"></div></div>
                    {test["failure_risk"]:.2f}
                </td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width: {test['complexity']*100}%;"></div></div>
                    {test["complexity"]:.2f}
                </td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width: {test['git_churn']*100}%;"></div></div>
                    {test["git_churn"]:.2f}
                </td>
                <td>
                    <div class="risk-bar"><div class="risk-fill" style="width: {test['dependency_risk']*100}%;"></div></div>
                    {test["dependency_risk"]:.2f}
                </td>
            </tr>
        """

    html += f"""
        </table>

        <div class="timestamp">
            Generated on: {datetime.now().isoformat()}
        </div>
    </body>
    </html>
    """

    with open(html_file, "w") as f:
        f.write(html)
    print(f"HTML report saved to {html_file}")


def print_high_risk_tests(high_risk_tests: list[dict[str, Any]]):
    """
    Print high-risk tests to the console.

    Args:
        high_risk_tests: List of high-risk tests with risk scores
    """
    print("\n" + "=" * 80)
    print("HIGH-RISK TESTS:")
    print("=" * 80)

    for i, test in enumerate(high_risk_tests):
        print(f"{i+1}. {test['test_path']}")
        print(f"   Total Risk: {test['total_risk']:.2f}")
        print(f"   Failure Risk: {test['failure_risk']:.2f}")

        if test["complexity"] > 0:
            print(f"   Complexity: {test['complexity']:.2f}")

        if test["git_churn"] > 0:
            print(f"   Git Churn: {test['git_churn']:.2f}")

        if test["dependency_risk"] > 0:
            print(f"   Dependency Risk: {test['dependency_risk']:.2f}")

        print()

    print(f"Total high-risk tests: {len(high_risk_tests)}")
    print("=" * 80)


def main():
    """Main function."""
    start_time = time.time()
    args = parse_args()

    # Set up the test environment
    setup_test_environment()

    # Load test execution history
    history = load_test_history(args.history_file)

    # Update history if requested
    if args.update_history and args.results_file:
        history = update_test_history(history, args.results_file)
        save_test_history(history, args.history_file)

    # Identify high-risk tests
    high_risk_tests = identify_high_risk_tests(
        history,
        args.risk_threshold,
        args.max_tests,
        args.consider_recent,
        args.git_history,
        args.complexity,
        args.dependencies,
        args.verbose,
    )

    # Save high-risk tests
    save_high_risk_tests(high_risk_tests, args.output)

    # Print high-risk tests
    print_high_risk_tests(high_risk_tests)

    # Calculate execution time
    execution_time = time.time() - start_time
    print(f"\nExecution time: {execution_time:.2f} seconds")


if __name__ == "__main__":
    main()
