#!/usr/bin/env python
"""
High-Risk Test Runner

This script runs high-risk tests identified by the identify_high_risk_tests.py script.
It focuses test execution on tests that are more likely to fail, improving efficiency
and reducing the time needed to identify potential issues.

Usage:
    python scripts/run_high_risk_tests.py [options]

Options:
    --high-risk-file FILE   High-risk tests file (default: high_risk_tests.json)
    --output FILE           Output file for results (default: high_risk_test_results.json)
    --risk-threshold N      Minimum risk threshold for tests to run (default: 0.5)
    --max-tests N           Maximum number of tests to run (default: 50)
    --timeout SECONDS       Timeout for each test (default: 60)
    --parallel              Run tests in parallel
    --workers N             Number of worker processes to use (default: auto)
    --update-history        Update test execution history with results
    --history-file FILE     Test execution history file (default: test_execution_history.json)
    --html                  Generate HTML report
    --identify              Run identify_high_risk_tests.py first to generate high-risk tests
"""

import argparse
import json
import multiprocessing
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test utilities if available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from test_utils import get_cache_dir, setup_test_environment
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run high-risk tests identified by identify_high_risk_tests.py."
    )
    parser.add_argument(
        "--high-risk-file",
        default="high_risk_tests.json",
        help="High-risk tests file (default: high_risk_tests.json)",
    )
    parser.add_argument(
        "--output",
        default="high_risk_test_results.json",
        help="Output file for results (default: high_risk_test_results.json)",
    )
    parser.add_argument(
        "--risk-threshold",
        type=float,
        default=0.5,
        help="Minimum risk threshold for tests to run (default: 0.5)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=50,
        help="Maximum number of tests to run (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for each test in seconds (default: 60)",
    )
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of worker processes to use (default: auto)",
    )
    parser.add_argument(
        "--update-history",
        action="store_true",
        help="Update test execution history with results",
    )
    parser.add_argument(
        "--history-file",
        default="test_execution_history.json",
        help="Test execution history file (default: test_execution_history.json)",
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument(
        "--identify",
        action="store_true",
        help="Run identify_high_risk_tests.py first to generate high-risk tests",
    )
    parser.add_argument(
        "--identify-args",
        default="",
        help="Additional arguments to pass to identify_high_risk_tests.py",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def load_high_risk_tests(high_risk_file: str) -> list[dict[str, Any]]:
    """
    Load high-risk tests from a file.

    Args:
        high_risk_file: Path to the high-risk tests file

    Returns:
        List of high-risk tests with risk scores
    """
    if not os.path.exists(high_risk_file):
        print(f"Error: {high_risk_file} does not exist")
        return []

    try:
        with open(high_risk_file) as f:
            data = json.load(f)

        if "high_risk_tests" in data:
            return data["high_risk_tests"]
        else:
            return []
    except json.JSONDecodeError:
        print(f"Error: {high_risk_file} is not a valid JSON file")
        return []


def identify_high_risk_tests(identify_args: str, high_risk_file: str) -> bool:
    """
    Run identify_high_risk_tests.py to generate high-risk tests.

    Args:
        identify_args: Additional arguments to pass to identify_high_risk_tests.py
        high_risk_file: Path to the high-risk tests file

    Returns:
        True if successful, False otherwise
    """
    cmd = ["python", "scripts/identify_high_risk_tests.py", "--output", high_risk_file]

    # Add additional arguments if provided
    if identify_args:
        cmd.extend(identify_args.split())

    try:
        print("Running identify_high_risk_tests.py...")
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        print("Error running identify_high_risk_tests.py")
        return False


def filter_high_risk_tests(
    high_risk_tests: list[dict[str, Any]], risk_threshold: float, max_tests: int
) -> list[str]:
    """
    Filter high-risk tests based on risk threshold and maximum number of tests.

    Args:
        high_risk_tests: List of high-risk tests with risk scores
        risk_threshold: Minimum risk threshold for tests to run
        max_tests: Maximum number of tests to run

    Returns:
        List of test paths to run
    """
    # Filter tests by risk threshold
    filtered_tests = [
        test for test in high_risk_tests if test["total_risk"] >= risk_threshold
    ]

    # Sort by risk score (highest first)
    sorted_tests = sorted(filtered_tests, key=lambda x: x["total_risk"], reverse=True)

    # Limit to max_tests
    limited_tests = sorted_tests[:max_tests]

    # Extract test paths
    test_paths = [test["test_path"] for test in limited_tests]

    return test_paths


def run_test(test_path: str, timeout: int) -> dict[str, Any]:
    """
    Run a single test.

    Args:
        test_path: Path to the test
        timeout: Timeout in seconds

    Returns:
        Dictionary with test results
    """
    start_time = time.time()

    # Build the pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        "--maxfail=1",
        test_path,
        "-v",  # verbose mode
    ]

    # Run the test
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        # Determine test status
        if result.returncode == 0:
            status = "passed"
        else:
            status = "failed"

        # Calculate execution time
        execution_time = time.time() - start_time

        return {
            "test_path": test_path,
            "status": status,
            "execution_time": execution_time,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired:
        # Handle timeout
        return {
            "test_path": test_path,
            "status": "timeout",
            "execution_time": timeout,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout} seconds",
            "timeout": True,
        }
    except Exception as e:
        # Handle other exceptions
        return {
            "test_path": test_path,
            "status": "error",
            "execution_time": time.time() - start_time,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "timeout": False,
        }


def run_tests_sequential(
    test_paths: list[str], timeout: int, verbose: bool
) -> list[dict[str, Any]]:
    """
    Run tests sequentially.

    Args:
        test_paths: List of test paths to run
        timeout: Timeout for each test
        verbose: Whether to print verbose output

    Returns:
        List of test results
    """
    results = []

    for i, test_path in enumerate(test_paths):
        if verbose:
            print(f"Running test {i+1}/{len(test_paths)}: {test_path}")
        else:
            print(f"Running test {i+1}/{len(test_paths)}...", end="\r")

        result = run_test(test_path, timeout)
        results.append(result)

        if verbose:
            print(f"  Status: {result['status']}")
            print(f"  Time: {result['execution_time']:.2f}s")

    print()  # Add a newline after progress indicator

    return results


def run_tests_parallel(
    test_paths: list[str], timeout: int, num_workers: int, verbose: bool
) -> list[dict[str, Any]]:
    """
    Run tests in parallel.

    Args:
        test_paths: List of test paths to run
        timeout: Timeout for each test
        num_workers: Number of worker processes
        verbose: Whether to print verbose output

    Returns:
        List of test results
    """
    if num_workers <= 0:
        # Auto-detect number of workers
        num_workers = multiprocessing.cpu_count()

    print(f"Running {len(test_paths)} tests with {num_workers} workers")

    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tests
        future_to_test = {
            executor.submit(run_test, test_path, timeout): test_path
            for test_path in test_paths
        }

        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_test)):
            test_path = future_to_test[future]
            try:
                result = future.result()
                results.append(result)

                if verbose:
                    print(f"Completed test {i+1}/{len(test_paths)}: {test_path}")
                    print(f"  Status: {result['status']}")
                    print(f"  Time: {result['execution_time']:.2f}s")
                else:
                    print(f"Completed test {i+1}/{len(test_paths)}...", end="\r")
            except Exception as e:
                print(f"Error processing test {test_path}: {e}")
                results.append(
                    {
                        "test_path": test_path,
                        "status": "error",
                        "execution_time": 0,
                        "returncode": -1,
                        "stdout": "",
                        "stderr": str(e),
                        "timeout": False,
                    }
                )

    print()  # Add a newline after progress indicator

    return results


def aggregate_results(test_results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate test results.

    Args:
        test_results: List of test results

    Returns:
        Aggregated results
    """
    # Count results by status
    status_counts = {
        "passed": 0,
        "failed": 0,
        "timeout": 0,
        "error": 0,
    }

    total_execution_time = 0

    for result in test_results:
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        total_execution_time += result["execution_time"]

    # Calculate pass rate
    total_tests = len(test_results)
    pass_rate = status_counts["passed"] / total_tests * 100 if total_tests > 0 else 0

    # Build aggregated results
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "status_counts": status_counts,
        "pass_rate": pass_rate,
        "total_execution_time": total_execution_time,
        "average_execution_time": (
            total_execution_time / total_tests if total_tests > 0 else 0
        ),
        "test_results": test_results,
    }

    return aggregated


def save_results(results: dict[str, Any], output_file: str):
    """
    Save results to a file.

    Args:
        results: Test results
        output_file: Path to the output file
    """
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


def update_test_history(results: dict[str, Any], history_file: str):
    """
    Update test execution history with results.

    Args:
        results: Test results
        history_file: Path to the history file
    """
    # Check if identify_high_risk_tests.py is available
    if not os.path.exists("scripts/identify_high_risk_tests.py"):
        print("Error: scripts/identify_high_risk_tests.py not found")
        return

    # Load the history file
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {history_file} is not a valid JSON file")
            return
    else:
        # Create a new history file
        history = {
            "last_updated": datetime.now().isoformat(),
            "tests": {},
            "executions": [],
        }

    # Create a new execution record
    execution = {
        "timestamp": results["timestamp"],
        "passed": [],
        "failed": [],
        "skipped": [],
    }

    # Categorize test results
    for result in results["test_results"]:
        test_path = result["test_path"]
        status = result["status"]

        if status == "passed":
            execution["passed"].append(test_path)
        elif status in ["failed", "timeout", "error"]:
            execution["failed"].append(test_path)

    # Add the execution to the history
    history["executions"].append(execution)

    # Update test records
    for test in execution["passed"] + execution["failed"]:
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

    # Save the updated history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Test execution history updated in {history_file}")


def generate_html_report(results: dict[str, Any], output_file: str):
    """
    Generate an HTML report from the results.

    Args:
        results: Test results
        output_file: Path to the output file
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>High-Risk Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .metric {{ margin-bottom: 10px; }}
            .metric-name {{ font-weight: bold; }}
            .metric-value {{ float: right; }}
            .good {{ color: green; }}
            .warning {{ color: orange; }}
            .bad {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .timestamp {{ color: #666; font-size: 0.8em; margin-top: 30px; }}
            .test {{ margin-bottom: 20px; }}
            .test-header {{ cursor: pointer; padding: 10px; background-color: #f2f2f2; }}
            .test-content {{ display: none; padding: 10px; border: 1px solid #ddd; }}
            .show {{ display: block; }}
            .passed {{ background-color: #dff0d8; }}
            .failed {{ background-color: #f2dede; }}
            .timeout {{ background-color: #fcf8e3; }}
            .error {{ background-color: #f2dede; }}
        </style>
        <script>
            function toggleTest(testId) {{
                var content = document.getElementById('test-content-' + testId);
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    content.style.display = 'block';
                }}
            }}
        </script>
    </head>
    <body>
        <h1>High-Risk Test Results</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">
                <span class="metric-name">Total Tests:</span>
                <span class="metric-value">{results['total_tests']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Passed:</span>
                <span class="metric-value good">{results['status_counts']['passed']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Failed:</span>
                <span class="metric-value {'bad' if results['status_counts']['failed'] > 0 else 'good'}">{results['status_counts']['failed']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Timeout:</span>
                <span class="metric-value {'bad' if results['status_counts']['timeout'] > 0 else 'good'}">{results['status_counts']['timeout']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Error:</span>
                <span class="metric-value {'bad' if results['status_counts']['error'] > 0 else 'good'}">{results['status_counts']['error']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Pass Rate:</span>
                <span class="metric-value {'good' if results['pass_rate'] > 90 else 'warning' if results['pass_rate'] > 75 else 'bad'}">{results['pass_rate']:.2f}%</span>
            </div>
            <div class="metric">
                <span class="metric-name">Total Execution Time:</span>
                <span class="metric-value">{results['total_execution_time']:.2f}s</span>
            </div>
            <div class="metric">
                <span class="metric-name">Average Execution Time:</span>
                <span class="metric-value">{results['average_execution_time']:.2f}s</span>
            </div>
        </div>

        <h2>Test Results</h2>
    """

    # Add test results
    for i, result in enumerate(results["test_results"]):
        status_class = result["status"]
        html += f"""
        <div class="test">
            <div class="test-header {status_class}" onclick="toggleTest({i})">
                {result['test_path']} - {result['status'].upper()} ({result['execution_time']:.2f}s)
            </div>
            <div id="test-content-{i}" class="test-content">
                <h3>Details</h3>
                <p><strong>Return Code:</strong> {result['returncode']}</p>
                <p><strong>Execution Time:</strong> {result['execution_time']:.2f}s</p>
                <p><strong>Timeout:</strong> {'Yes' if result['timeout'] else 'No'}</p>

                <h3>Standard Output</h3>
                <pre>{result['stdout']}</pre>

                <h3>Standard Error</h3>
                <pre>{result['stderr']}</pre>
            </div>
        </div>
        """

    html += f"""
        <div class="timestamp">
            Generated on: {results['timestamp']}
        </div>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html)
    print(f"HTML report saved to {output_file}")


def print_summary(results: dict[str, Any], execution_time: float):
    """
    Print a summary of the results.

    Args:
        results: Test results
        execution_time: Total execution time
    """
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['status_counts']['passed']}")
    print(f"Failed: {results['status_counts']['failed']}")
    print(f"Timeout: {results['status_counts']['timeout']}")
    print(f"Error: {results['status_counts']['error']}")
    print(f"Pass Rate: {results['pass_rate']:.2f}%")
    print(f"Total Execution Time: {results['total_execution_time']:.2f}s")
    print(f"Average Execution Time: {results['average_execution_time']:.2f}s")
    print(f"Total Wall Clock Time: {execution_time:.2f}s")
    print("=" * 80)

    # Print failed tests
    failed_tests = [
        r
        for r in results["test_results"]
        if r["status"] in ["failed", "timeout", "error"]
    ]
    if failed_tests:
        print("\nFailed Tests:")
        for i, result in enumerate(
            failed_tests[:10]
        ):  # Show only the first 10 failures
            print(
                f"{i+1}. {result['test_path']} - {result['status'].upper()} ({result['execution_time']:.2f}s)"
            )

        if len(failed_tests) > 10:
            print(f"... and {len(failed_tests) - 10} more")

    print("\n" + "=" * 80)


def main():
    """Main function."""
    start_time = time.time()
    args = parse_args()

    # Set up the test environment
    setup_test_environment()

    # Run identify_high_risk_tests.py if requested
    if args.identify:
        if not identify_high_risk_tests(args.identify_args, args.high_risk_file):
            print("Error identifying high-risk tests")
            return

    # Load high-risk tests
    high_risk_tests = load_high_risk_tests(args.high_risk_file)

    if not high_risk_tests:
        print("No high-risk tests found")
        return

    # Filter high-risk tests
    test_paths = filter_high_risk_tests(
        high_risk_tests, args.risk_threshold, args.max_tests
    )

    if not test_paths:
        print("No tests to run after filtering")
        return

    print(f"Running {len(test_paths)} high-risk tests...")

    # Run tests
    if args.parallel:
        test_results = run_tests_parallel(
            test_paths, args.timeout, args.workers, args.verbose
        )
    else:
        test_results = run_tests_sequential(test_paths, args.timeout, args.verbose)

    # Aggregate results
    results = aggregate_results(test_results)

    # Save results
    save_results(results, args.output)

    # Update test history if requested
    if args.update_history:
        update_test_history(results, args.history_file)

    # Generate HTML report if requested
    if args.html:
        html_output = args.output.replace(".json", ".html")
        generate_html_report(results, html_output)

    # Calculate total execution time
    execution_time = time.time() - start_time

    # Print summary
    print_summary(results, execution_time)


if __name__ == "__main__":
    main()
