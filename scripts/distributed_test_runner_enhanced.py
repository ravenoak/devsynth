#!/usr/bin/env python
"""
Enhanced Distributed Test Runner

This script implements an improved distributed test execution system for running tests in parallel
across multiple processes. It addresses the performance issues with large test suites by
distributing the test load and aggregating results.

Enhancements over the original distributed_test_runner.py:
1. Integration with test_utils_extended.py for more accurate test collection
2. Better handling of behavior tests
3. Improved load balancing based on test complexity or historical execution time
4. Enhanced caching mechanisms
5. More sophisticated failure analysis
6. Integration with the test categorization system

Usage:
    python scripts/distributed_test_runner_enhanced.py [options]

Options:
    --workers N           Number of worker processes to use (default: auto)
    --test-dir DIR        Directory containing tests to run (default: tests)
    --category CAT        Test category to run (unit, integration, behavior, all)
    --speed SPEED         Test speed category (fast, medium, slow, all)
    --output FILE         Output file for results (default: distributed_test_results.json)
    --timeout SECONDS     Timeout for each test batch (default: 300)
    --batch-size N        Number of tests per batch (default: 20)
    --max-retries N       Maximum number of retries for failed batches (default: 2)
    --html                Generate HTML report
    --fail-fast           Stop on first failure
    --balance-load        Balance test load based on complexity
    --use-history         Use historical execution times for load balancing
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

# Import enhanced test utilities
try:
    from . import test_utils_extended as test_utils_ext
except ImportError:
    print("Warning: test_utils_extended.py not found. Using fallback implementation.")
    # Fallback implementation if test_utils_extended.py is not available
    test_utils_ext = None

# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}

# Speed categories
SPEED_CATEGORIES = ["fast", "medium", "slow"]

# Cache directory
CACHE_DIR = Path(".distributed_test_cache")
CACHE_DIR.mkdir(exist_ok=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests in a distributed manner across multiple processes."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of worker processes to use (default: auto)",
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests to run (default: tests)",
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to run (default: all)",
    )
    parser.add_argument(
        "--speed",
        choices=SPEED_CATEGORIES + ["all", "unmarked"],
        default="all",
        help="Test speed category (default: all)",
    )
    parser.add_argument(
        "--output",
        default="distributed_test_results.json",
        help="Output file for results (default: distributed_test_results.json)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for each test batch in seconds (default: 300)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of tests per batch (default: 20)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum number of retries for failed batches (default: 2)",
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear cache before running"
    )
    parser.add_argument("--no-cache", action="store_true", help="Don't use cache")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--balance-load",
        action="store_true",
        help="Balance test load based on complexity",
    )
    parser.add_argument(
        "--use-history",
        action="store_true",
        help="Use historical execution times for load balancing",
    )
    return parser.parse_args()


def collect_tests(
    category: str, speed: str = "all", use_cache: bool = True
) -> list[str]:
    """
    Collect tests to run based on category and speed.

    Args:
        category: Test category (unit, integration, behavior, etc.)
        speed: Test speed category (fast, medium, slow, all)
        use_cache: Whether to use cached test collection results

    Returns:
        List of test paths
    """
    # Determine the test directory
    test_dir = TEST_CATEGORIES.get(category, category)
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return []

    # Use test_utils_extended if available
    if test_utils_ext is not None:
        if category == "behavior":
            return test_utils_ext.collect_behavior_tests(test_dir, use_cache)
        else:
            return test_utils_ext.test_utils.collect_tests(test_dir, speed, use_cache)

    # Fallback implementation
    # Build the pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        test_dir,
        "--collect-only",
        "-q",  # quiet mode
    ]

    # Add speed marker if specified
    if speed != "all" and speed != "unmarked":
        cmd.extend(["-m", speed])
    elif speed == "unmarked":
        # Collect all tests, then filter out marked tests later
        pass

    # Run pytest to collect tests
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Parse the output to get the list of tests
        test_list = []
        for line in result.stdout.split("\n"):
            if line.startswith(test_dir):
                test_list.append(line.strip())

        # If we're looking for unmarked tests, we need to filter out marked tests
        if speed == "unmarked":
            # Collect all marked tests
            marked_tests = set()
            for marker in SPEED_CATEGORIES:
                marker_cmd = [
                    "python",
                    "-m",
                    "pytest",
                    test_dir,
                    "--collect-only",
                    "-q",  # quiet mode
                    "-m",
                    marker,
                ]
                marker_result = subprocess.run(
                    marker_cmd, check=False, capture_output=True, text=True
                )
                for line in marker_result.stdout.split("\n"):
                    if line.startswith(test_dir):
                        marked_tests.add(line.strip())

            # Filter out marked tests
            test_list = [test for test in test_list if test not in marked_tests]

        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def collect_all_tests(
    categories: list[str], speed: str = "all", use_cache: bool = True
) -> dict[str, list[str]]:
    """
    Collect tests from multiple categories.

    Args:
        categories: List of test categories
        speed: Test speed category
        use_cache: Whether to use cached test collection results

    Returns:
        Dictionary mapping categories to lists of tests
    """
    all_tests = {}
    for category in categories:
        tests = collect_tests(category, speed, use_cache)
        if tests:
            all_tests[category] = tests
    return all_tests


def get_test_complexity(test_path: str, use_history: bool = False) -> float:
    """
    Estimate the complexity of a test based on various factors.

    Args:
        test_path: Path to the test
        use_history: Whether to use historical execution times

    Returns:
        Complexity score (higher means more complex)
    """
    # Check if we have historical execution time
    if use_history:
        history_file = (
            CACHE_DIR / f"{test_path.replace('/', '_').replace(':', '_')}_history.json"
        )
        if history_file.exists():
            try:
                with open(history_file) as f:
                    history = json.load(f)
                return history.get("average_time", 1.0)
            except (json.JSONDecodeError, KeyError):
                pass

    # Estimate complexity based on test category and other factors
    complexity = 1.0

    # Behavior tests are typically more complex
    if test_path.startswith("tests/behavior"):
        complexity *= 2.0

    # Integration tests are more complex than unit tests
    elif test_path.startswith("tests/integration"):
        complexity *= 1.5

    # Check for speed markers in the test file
    if test_utils_ext is not None:
        has_marker, marker_type = test_utils_ext.check_test_has_marker(test_path)
        if has_marker:
            if marker_type == "slow":
                complexity *= 3.0
            elif marker_type == "medium":
                complexity *= 1.5
            # fast tests keep default complexity

    return complexity


def create_balanced_batches(
    tests_by_category: dict[str, list[str]], batch_size: int, use_history: bool = False
) -> list[list[str]]:
    """
    Create balanced batches of tests for distributed execution.

    Args:
        tests_by_category: Dictionary mapping categories to lists of tests
        batch_size: Target number of tests per batch
        use_history: Whether to use historical execution times for balancing

    Returns:
        List of test batches
    """
    # Flatten the tests list
    all_tests = []
    for category, tests in tests_by_category.items():
        all_tests.extend(tests)

    # Calculate complexity for each test
    test_complexities = [
        (test, get_test_complexity(test, use_history)) for test in all_tests
    ]

    # Sort tests by complexity (descending)
    test_complexities.sort(key=lambda x: x[1], reverse=True)

    # Create balanced batches using a greedy algorithm
    batches = []
    batch_complexities = []

    for test, complexity in test_complexities:
        # Find the batch with the lowest total complexity
        if not batches:
            batches.append([test])
            batch_complexities.append(complexity)
        else:
            # If any batch is below the target size, add to the least complex one
            below_target = [
                i for i, batch in enumerate(batches) if len(batch) < batch_size
            ]
            if below_target:
                min_complexity_idx = min(
                    below_target, key=lambda i: batch_complexities[i]
                )
                batches[min_complexity_idx].append(test)
                batch_complexities[min_complexity_idx] += complexity
            else:
                # All batches are at or above target size, create a new batch
                batches.append([test])
                batch_complexities.append(complexity)

    return batches


def run_test_batch(batch: list[str], timeout: int, batch_id: int) -> dict[str, Any]:
    """
    Run a batch of tests.

    Args:
        batch: List of tests to run
        timeout: Timeout in seconds
        batch_id: Batch identifier

    Returns:
        Dictionary with test results
    """
    start_time = time.time()

    # Build the pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        *batch,
        "-v",  # verbose mode
    ]

    # Run the tests
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        # Parse the output to get test results
        passed = []
        failed = []
        skipped = []

        for line in result.stdout.split("\n"):
            if "PASSED" in line:
                match = line.split(" ")[0]
                if match:
                    passed.append(match)
            elif "FAILED" in line:
                match = line.split(" ")[0]
                if match:
                    failed.append(match)
            elif "SKIPPED" in line:
                match = line.split(" ")[0]
                if match:
                    skipped.append(match)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Update test history
        for test in batch:
            update_test_history(test, test in passed, execution_time / len(batch))

        return {
            "batch_id": batch_id,
            "tests": batch,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "execution_time": execution_time,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired as e:
        # Handle timeout
        return {
            "batch_id": batch_id,
            "tests": batch,
            "passed": [],
            "failed": batch,  # Consider all tests as failed
            "skipped": [],
            "execution_time": timeout,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout} seconds",
            "timeout": True,
        }
    except Exception as e:
        # Handle other exceptions
        return {
            "batch_id": batch_id,
            "tests": batch,
            "passed": [],
            "failed": batch,  # Consider all tests as failed
            "skipped": [],
            "execution_time": time.time() - start_time,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "timeout": False,
        }


def update_test_history(test_path: str, passed: bool, execution_time: float):
    """
    Update the execution history for a test.

    Args:
        test_path: Path to the test
        passed: Whether the test passed
        execution_time: Execution time in seconds
    """
    history_file = (
        CACHE_DIR / f"{test_path.replace('/', '_').replace(':', '_')}_history.json"
    )

    # Load existing history or create new
    if history_file.exists():
        try:
            with open(history_file) as f:
                history = json.load(f)
        except (json.JSONDecodeError, KeyError):
            history = {"executions": [], "pass_rate": 0.0, "average_time": 0.0}
    else:
        history = {"executions": [], "pass_rate": 0.0, "average_time": 0.0}

    # Add new execution
    history["executions"].append(
        {
            "timestamp": datetime.now().isoformat(),
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
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def run_distributed_tests(
    batches: list[list[str]],
    num_workers: int,
    timeout: int,
    max_retries: int,
    fail_fast: bool,
    verbose: bool,
) -> list[dict[str, Any]]:
    """
    Run tests in a distributed manner across multiple processes.

    Args:
        batches: List of test batches
        num_workers: Number of worker processes
        timeout: Timeout for each batch
        max_retries: Maximum number of retries for failed batches
        fail_fast: Whether to stop on first failure
        verbose: Whether to print verbose output

    Returns:
        List of batch results
    """
    if num_workers <= 0:
        # Auto-detect number of workers
        num_workers = multiprocessing.cpu_count()

    print(f"Running {len(batches)} test batches with {num_workers} workers")

    # Set up the process pool
    results = []
    failed_batches = []
    retry_counts = {}

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all batches
        future_to_batch = {
            executor.submit(run_test_batch, batch, timeout, i): (i, batch)
            for i, batch in enumerate(batches)
        }

        # Process results as they complete
        for future in as_completed(future_to_batch):
            batch_id, batch = future_to_batch[future]
            try:
                result = future.result()
                results.append(result)

                # Print progress
                if verbose:
                    print(f"Batch {batch_id+1}/{len(batches)} completed:")
                    print(f"  Passed: {len(result['passed'])}")
                    print(f"  Failed: {len(result['failed'])}")
                    print(f"  Skipped: {len(result['skipped'])}")
                    print(f"  Time: {result['execution_time']:.2f}s")
                else:
                    status = "✓" if not result["failed"] else "✗"
                    print(
                        f"Batch {batch_id+1}/{len(batches)} {status} - "
                        f"P: {len(result['passed'])}, "
                        f"F: {len(result['failed'])}, "
                        f"S: {len(result['skipped'])}, "
                        f"T: {result['execution_time']:.2f}s"
                    )

                # Check if we need to retry this batch
                if result["failed"] and retry_counts.get(batch_id, 0) < max_retries:
                    failed_batches.append((batch_id, batch))

                # Stop on first failure if requested
                if fail_fast and result["failed"]:
                    print("Stopping on first failure")
                    executor.shutdown(wait=False)
                    break
            except Exception as e:
                print(f"Error processing batch {batch_id}: {e}")
                results.append(
                    {
                        "batch_id": batch_id,
                        "tests": batch,
                        "passed": [],
                        "failed": batch,  # Consider all tests as failed
                        "skipped": [],
                        "execution_time": 0,
                        "returncode": -1,
                        "stdout": "",
                        "stderr": str(e),
                        "timeout": False,
                    }
                )

    # Retry failed batches
    if failed_batches and not fail_fast:
        print(f"Retrying {len(failed_batches)} failed batches")

        for batch_id, batch in failed_batches:
            retry_count = retry_counts.get(batch_id, 0) + 1
            retry_counts[batch_id] = retry_count

            print(f"Retry {retry_count}/{max_retries} for batch {batch_id+1}")

            # Run the batch directly (not in a separate process)
            result = run_test_batch(batch, timeout, batch_id)

            # Update the result in the results list
            for i, r in enumerate(results):
                if r["batch_id"] == batch_id:
                    results[i] = result
                    break

            # Print progress
            if verbose:
                print(f"Batch {batch_id+1} retry completed:")
                print(f"  Passed: {len(result['passed'])}")
                print(f"  Failed: {len(result['failed'])}")
                print(f"  Skipped: {len(result['skipped'])}")
                print(f"  Time: {result['execution_time']:.2f}s")
            else:
                status = "✓" if not result["failed"] else "✗"
                print(
                    f"Batch {batch_id+1} retry {status} - "
                    f"P: {len(result['passed'])}, "
                    f"F: {len(result['failed'])}, "
                    f"S: {len(result['skipped'])}, "
                    f"T: {result['execution_time']:.2f}s"
                )

    return results


def aggregate_results(batch_results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate results from multiple batches.

    Args:
        batch_results: List of batch results

    Returns:
        Aggregated results
    """
    # Initialize aggregated results
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": 0,
        "passed": [],
        "failed": [],
        "skipped": [],
        "total_execution_time": 0,
        "batches": len(batch_results),
        "batch_results": batch_results,
    }

    # Aggregate results
    for result in batch_results:
        aggregated["total_tests"] += len(result["tests"])
        aggregated["passed"].extend(result["passed"])
        aggregated["failed"].extend(result["failed"])
        aggregated["skipped"].extend(result["skipped"])
        aggregated["total_execution_time"] += result["execution_time"]

    # Calculate summary metrics
    aggregated["summary"] = {
        "total_tests": aggregated["total_tests"],
        "total_passed": len(aggregated["passed"]),
        "total_failed": len(aggregated["failed"]),
        "total_skipped": len(aggregated["skipped"]),
        "pass_rate": (
            len(aggregated["passed"]) / aggregated["total_tests"] * 100
            if aggregated["total_tests"] > 0
            else 0
        ),
        "total_execution_time": aggregated["total_execution_time"],
        "average_execution_time": (
            aggregated["total_execution_time"] / len(batch_results)
            if batch_results
            else 0
        ),
    }

    return aggregated


def save_results(results: dict[str, Any], filename: str):
    """
    Save results to a file.

    Args:
        results: Results to save
        filename: Output filename
    """
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename}")


def generate_html_report(results: dict[str, Any], filename: str):
    """
    Generate an HTML report from the results.

    Args:
        results: Test results
        filename: Output filename
    """
    # Create a simple HTML report template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced Distributed Test Results</title>
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
            .batch {{ margin-bottom: 20px; }}
            .batch-header {{ cursor: pointer; padding: 10px; background-color: #f2f2f2; }}
            .batch-content {{ display: none; padding: 10px; border: 1px solid #ddd; }}
            .show {{ display: block; }}
        </style>
        <script>
            function toggleBatch(batchId) {{
                var content = document.getElementById('batch-content-' + batchId);
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    content.style.display = 'block';
                }}
            }}
        </script>
    </head>
    <body>
        <h1>Enhanced Distributed Test Results</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">
                <span class="metric-name">Total Tests:</span>
                <span class="metric-value">{results['summary']['total_tests']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Passed Tests:</span>
                <span class="metric-value good">{results['summary']['total_passed']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Failed Tests:</span>
                <span class="metric-value {'bad' if results['summary']['total_failed'] > 0 else 'good'}">{results['summary']['total_failed']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Skipped Tests:</span>
                <span class="metric-value">{results['summary']['total_skipped']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Pass Rate:</span>
                <span class="metric-value {'good' if results['summary']['pass_rate'] > 90 else 'warning' if results['summary']['pass_rate'] > 75 else 'bad'}">{results['summary']['pass_rate']:.2f}%</span>
            </div>
            <div class="metric">
                <span class="metric-name">Total Execution Time:</span>
                <span class="metric-value">{results['summary']['total_execution_time']:.2f}s</span>
            </div>
            <div class="metric">
                <span class="metric-name">Average Batch Time:</span>
                <span class="metric-value">{results['summary']['average_execution_time']:.2f}s</span>
            </div>
        </div>
    """

    # Add failed tests section if there are any
    if results["failed"]:
        html += """
        <h2>Failed Tests</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>Batch</th>
            </tr>
        """

        for test in results["failed"]:
            # Find the batch that contains this test
            batch_id = None
            for batch in results["batch_results"]:
                if test in batch["failed"]:
                    batch_id = batch["batch_id"]
                    break

            html += f"""
            <tr>
                <td>{test}</td>
                <td>{batch_id + 1 if batch_id is not None else 'Unknown'}</td>
            </tr>
            """

        html += "</table>"

    # Add batch details
    html += """
        <h2>Batch Details</h2>
    """

    for batch in results["batch_results"]:
        status = "✓" if not batch["failed"] else "✗"
        html += f"""
        <div class="batch">
            <div class="batch-header" onclick="toggleBatch({batch['batch_id']})">
                Batch {batch['batch_id'] + 1} {status} -
                Passed: {len(batch['passed'])},
                Failed: {len(batch['failed'])},
                Skipped: {len(batch['skipped'])},
                Time: {batch['execution_time']:.2f}s
                {' (Timeout)' if batch['timeout'] else ''}
            </div>
            <div id="batch-content-{batch['batch_id']}" class="batch-content">
                <h3>Tests</h3>
                <ul>
        """

        for test in batch["tests"]:
            if test in batch["passed"]:
                html += f'<li class="good">{test} - PASSED</li>'
            elif test in batch["failed"]:
                html += f'<li class="bad">{test} - FAILED</li>'
            elif test in batch["skipped"]:
                html += f"<li>{test} - SKIPPED</li>"
            else:
                html += f"<li>{test} - UNKNOWN</li>"

        html += """
                </ul>
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

    with open(filename, "w") as f:
        f.write(html)
    print(f"HTML report saved to {filename}")


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
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Passed Tests: {results['summary']['total_passed']}")
    print(f"Failed Tests: {results['summary']['total_failed']}")
    print(f"Skipped Tests: {results['summary']['total_skipped']}")
    print(f"Pass Rate: {results['summary']['pass_rate']:.2f}%")
    print(f"Total Execution Time: {results['summary']['total_execution_time']:.2f}s")
    print(f"Average Batch Time: {results['summary']['average_execution_time']:.2f}s")
    print(f"Total Wall Clock Time: {execution_time:.2f}s")
    print(
        f"Speedup Factor: {results['summary']['total_execution_time'] / execution_time:.2f}x"
    )
    print("=" * 80)

    if results["failed"]:
        print("\nFailed Tests:")
        for test in results["failed"][:10]:  # Show only the first 10 failures
            print(f"  {test}")

        if len(results["failed"]) > 10:
            print(f"  ... and {len(results['failed']) - 10} more")

    print("\n" + "=" * 80)


def clear_cache():
    """Clear the cache directory."""
    if CACHE_DIR.exists():
        for file in CACHE_DIR.iterdir():
            file.unlink()
        print(f"Cleared cache directory: {CACHE_DIR}")


def main():
    """Main function."""
    start_time = time.time()
    args = parse_args()

    # Clear cache if requested
    if args.clear_cache:
        clear_cache()

    # Determine test categories
    categories = (
        list(TEST_CATEGORIES.keys()) if args.category == "all" else [args.category]
    )

    # Collect tests
    print(f"Collecting tests for categories: {', '.join(categories)}")
    tests_by_category = collect_all_tests(categories, args.speed, not args.no_cache)

    # Create test batches
    if args.balance_load:
        print("Creating balanced test batches...")
        batches = create_balanced_batches(
            tests_by_category, args.batch_size, args.use_history
        )
    else:
        batches = []
        all_tests = []
        for category, tests in tests_by_category.items():
            all_tests.extend(tests)

        # Create batches
        for i in range(0, len(all_tests), args.batch_size):
            batch = all_tests[i : i + args.batch_size]
            batches.append(batch)

    if not batches:
        print("No tests found")
        return

    # Run tests
    batch_results = run_distributed_tests(
        batches,
        args.workers,
        args.timeout,
        args.max_retries,
        args.fail_fast,
        args.verbose,
    )

    # Aggregate results
    results = aggregate_results(batch_results)

    # Save results
    save_results(results, args.output)

    # Generate HTML report if requested
    if args.html:
        html_filename = args.output.replace(".json", ".html")
        generate_html_report(results, html_filename)

    # Calculate total execution time
    execution_time = time.time() - start_time

    # Print summary
    print_summary(results, execution_time)


if __name__ == "__main__":
    main()
