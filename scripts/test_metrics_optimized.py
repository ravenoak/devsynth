#!/usr/bin/env python
"""
Optimized Test Metrics Reporting System

This script is an optimized version of test_metrics.py designed to handle large test suites.
It implements batch processing, timeout handling, and partial results reporting to avoid
timeouts when analyzing large test suites.

Usage:
    python scripts/test_metrics_optimized.py [options]

Options:
    --output FILENAME      Output file for the report (default: test_metrics_report.json)
    --run-tests            Run tests to identify failures (otherwise just counts tests)
    --html                 Generate an HTML report in addition to JSON
    --batch-size N         Number of tests per batch (default: 20)
    --max-batches N        Maximum number of batches to process (default: all)
    --timeout SECONDS      Timeout for each batch (default: 300)
    --category CAT         Only analyze tests in the specified category
    --speed SPEED          Only analyze tests with the specified speed marker
    --dashboard            Generate a test execution dashboard
"""

import argparse
import datetime
import json
import os
import re
import subprocess

# Import common test utilities if available
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
        cache_dir = Path(".test_metrics_cache")
        cache_dir.mkdir(exist_ok=True)
        return cache_dir


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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate optimized test metrics report for large test suites."
    )
    parser.add_argument(
        "-o",
        "--output",
        default="test_metrics_report.json",
        help="Output file for the report (default: test_metrics_report.json)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests to identify failures (otherwise just counts tests)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate an HTML report in addition to JSON",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of tests per batch (default: 20)",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=0,
        help="Maximum number of batches to process (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for each batch in seconds (default: 300)",
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Only analyze tests in the specified category",
    )
    parser.add_argument(
        "--speed",
        choices=SPEED_CATEGORIES + ["all", "unmarked"],
        default="all",
        help="Only analyze tests with the specified speed marker",
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Generate a test execution dashboard"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (always collect fresh data)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached data before running",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of worker processes to use (default: auto)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def clear_cache():
    """Clear all cached data."""
    cache_dir = get_cache_dir()
    if cache_dir.exists():
        for file in cache_dir.iterdir():
            file.unlink()
        print(f"Cleared cache directory: {cache_dir}")


def collect_tests(category: str, speed: str = "all") -> list[str]:
    """
    Collect tests to run based on category and speed.

    Args:
        category: Test category (unit, integration, behavior, etc.)
        speed: Test speed category (fast, medium, slow, all)

    Returns:
        List of test paths
    """
    # Determine the test directory
    test_dir = TEST_CATEGORIES.get(category, category)
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return []

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
    categories: list[str], speed: str = "all"
) -> dict[str, list[str]]:
    """
    Collect tests from multiple categories.

    Args:
        categories: List of test categories
        speed: Test speed category

    Returns:
        Dictionary mapping categories to lists of tests
    """
    all_tests = {}
    for category in categories:
        tests = collect_tests(category, speed)
        if tests:
            all_tests[category] = tests
    return all_tests


def create_test_batches(
    tests_by_category: dict[str, list[str]], batch_size: int
) -> list[tuple[str, list[str]]]:
    """
    Create batches of tests for processing.

    Args:
        tests_by_category: Dictionary mapping categories to lists of tests
        batch_size: Number of tests per batch

    Returns:
        List of (category, batch) tuples
    """
    batches = []
    for category, tests in tests_by_category.items():
        # Create batches for this category
        for i in range(0, len(tests), batch_size):
            batch = tests[i : i + batch_size]
            batches.append((category, batch))

    return batches


def run_test_batch(category: str, batch: list[str], timeout: int) -> dict[str, Any]:
    """
    Run a batch of tests.

    Args:
        category: Test category
        batch: List of tests to run
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

        return {
            "category": category,
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
    except subprocess.TimeoutExpired:
        # Handle timeout
        return {
            "category": category,
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
            "category": category,
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


def process_batches(
    batches: list[tuple[str, list[str]]],
    timeout: int,
    max_batches: int,
    parallel: bool,
    workers: int,
    verbose: bool,
) -> list[dict[str, Any]]:
    """
    Process test batches.

    Args:
        batches: List of (category, batch) tuples
        timeout: Timeout for each batch
        max_batches: Maximum number of batches to process
        parallel: Whether to run tests in parallel
        workers: Number of worker processes
        verbose: Whether to print verbose output

    Returns:
        List of batch results
    """
    # Limit the number of batches if specified
    if max_batches > 0:
        batches = batches[:max_batches]

    results = []

    if parallel:
        # Import ProcessPoolExecutor for parallel execution
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor, as_completed

        if workers <= 0:
            # Auto-detect number of workers
            workers = multiprocessing.cpu_count()

        print(f"Processing {len(batches)} batches with {workers} workers")

        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(run_test_batch, category, batch, timeout): (
                    i,
                    category,
                    batch,
                )
                for i, (category, batch) in enumerate(batches)
            }

            # Process results as they complete
            for future in as_completed(future_to_batch):
                i, category, batch = future_to_batch[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Print progress
                    if verbose:
                        print(f"Batch {i+1}/{len(batches)} completed:")
                        print(f"  Category: {category}")
                        print(f"  Passed: {len(result['passed'])}")
                        print(f"  Failed: {len(result['failed'])}")
                        print(f"  Skipped: {len(result['skipped'])}")
                        print(f"  Time: {result['execution_time']:.2f}s")
                    else:
                        status = "✓" if not result["failed"] else "✗"
                        print(
                            f"Batch {i+1}/{len(batches)} {status} - "
                            f"P: {len(result['passed'])}, "
                            f"F: {len(result['failed'])}, "
                            f"S: {len(result['skipped'])}, "
                            f"T: {result['execution_time']:.2f}s"
                        )
                except Exception as e:
                    print(f"Error processing batch {i}: {e}")
                    results.append(
                        {
                            "category": category,
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
    else:
        # Process batches sequentially
        for i, (category, batch) in enumerate(batches):
            if verbose:
                print(f"Processing batch {i+1}/{len(batches)}:")
                print(f"  Category: {category}")
                print(f"  Tests: {len(batch)}")
            else:
                print(f"Processing batch {i+1}/{len(batches)}...", end="\r")

            result = run_test_batch(category, batch, timeout)
            results.append(result)

            if verbose:
                print(f"  Passed: {len(result['passed'])}")
                print(f"  Failed: {len(result['failed'])}")
                print(f"  Skipped: {len(result['skipped'])}")
                print(f"  Time: {result['execution_time']:.2f}s")
            else:
                status = "✓" if not result["failed"] else "✗"
                print(
                    f"Batch {i+1}/{len(batches)} {status} - "
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
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tests": 0,
        "passed": [],
        "failed": [],
        "skipped": [],
        "total_execution_time": 0,
        "batches": len(batch_results),
        "batch_results": batch_results,
        "categories": {},
    }

    # Aggregate results
    for result in batch_results:
        category = result["category"]

        # Initialize category if not already present
        if category not in aggregated["categories"]:
            aggregated["categories"][category] = {
                "total_tests": 0,
                "passed": [],
                "failed": [],
                "skipped": [],
                "execution_time": 0,
            }

        # Update category statistics
        aggregated["categories"][category]["total_tests"] += len(result["tests"])
        aggregated["categories"][category]["passed"].extend(result["passed"])
        aggregated["categories"][category]["failed"].extend(result["failed"])
        aggregated["categories"][category]["skipped"].extend(result["skipped"])
        aggregated["categories"][category]["execution_time"] += result["execution_time"]

        # Update overall statistics
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

    # Calculate category summary metrics
    for category, stats in aggregated["categories"].items():
        stats["pass_rate"] = (
            len(stats["passed"]) / stats["total_tests"] * 100
            if stats["total_tests"] > 0
            else 0
        )

    return aggregated


def save_results(results: dict[str, Any], output_file: str):
    """
    Save results to a file.

    Args:
        results: Results to save
        output_file: Output filename
    """
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


def generate_html_report(results: dict[str, Any], output_file: str):
    """
    Generate an HTML report from the results.

    Args:
        results: Test results
        output_file: Output filename
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Metrics Report</title>
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
            .category {{ margin-bottom: 20px; }}
            .category-header {{ cursor: pointer; padding: 10px; background-color: #f2f2f2; }}
            .category-content {{ display: none; padding: 10px; border: 1px solid #ddd; }}
            .show {{ display: block; }}
        </style>
        <script>
            function toggleCategory(categoryId) {{
                var content = document.getElementById('category-content-' + categoryId);
                if (content.style.display === 'block') {{
                    content.style.display = 'none';
                }} else {{
                    content.style.display = 'block';
                }}
            }}
        </script>
    </head>
    <body>
        <h1>Test Metrics Report</h1>

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

    # Add category sections
    html += """
        <h2>Categories</h2>
    """

    for i, (category, stats) in enumerate(results["categories"].items()):
        pass_rate_class = (
            "good"
            if stats["pass_rate"] > 90
            else "warning" if stats["pass_rate"] > 75 else "bad"
        )
        html += f"""
        <div class="category">
            <div class="category-header" onclick="toggleCategory({i})">
                {category} - {stats['total_tests']} tests, {len(stats['passed'])} passed, {len(stats['failed'])} failed, {stats['pass_rate']:.2f}%
            </div>
            <div id="category-content-{i}" class="category-content">
                <h3>Statistics</h3>
                <div class="metric">
                    <span class="metric-name">Total Tests:</span>
                    <span class="metric-value">{stats['total_tests']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Passed Tests:</span>
                    <span class="metric-value good">{len(stats['passed'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Failed Tests:</span>
                    <span class="metric-value {'bad' if stats['failed'] else 'good'}">{len(stats['failed'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Skipped Tests:</span>
                    <span class="metric-value">{len(stats['skipped'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Pass Rate:</span>
                    <span class="metric-value {pass_rate_class}">{stats['pass_rate']:.2f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Execution Time:</span>
                    <span class="metric-value">{stats['execution_time']:.2f}s</span>
                </div>
        """

        # Add failed tests if any
        if stats["failed"]:
            html += """
                <h3>Failed Tests</h3>
                <ul>
            """

            for test in stats["failed"][:20]:  # Show only the first 20 failures
                html += f"""
                    <li>{test}</li>
                """

            if len(stats["failed"]) > 20:
                html += f"""
                    <li>... and {len(stats["failed"]) - 20} more</li>
                """

            html += """
                </ul>
            """

        html += """
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
                <th>Category</th>
            </tr>
        """

        for test in results["failed"][:100]:  # Show only the first 100 failures
            # Find the category for this test
            category = None
            for cat, stats in results["categories"].items():
                if test in stats["failed"]:
                    category = cat
                    break

            html += f"""
            <tr>
                <td>{test}</td>
                <td>{category if category else 'Unknown'}</td>
            </tr>
            """

        if len(results["failed"]) > 100:
            html += f"""
            <tr>
                <td colspan="2">... and {len(results["failed"]) - 100} more</td>
            </tr>
            """

        html += "</table>"

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


def generate_dashboard(results: dict[str, Any], output_file: str):
    """
    Generate a test execution dashboard.

    Args:
        results: Test results
        output_file: Output filename
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Execution Dashboard</title>
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
            .dashboard {{ display: flex; flex-wrap: wrap; }}
            .dashboard-item {{ width: 45%; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .chart {{ width: 100%; height: 300px; }}
            .progress-bar {{ height: 20px; background-color: #f2f2f2; border-radius: 5px; margin-bottom: 10px; }}
            .progress {{ height: 100%; border-radius: 5px; }}
            .progress-passed {{ background-color: #5cb85c; }}
            .progress-failed {{ background-color: #d9534f; }}
            .progress-skipped {{ background-color: #f0ad4e; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Category Pass Rates Chart
                var ctxPassRates = document.getElementById('chart-pass-rates').getContext('2d');
                var passRatesChart = new Chart(ctxPassRates, {{
                    type: 'bar',
                    data: {{
                        labels: [{', '.join([f'"{cat}"' for cat in results["categories"].keys()])}],
                        datasets: [{{
                            label: 'Pass Rate (%)',
                            data: [{', '.join([f'{stats["pass_rate"]:.2f}' for stats in results["categories"].values()])}],
                            backgroundColor: [
                                {', '.join(['stats["pass_rate"] > 90 ? "rgba(92, 184, 92, 0.6)" : stats["pass_rate"] > 75 ? "rgba(240, 173, 78, 0.6)" : "rgba(217, 83, 79, 0.6)"' for stats in results["categories"].values()])}
                            ],
                            borderColor: [
                                {', '.join(['stats["pass_rate"] > 90 ? "rgba(92, 184, 92, 1)" : stats["pass_rate"] > 75 ? "rgba(240, 173, 78, 1)" : "rgba(217, 83, 79, 1)"' for stats in results["categories"].values()])}
                            ],
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});

                // Test Counts Chart
                var ctxTestCounts = document.getElementById('chart-test-counts').getContext('2d');
                var testCountsChart = new Chart(ctxTestCounts, {{
                    type: 'pie',
                    data: {{
                        labels: ['Passed', 'Failed', 'Skipped'],
                        datasets: [{{
                            label: 'Test Counts',
                            data: [{results['summary']['total_passed']}, {results['summary']['total_failed']}, {results['summary']['total_skipped']}],
                            backgroundColor: [
                                'rgba(92, 184, 92, 0.6)',
                                'rgba(217, 83, 79, 0.6)',
                                'rgba(240, 173, 78, 0.6)'
                            ],
                            borderColor: [
                                'rgba(92, 184, 92, 1)',
                                'rgba(217, 83, 79, 1)',
                                'rgba(240, 173, 78, 1)'
                            ],
                            borderWidth: 1
                        }}]
                    }}
                }});

                // Execution Time Chart
                var ctxExecutionTime = document.getElementById('chart-execution-time').getContext('2d');
                var executionTimeChart = new Chart(ctxExecutionTime, {{
                    type: 'bar',
                    data: {{
                        labels: [{', '.join([f'"{cat}"' for cat in results["categories"].keys()])}],
                        datasets: [{{
                            label: 'Execution Time (s)',
                            data: [{', '.join([f'{stats["execution_time"]:.2f}' for stats in results["categories"].values()])}],
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});

                // Test Distribution Chart
                var ctxTestDistribution = document.getElementById('chart-test-distribution').getContext('2d');
                var testDistributionChart = new Chart(ctxTestDistribution, {{
                    type: 'pie',
                    data: {{
                        labels: [{', '.join([f'"{cat}"' for cat in results["categories"].keys()])}],
                        datasets: [{{
                            label: 'Test Distribution',
                            data: [{', '.join([f'{stats["total_tests"]}' for stats in results["categories"].values()])}],
                            backgroundColor: [
                                'rgba(54, 162, 235, 0.6)',
                                'rgba(255, 99, 132, 0.6)',
                                'rgba(255, 206, 86, 0.6)',
                                'rgba(75, 192, 192, 0.6)',
                                'rgba(153, 102, 255, 0.6)'
                            ],
                            borderColor: [
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 99, 132, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }}]
                    }}
                }});
            }});
        </script>
    </head>
    <body>
        <h1>Test Execution Dashboard</h1>

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

            <div class="progress-bar">
                <div class="progress progress-passed" style="width: {results['summary']['total_passed'] / results['summary']['total_tests'] * 100 if results['summary']['total_tests'] > 0 else 0}%;"></div>
            </div>
            <div class="progress-bar">
                <div class="progress progress-failed" style="width: {results['summary']['total_failed'] / results['summary']['total_tests'] * 100 if results['summary']['total_tests'] > 0 else 0}%;"></div>
            </div>
            <div class="progress-bar">
                <div class="progress progress-skipped" style="width: {results['summary']['total_skipped'] / results['summary']['total_tests'] * 100 if results['summary']['total_tests'] > 0 else 0}%;"></div>
            </div>
        </div>

        <div class="dashboard">
            <div class="dashboard-item">
                <h3>Pass Rates by Category</h3>
                <canvas id="chart-pass-rates" class="chart"></canvas>
            </div>

            <div class="dashboard-item">
                <h3>Test Results</h3>
                <canvas id="chart-test-counts" class="chart"></canvas>
            </div>

            <div class="dashboard-item">
                <h3>Execution Time by Category</h3>
                <canvas id="chart-execution-time" class="chart"></canvas>
            </div>

            <div class="dashboard-item">
                <h3>Test Distribution by Category</h3>
                <canvas id="chart-test-distribution" class="chart"></canvas>
            </div>
        </div>

        <h2>Category Details</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Total Tests</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Pass Rate</th>
                <th>Execution Time</th>
            </tr>
    """

    for category, stats in results["categories"].items():
        pass_rate_class = (
            "good"
            if stats["pass_rate"] > 90
            else "warning" if stats["pass_rate"] > 75 else "bad"
        )
        html += f"""
            <tr>
                <td>{category}</td>
                <td>{stats['total_tests']}</td>
                <td class="good">{len(stats['passed'])}</td>
                <td class="{'bad' if stats['failed'] else 'good'}">{len(stats['failed'])}</td>
                <td>{len(stats['skipped'])}</td>
                <td class="{pass_rate_class}">{stats['pass_rate']:.2f}%</td>
                <td>{stats['execution_time']:.2f}s</td>
            </tr>
        """

    html += f"""
        </table>

        <div class="timestamp">
            Generated on: {results['timestamp']}
        </div>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html)
    print(f"Dashboard saved to {output_file}")


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
    print(f"Total Wall Clock Time: {execution_time:.2f}s")
    print(
        f"Speedup Factor: {results['summary']['total_execution_time'] / execution_time:.2f}x"
    )
    print("=" * 80)

    print("\nCategory Summary:")
    for category, stats in results["categories"].items():
        print(f"  {category}:")
        print(f"    Total Tests: {stats['total_tests']}")
        print(f"    Passed: {len(stats['passed'])}")
        print(f"    Failed: {len(stats['failed'])}")
        print(f"    Skipped: {len(stats['skipped'])}")
        print(f"    Pass Rate: {stats['pass_rate']:.2f}%")
        print(f"    Execution Time: {stats['execution_time']:.2f}s")

    print("\n" + "=" * 80)


def main():
    """Main function."""
    start_time = time.time()
    args = parse_args()

    # Set up the test environment
    setup_test_environment()

    # Clear cache if requested
    if args.clear_cache:
        clear_cache()

    # Determine test categories
    categories = (
        list(TEST_CATEGORIES.keys()) if args.category == "all" else [args.category]
    )

    # Collect tests
    print(f"Collecting tests for categories: {', '.join(categories)}")
    tests_by_category = collect_all_tests(categories, args.speed)

    # Create test batches
    batches = create_test_batches(tests_by_category, args.batch_size)

    if not batches:
        print("No tests found")
        return

    # Process batches
    if args.run_tests:
        print(f"Processing {len(batches)} batches...")
        batch_results = process_batches(
            batches,
            args.timeout,
            args.max_batches,
            args.parallel,
            args.workers,
            args.verbose,
        )
    else:
        print("Skipping test execution (use --run-tests to run tests)")
        batch_results = []
        for category, batch in batches:
            batch_results.append(
                {
                    "category": category,
                    "tests": batch,
                    "passed": [],
                    "failed": [],
                    "skipped": [],
                    "execution_time": 0,
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "timeout": False,
                }
            )

    # Aggregate results
    results = aggregate_results(batch_results)

    # Save results
    save_results(results, args.output)

    # Generate HTML report if requested
    if args.html:
        html_output = args.output.replace(".json", ".html")
        generate_html_report(results, html_output)

    # Generate dashboard if requested
    if args.dashboard:
        dashboard_output = args.output.replace(".json", "_dashboard.html")
        generate_dashboard(results, dashboard_output)

    # Calculate total execution time
    execution_time = time.time() - start_time

    # Print summary
    print_summary(results, execution_time)


if __name__ == "__main__":
    main()
