#!/usr/bin/env python
"""
Test Metrics Reporting System

This script generates a comprehensive report on the test suite status, including:
- Total test count by type (unit, integration, behavior, etc.)
- Test counts by speed category (fast, medium, slow)
- Failing test counts and details
- Test coverage metrics

Usage:
    python scripts/test_metrics.py [--output FILENAME] [--run-tests] [--html]

Options:
    --output FILENAME  Output file for the report (default: test_metrics_report.json)
    --run-tests        Run tests to identify failures (otherwise just counts tests)
    --html             Generate an HTML report in addition to JSON
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import psutil

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common_test_collector

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
COVERAGE_THRESHOLDS = {"fast": 8.0, "medium": 8.0}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate test metrics report.")
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
        "--skip-coverage",
        action="store_true",
        help="Skip coverage calculation (faster)",
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Only analyze tests in the specified category",
    )
    parser.add_argument(
        "--speed",
        choices=SPEED_CATEGORIES + ["all"],
        default="all",
        help="Only analyze tests with the specified speed marker",
    )
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel test execution"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (always collect fresh data)",
    )
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Run tests in smaller batches to improve performance",
    )
    parser.add_argument(
        "--segment-size",
        type=int,
        default=50,
        help="Number of tests per batch when using --segment (default: 50)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached data before running",
    )
    return parser.parse_args()


def count_tests_by_category(use_cache: bool = True) -> dict[str, int]:
    """
    Count tests by category (unit, integration, behavior, etc.).

    Args:
        use_cache: Whether to use cached results if available

    Returns:
        Dictionary mapping category names to test counts.
    """
    # Check for cached results
    cache_file = ".test_metrics_cache/category_counts.json"
    cache_timestamp_file = ".test_metrics_cache/category_counts_timestamp.txt"

    if (
        use_cache
        and os.path.exists(cache_file)
        and os.path.exists(cache_timestamp_file)
    ):
        try:
            # Check if cache is recent (less than 24 hours old)
            with open(cache_timestamp_file) as f:
                timestamp = float(f.read().strip())

            if time.time() - timestamp < 86400:  # 24 hours in seconds
                with open(cache_file) as f:
                    counts = json.load(f)
                    print(
                        "Using cached test counts by category (less than 24 hours old)"
                    )
                    return counts
            else:
                print(
                    "Cached test counts are more than 24 hours old, collecting fresh data..."
                )
        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            # Cache is invalid, continue with collection
            pass

    print("Collecting test counts by category using common_test_collector...")

    # Use common_test_collector to get test counts
    test_counts = common_test_collector.get_test_counts(use_cache=use_cache)

    # Convert to the expected format
    counts = {}
    for category in TEST_CATEGORIES:
        if category in test_counts:
            counts[category] = test_counts[category]
        else:
            counts[category] = 0

    # Add total count
    counts["total"] = test_counts["total"]

    # Cache the results
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(counts, f)

    # Save the timestamp
    with open(cache_timestamp_file, "w") as f:
        f.write(str(time.time()))

    return counts


def count_tests_by_speed(
    use_cache: bool = True, category_counts: dict[str, int] = None
) -> dict[str, int]:
    """
    Count tests by speed category (fast, medium, slow).

    Args:
        use_cache: Whether to use cached results if available
        category_counts: Pre-computed category counts to avoid recalculation

    Returns:
        Dictionary mapping speed categories to test counts.
    """
    # Check for cached results
    cache_file = ".test_metrics_cache/speed_counts.json"
    cache_timestamp_file = ".test_metrics_cache/speed_counts_timestamp.txt"

    if (
        use_cache
        and os.path.exists(cache_file)
        and os.path.exists(cache_timestamp_file)
    ):
        try:
            # Check if cache is recent (less than 24 hours old)
            with open(cache_timestamp_file) as f:
                timestamp = float(f.read().strip())

            if time.time() - timestamp < 86400:  # 24 hours in seconds
                with open(cache_file) as f:
                    counts = json.load(f)
                    print("Using cached test counts by speed (less than 24 hours old)")
                    return counts
            else:
                print(
                    "Cached test counts by speed are more than 24 hours old, collecting fresh data..."
                )
        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            # Cache is invalid, continue with collection
            pass

    print("Collecting test counts by speed category using common_test_collector...")

    # Use common_test_collector to get marker counts
    marker_counts = common_test_collector.get_marker_counts(use_cache=use_cache)

    # Extract counts for each speed category
    counts = {}
    for speed in SPEED_CATEGORIES:
        counts[speed] = marker_counts["total"][speed]

    # Calculate unmarked tests
    if category_counts is None:
        total_tests = count_tests_by_category(use_cache)["total"]
    else:
        total_tests = category_counts["total"]

    marked_tests = sum(counts.values())
    counts["unmarked"] = total_tests - marked_tests

    # Cache the results
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(counts, f)

    # Save the timestamp
    with open(cache_timestamp_file, "w") as f:
        f.write(str(time.time()))

    return counts


def _run_with_memory(cmd: list[str]) -> tuple[str, str, float]:
    """Run a command and track peak memory usage.

    Args:
        cmd: Command and arguments to execute.

    Returns:
        stdout: Captured standard output.
        stderr: Captured standard error.
        peak_mb: Peak resident set size in megabytes observed while the
            command was running (including child processes).
    """
    process = psutil.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    peak = 0
    try:
        while True:
            if process.poll() is not None:
                break
            rss = process.memory_info().rss
            for child in process.children(recursive=True):
                try:
                    rss += child.memory_info().rss
                except psutil.Error:
                    continue
            peak = max(peak, rss)
            time.sleep(0.1)
        stdout, stderr = process.communicate()
    finally:
        process.wait()
    peak_mb = peak / (1024 * 1024)
    return stdout, stderr, peak_mb


def identify_failing_tests(
    parallel: bool = True,
    segment: bool = True,
    segment_size: int = 50,
    use_cache: bool = True,
) -> tuple[dict[str, list[str]], dict[str, float]]:
    """
    Run tests to identify failing tests.

    Args:
        parallel (bool): Whether to run tests in parallel using pytest-xdist
        segment (bool): Whether to run tests in smaller batches
        segment_size (int): Number of tests per batch when using segmentation
        use_cache (bool): Whether to use cached results if available

    Returns:
        Dictionary mapping categories to lists of failing test names.
    """
    # Check for cached results
    cache_file = ".test_metrics_cache/failing_tests.json"
    cache_timestamp_file = ".test_metrics_cache/failing_tests_timestamp.txt"

    if (
        use_cache
        and os.path.exists(cache_file)
        and os.path.exists(cache_timestamp_file)
    ):
        try:
            # Check if cache is recent (less than 1 hour old)
            with open(cache_timestamp_file) as f:
                timestamp = float(f.read().strip())

            if time.time() - timestamp < 3600:  # 1 hour in seconds
                with open(cache_file) as f:
                    failing_tests = json.load(f)
                    print("Using cached failing tests (less than 1 hour old)")
                    return failing_tests
            else:
                print(
                    "Cached failing tests are more than 1 hour old, running tests again..."
                )
        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            # Cache is invalid, continue with test execution
            pass

    print("Identifying failing tests...")
    failing_tests: dict[str, list[str]] = {}
    memory_usage: dict[str, float] = {}

    for category, path in TEST_CATEGORIES.items():
        if not os.path.exists(path):
            failing_tests[category] = []
            continue

        print(f"  Running {category} tests...")

        if segment:
            # Use common_test_collector to collect tests for this category
            test_list = common_test_collector.collect_tests_by_category(
                category, use_cache=use_cache
            )

            if not test_list:
                print(f"    No tests found in {path}")
                failing_tests[category] = []
                continue

            print(
                f"    Found {len(test_list)} tests, running in batches of {segment_size}..."
            )

            try:
                # Run tests in batches
                failing: list[str] = []
                for i in range(0, len(test_list), segment_size):
                    batch = test_list[i : i + segment_size]
                    print(
                        f"    Running batch {i//segment_size + 1}/{(len(test_list) + segment_size - 1)//segment_size}..."
                    )

                    # Create command for this batch
                    cmd = [
                        "python",
                        "-m",
                        "pytest",
                        *batch,
                        "-v",  # verbose mode
                    ]

                    # Run tests in parallel using pytest-xdist if requested
                    if parallel:
                        cmd.extend(["-n", "auto"])
                    else:
                        cmd.extend(["-n", "1"])

                    # Run the batch with memory tracking
                    stdout, _, peak = _run_with_memory(cmd)

                    # Parse the output to get failing tests
                    for line in stdout.split("\n"):
                        if "FAILED" in line:
                            match = re.search(r"(test_\w+\.py::[\w:]+)", line)
                            if match:
                                failing.append(match.group(1))

                    key = (
                        batch[0]
                        if len(batch) == 1
                        else f"{category}_batch_{i//segment_size + 1}"
                    )
                    memory_usage[key] = peak

                failing_tests[category] = failing
            except Exception as e:
                print(f"    Error: {e}")
                failing_tests[category] = []
        else:
            # Run all tests at once
            cmd = [
                "python",
                "-m",
                "pytest",
                path,
                "-v",  # verbose mode
            ]

            # Run tests in parallel using pytest-xdist if requested
            if parallel:
                cmd.extend(["-n", "auto"])
            else:
                cmd.extend(["-n", "1"])

            try:
                stdout, _, peak = _run_with_memory(cmd)

                # Parse the output to get failing tests
                failing: list[str] = []
                for line in stdout.split("\n"):
                    if "FAILED" in line:
                        match = re.search(r"(test_\w+\.py::[\w:]+)", line)
                        if match:
                            failing.append(match.group(1))

                failing_tests[category] = failing
                memory_usage[category] = peak
            except Exception as e:
                print(f"    Error running tests in {path}: {e}")
                failing_tests[category] = []

    # Cache the results
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(failing_tests, f)

    # Save the timestamp
    with open(cache_timestamp_file, "w") as f:
        f.write(str(time.time()))

    return failing_tests, memory_usage


def calculate_coverage(speed: str | None = None) -> dict[str, float]:
    """Calculate test coverage metrics for an optional speed selection."""
    coverage = {
        "line_coverage": 0.0,
        "branch_coverage": 0.0,
        "uncovered_modules": [],
    }

    cmd = [
        "python",
        "-m",
        "pytest",
        "--cov=src/devsynth",
        "--cov-report=term-missing",
    ]
    marker_expr = "not memory_intensive"
    if speed:
        marker_expr = f"{speed} and not memory_intensive"
    cmd.extend(["-m", marker_expr])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    coverage["line_coverage"] = float(parts[-1].strip("%"))
                if len(parts) >= 5:
                    coverage["branch_coverage"] = float(parts[-2].strip("%"))
            elif line.strip().endswith("0%") and not line.startswith("-"):
                module = line.split()[0]
                coverage["uncovered_modules"].append(module)
    except Exception:
        pass

    return coverage


def generate_report(args) -> dict[str, Any]:
    """
    Generate a comprehensive test metrics report.

    Returns:
        Dictionary with the report data.
    """
    print("Counting tests by category...")
    category_counts = count_tests_by_category()

    print("Counting tests by speed...")
    speed_counts = count_tests_by_speed()

    failing_tests = {}
    if args.run_tests:
        print("Running tests to identify failures...")
        failing_tests = identify_failing_tests()

    print("Calculating coverage metrics...")
    coverage = calculate_coverage()

    # Build the report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "test_counts": {
            "by_category": category_counts,
            "by_speed": speed_counts,
        },
        "failing_tests": failing_tests,
        "coverage": coverage,
    }

    # Calculate summary metrics
    total_tests = category_counts["total"]
    total_failing = (
        sum(len(tests) for tests in failing_tests.values()) if failing_tests else 0
    )

    report["summary"] = {
        "total_tests": total_tests,
        "total_failing": total_failing,
        "pass_rate": (
            (total_tests - total_failing) / total_tests * 100 if total_tests > 0 else 0
        ),
        "line_coverage": coverage["line_coverage"],
        "uncovered_modules": coverage.get("uncovered_modules", []),
    }

    return report


def save_json_report(report: dict[str, Any], filename: str):
    """Save the report as a JSON file."""
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {filename}")


def generate_html_report(report: dict[str, Any], filename: str):
    """Generate an HTML report from the metrics data."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DevSynth Test Metrics Report</title>
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
        </style>
    </head>
    <body>
        <h1>DevSynth Test Metrics Report</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">
                <span class="metric-name">Total Tests:</span>
                <span class="metric-value">{report['summary']['total_tests']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Failing Tests:</span>
                <span class="metric-value {'bad' if report['summary']['total_failing'] > 0 else 'good'}">{report['summary']['total_failing']}</span>
            </div>
            <div class="metric">
                <span class="metric-name">Pass Rate:</span>
                <span class="metric-value {'good' if report['summary']['pass_rate'] > 90 else 'warning' if report['summary']['pass_rate'] > 75 else 'bad'}">{report['summary']['pass_rate']:.2f}%</span>
            </div>
            <div class="metric">
                <span class="metric-name">Line Coverage:</span>
                <span class="metric-value {'good' if report['summary']['line_coverage'] > 80 else 'warning' if report['summary']['line_coverage'] > 60 else 'bad'}">{report['summary']['line_coverage']:.2f}%</span>
            </div>
        </div>

        <h2>Test Counts by Category</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Count</th>
            </tr>
    """

    # Add category counts
    for category, count in report["test_counts"]["by_category"].items():
        if category != "total":
            html += f"""
            <tr>
                <td>{category}</td>
                <td>{count}</td>
            </tr>
            """

    html += f"""
        </table>

        <h2>Test Counts by Speed</h2>
        <table>
            <tr>
                <th>Speed</th>
                <th>Count</th>
            </tr>
    """

    # Add speed counts
    for speed, count in report["test_counts"]["by_speed"].items():
        html += f"""
        <tr>
            <td>{speed}</td>
            <td>{count}</td>
        </tr>
        """

    # Add failing tests if available
    if report["failing_tests"]:
        html += """
        <h2>Failing Tests</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Test</th>
            </tr>
        """

        for category, tests in report["failing_tests"].items():
            for test in tests:
                html += f"""
                <tr>
                    <td>{category}</td>
                    <td>{test}</td>
                </tr>
                """

        html += "</table>"

    html += f"""
        <div class="timestamp">
            Generated on: {report['timestamp']}
        </div>
    </body>
    </html>
    """

    with open(filename, "w") as f:
        f.write(html)
    print(f"HTML report saved to {filename}")


def clear_cache():
    """Clear all cached data."""
    cache_dir = ".test_metrics_cache"
    if os.path.exists(cache_dir):
        print(f"Clearing cache directory: {cache_dir}")
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
    else:
        print("No cache directory found.")


def create_issues_for_failing_tests(failing_tests: dict[str, list[str]]) -> list[Path]:
    """Create issue files for failing tests when their total count is below 50."""
    total = sum(len(t) for t in failing_tests.values())
    if total == 0 or total >= 50:
        return []

    issue_dir = Path("issues")
    issue_dir.mkdir(exist_ok=True)
    existing = [int(p.stem) for p in issue_dir.glob("*.md") if p.stem.isdigit()]
    next_number = max(existing) + 1 if existing else 1
    created: list[Path] = []
    for tests in failing_tests.values():
        for test in tests:
            issue_path = issue_dir / f"{next_number}.md"
            content = (
                f"# Issue {next_number}: Fix failing test {test}\n\n"
                "Milestone: 0.1.0-alpha.1\n\n"
                f"The test `{test}` is failing. Investigate and resolve.\n"
            )
            with open(issue_path, "w") as f:
                f.write(content)
            created.append(issue_path)
            next_number += 1
    return created


def generate_report(args) -> dict[str, Any]:
    """
    Generate a comprehensive test metrics report based on command-line arguments.

    Args:
        args: Command-line arguments

    Returns:
        Dictionary with the report data
    """
    # Count tests by category
    use_cache = not args.no_cache
    category_counts = count_tests_by_category(use_cache)

    # Filter by category if specified
    if args.category != "all":
        if args.category in category_counts:
            filtered_counts = {
                args.category: category_counts[args.category],
                "total": category_counts[args.category],
            }
            category_counts = filtered_counts
        else:
            print(f"Category '{args.category}' not found in test categories.")
            category_counts = {args.category: 0, "total": 0}

    # Count tests by speed
    speed_counts = count_tests_by_speed(use_cache, category_counts)

    # Filter by speed if specified
    if args.speed != "all":
        if args.speed in speed_counts:
            filtered_counts = {args.speed: speed_counts[args.speed]}
            speed_counts = filtered_counts
        else:
            print(f"Speed '{args.speed}' not found in speed categories.")
            speed_counts = {args.speed: 0}

    # Identify failing tests if requested
    failing_tests: dict[str, list[str]] = {}
    memory_usage: dict[str, Any] = {}
    if args.run_tests:
        parallel = not args.no_parallel
        segment = args.segment
        segment_size = args.segment_size

        failing_tests, memory_usage = identify_failing_tests(
            parallel=parallel,
            segment=segment,
            segment_size=segment_size,
            use_cache=use_cache,
        )

        if args.category != "all":
            if args.category in failing_tests:
                failing_tests = {args.category: failing_tests[args.category]}
            else:
                failing_tests = {args.category: []}

    created_issues: list[Path] = []
    if failing_tests:
        created_issues = create_issues_for_failing_tests(failing_tests)

    coverage = {"line_coverage": 0.0, "branch_coverage": 0.0}
    coverage_by_speed: dict[str, float] = {}
    coverage_failures: list[str] = []
    if not args.skip_coverage:
        print("Calculating coverage metrics...")
        coverage = calculate_coverage()
        for speed_name in ["fast", "medium"]:
            speed_cov = calculate_coverage(speed_name)["line_coverage"]
            coverage_by_speed[speed_name] = speed_cov
            threshold = COVERAGE_THRESHOLDS.get(speed_name, 0)
            if speed_cov < threshold:
                coverage_failures.append(
                    f"{speed_name} ({speed_cov:.2f}% < {threshold}%)"
                )

    # Build the report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "execution_parameters": {
            "category": args.category,
            "speed": args.speed,
            "run_tests": args.run_tests,
            "skip_coverage": args.skip_coverage,
            "parallel": not args.no_parallel,
            "use_cache": not args.no_cache,
            "segment": args.segment,
            "segment_size": (
                args.segment_size if hasattr(args, "segment_size") else None
            ),
        },
        "test_counts": {
            "by_category": category_counts,
            "by_speed": speed_counts,
        },
        "failing_tests": failing_tests,
        "memory_usage": memory_usage,
        "coverage": coverage,
        "coverage_by_speed": coverage_by_speed,
        "created_issues": [str(p) for p in created_issues],
        "coverage_failures": coverage_failures,
    }

    # Calculate summary metrics
    total_tests = category_counts["total"]
    total_failing = (
        sum(len(tests) for tests in failing_tests.values()) if failing_tests else 0
    )

    report["summary"] = {
        "total_tests": total_tests,
        "total_failing": total_failing,
        "pass_rate": (
            (total_tests - total_failing) / total_tests * 100 if total_tests > 0 else 0
        ),
        "line_coverage": coverage["line_coverage"],
        "coverage_by_speed": coverage_by_speed,
    }

    return report


def print_execution_plan(args):
    """Print the execution plan based on command-line arguments."""
    print("EXECUTION PLAN:")
    print(f"- Category: {args.category}")
    print(f"- Speed: {args.speed}")
    print(f"- Run Tests: {args.run_tests}")
    print(f"- Skip Coverage: {args.skip_coverage}")
    print(f"- Parallel Execution: {not args.no_parallel}")
    print(f"- Use Cache: {not args.no_cache}")
    print(f"- Segmentation: {args.segment}")
    if args.segment and hasattr(args, "segment_size"):
        print(f"- Segment Size: {args.segment_size}")
    print(f"{'='*80}\n")


def print_summary(report, args, execution_time):
    """Print a summary of the report and execution time."""
    print(f"\n{'='*80}")
    print("SUMMARY:")
    print(f"{'='*80}")
    print(f"- Total Tests: {report['summary']['total_tests']}")
    print(f"- Tests by Category:")
    for category, count in report["test_counts"]["by_category"].items():
        if category != "total":
            print(f"  - {category}: {count}")
    print(f"- Tests by Speed:")
    for speed, count in report["test_counts"]["by_speed"].items():
        print(f"  - {speed}: {count}")

    if args.run_tests:
        total_failing = report["summary"]["total_failing"]
        print(f"- Failing Tests: {total_failing}")
        print(f"- Pass Rate: {report['summary']['pass_rate']:.2f}%")
        if report.get("memory_usage"):
            print("- Top Memory Consumers:")
            top_mem = sorted(
                report["memory_usage"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            for test, mem in top_mem:
                print(f"  - {test}: {mem:.2f} MB")

    if not args.skip_coverage:
        print(f"- Line Coverage: {report['summary']['line_coverage']:.2f}%")
        for speed, value in report["summary"]["coverage_by_speed"].items():
            print(f"  - {speed}: {value:.2f}%")
        uncovered = report["coverage"].get("uncovered_modules", [])
        if uncovered:
            print("- Modules with 0% coverage:")
            for mod in uncovered:
                print(f"  - {mod}")

    print(
        f"\nExecution Time: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)"
    )


def print_optimization_tips(args):
    """Print tips for faster execution based on command-line arguments."""
    print("\nTips for faster execution:")
    if not args.skip_coverage:
        print("- Skip coverage calculation: --skip-coverage")
    if args.category == "all":
        print("- Analyze only a specific category: --category unit")
    if args.speed == "all":
        print("- Analyze only a specific speed: --speed fast")
    if not args.segment and args.run_tests:
        print("- Run tests in smaller batches: --segment")
    if hasattr(args, "no_cache") and not args.no_cache:
        print("- Use cached results when available: remove --no-cache")

    print("\nFor more options, run: python scripts/test_metrics.py --help")


def main():
    """Main function."""
    start_time = time.time()
    args = parse_args()

    # Clear cache if requested
    if args.clear_cache:
        clear_cache()

    print("Generating test metrics report...")
    print(f"{'='*80}")

    # Print execution plan
    print_execution_plan(args)

    # Generate the report
    report = generate_report(args)
    if report.get("coverage_failures"):
        print("Coverage below threshold for: " + ", ".join(report["coverage_failures"]))
        sys.exit(1)

    # Save the report
    save_json_report(report, args.output)

    if args.html:
        html_filename = args.output.replace(".json", ".html")
        generate_html_report(report, html_filename)

    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time

    # Print summary
    print_summary(report, args, execution_time)

    # Print tips for faster execution
    print_optimization_tips(args)


if __name__ == "__main__":
    main()
