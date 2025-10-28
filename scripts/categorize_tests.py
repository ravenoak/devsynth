#!/usr/bin/env python
"""
Script to analyze test execution times and add appropriate markers.

This script runs tests with the pytest-benchmark plugin to measure execution times,
then adds appropriate markers (fast, medium, slow) to tests based on their execution time.
It also identifies tests that might need the isolation marker.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Thresholds for categorizing tests (in seconds)
FAST_THRESHOLD = 1.0
MEDIUM_THRESHOLD = 5.0

# Regex patterns for finding and updating markers
MARKER_PATTERN = re.compile(r"@pytest\.mark\.(fast|medium|slow|isolation)")
FUNCTION_PATTERN = re.compile(r"def (test_\w+)\(")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze test execution times and add appropriate markers."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="tests",
        help="Directory containing tests to analyze (default: tests)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="test_timing_report.json",
        help="Output file for timing report (default: test_timing_report.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update test files with appropriate markers",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of tests to run in each batch (default: 100)",
    )
    parser.add_argument(
        "--skip-benchmarks",
        action="store_true",
        help="Skip running benchmarks (use existing timing report)",
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
        help="Only analyze tests in the specified category",
    )
    return parser.parse_args()


def run_benchmarks(directory: str, batch_size: int = 100) -> dict:
    """
    Run tests with pytest-benchmark to measure execution times.

    Args:
        directory: Directory containing tests to benchmark
        batch_size: Number of tests to run in each batch

    Returns:
        Dictionary with benchmark results
    """
    print(f"Running benchmarks for tests in {directory}...")

    # Create a temporary directory for benchmark results
    os.makedirs(".benchmarks", exist_ok=True)

    # First collect all tests
    collect_cmd = ["python", "-m", "pytest", directory, "--collect-only", "-q"]

    try:
        collect_result = subprocess.run(
            collect_cmd, check=True, capture_output=True, text=True
        )
        test_list = []

        # Parse the output to get the list of tests
        for line in collect_result.stdout.split("\n"):
            if line.startswith(directory):
                test_list.append(line.strip())

        if not test_list:
            print(f"No tests found in {directory}")
            return {}

        print(
            f"Found {len(test_list)} tests, running benchmarks in batches of {batch_size}..."
        )

        # Initialize an empty benchmark data structure
        benchmark_data = {"benchmarks": []}

        # Run tests in batches
        for i in range(0, len(test_list), batch_size):
            batch = test_list[i : i + batch_size]
            print(
                f"\nRunning batch {i//batch_size + 1}/{(len(test_list) + batch_size - 1)//batch_size}..."
            )

            # Create a unique filename for this batch
            batch_filename = f".benchmarks/timing_batch_{i//batch_size + 1}.json"

            # Run pytest with benchmark plugin for this batch
            cmd = [
                "python",
                "-m",
                "pytest",
                *batch,
                "--benchmark-only",
                f"--benchmark-json={batch_filename}",
                "-v",
            ]

            try:
                subprocess.run(cmd, check=True)

                # Load benchmark results for this batch
                with open(batch_filename) as f:
                    batch_data = json.load(f)

                # Append the benchmarks from this batch to the overall results
                if "benchmarks" in batch_data:
                    benchmark_data["benchmarks"].extend(batch_data["benchmarks"])
            except subprocess.CalledProcessError:
                print(f"Error running benchmarks for batch {i//batch_size + 1}")
            except FileNotFoundError:
                print(f"Benchmark results file not found for batch {i//batch_size + 1}")

        return benchmark_data
    except subprocess.CalledProcessError:
        print("Error collecting tests")
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}


def analyze_benchmarks(benchmark_data: dict) -> dict[str, str]:
    """Analyze benchmark data and determine appropriate markers."""
    test_markers = {}

    if not benchmark_data or "benchmarks" not in benchmark_data:
        return test_markers

    for benchmark in benchmark_data["benchmarks"]:
        test_name = benchmark["name"]
        test_time = benchmark["stats"]["mean"]

        # Determine marker based on execution time
        if test_time < FAST_THRESHOLD:
            marker = "fast"
        elif test_time < MEDIUM_THRESHOLD:
            marker = "medium"
        else:
            marker = "slow"

        test_markers[test_name] = marker

    return test_markers


def find_test_files(directory: str) -> list[Path]:
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(os.path.join(root, file)))
    return test_files


def analyze_test_file(file_path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """
    Analyze a test file to extract existing markers and test functions.

    Returns:
        Tuple containing:
        - Dictionary mapping test names to their existing markers
        - Dictionary mapping line numbers to test names
    """
    existing_markers = {}
    test_line_numbers = {}

    with open(file_path) as f:
        lines = f.readlines()

    current_markers = []
    for i, line in enumerate(lines):
        # Check for markers
        marker_match = MARKER_PATTERN.search(line)
        if marker_match:
            current_markers.append(marker_match.group(1))

        # Check for test functions
        func_match = FUNCTION_PATTERN.search(line)
        if func_match:
            test_name = func_match.group(1)
            test_line_numbers[i] = test_name
            if current_markers:
                existing_markers[test_name] = current_markers.copy()
            current_markers = []

    return existing_markers, test_line_numbers


def update_test_file(
    file_path: Path, test_markers: dict[str, str], dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Update a test file with appropriate markers.

    Returns:
        Tuple containing counts of (added, updated, unchanged) markers
    """
    added = 0
    updated = 0
    unchanged = 0

    # Analyze the file
    existing_markers, test_line_numbers = analyze_test_file(file_path)

    if not test_line_numbers:
        return added, updated, unchanged

    with open(file_path) as f:
        lines = f.readlines()

    # Process each test function
    for line_num, test_name in test_line_numbers.items():
        if test_name not in test_markers:
            continue

        new_marker = test_markers[test_name]

        # Check if the test already has the correct marker
        if test_name in existing_markers and new_marker in existing_markers[test_name]:
            unchanged += 1
            continue

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
                    updated += 1
                    break
        else:
            # Add new marker
            marker_line = f"@pytest.mark.{new_marker}\n"
            lines.insert(line_num, marker_line)

            # Update line numbers for subsequent tests
            test_line_numbers = {
                k + 1 if k >= line_num else k: v for k, v in test_line_numbers.items()
            }

            if dry_run:
                print(f"Would add to {file_path}:{line_num+1} - {marker_line.strip()}")
            added += 1

    # Write changes back to the file
    if not dry_run and (added > 0 or updated > 0):
        with open(file_path, "w") as f:
            f.writelines(lines)

    return added, updated, unchanged


def identify_isolation_candidates(directory: str) -> set[str]:
    """
    Identify tests that might need the isolation marker.

    This looks for tests that modify global state, use files, or have side effects.
    """
    isolation_candidates = set()

    # Run tests with special flags to detect isolation needs
    cmd = [
        "python",
        "-m",
        "pytest",
        directory,
        "-v",
        "--collect-only",
        "--no-header",
        "--no-summary",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Analyze output to find tests that might need isolation
        for line in result.stdout.splitlines():
            if any(
                pattern in line
                for pattern in [
                    "test_file",
                    "test_io",
                    "test_network",
                    "test_database",
                    "test_global",
                    "test_env",
                    "test_environment",
                    "test_config",
                ]
            ):
                isolation_candidates.add(line.strip())

        return isolation_candidates
    except subprocess.CalledProcessError:
        print("Error analyzing tests for isolation needs")
        return set()


def main():
    """Main function."""
    args = parse_args()

    # Set global thresholds based on command-line arguments
    global FAST_THRESHOLD, MEDIUM_THRESHOLD
    FAST_THRESHOLD = args.fast_threshold
    MEDIUM_THRESHOLD = args.medium_threshold

    # Determine the directory to analyze
    directory = args.directory
    if args.category != "all":
        if args.category == "unit":
            directory = "tests/unit"
        elif args.category == "integration":
            directory = "tests/integration"
        elif args.category == "behavior":
            directory = "tests/behavior"

    print(f"Analyzing tests in {directory}...")
    print(f"Fast threshold: {FAST_THRESHOLD}s, Medium threshold: {MEDIUM_THRESHOLD}s")

    # Run benchmarks or load existing timing report
    if args.skip_benchmarks:
        print("Skipping benchmarks, using existing timing report...")
        try:
            with open(args.output) as f:
                report = json.load(f)
                test_markers = {
                    name: data["marker"]
                    for name, data in report.get("tests", {}).items()
                }
                if not test_markers:
                    print(
                        "No test markers found in timing report, running benchmarks..."
                    )
                    benchmark_data = run_benchmarks(directory, args.batch_size)
                    test_markers = analyze_benchmarks(benchmark_data)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Timing report not found or invalid, running benchmarks...")
            benchmark_data = run_benchmarks(directory, args.batch_size)
            test_markers = analyze_benchmarks(benchmark_data)
    else:
        # Run benchmarks to measure test execution times
        start_time = time.time()
        benchmark_data = run_benchmarks(directory, args.batch_size)
        end_time = time.time()
        print(f"Benchmarking completed in {end_time - start_time:.2f} seconds")

        # Analyze benchmark data
        test_markers = analyze_benchmarks(benchmark_data)

    # Save timing report
    with open(args.output, "w") as f:
        json.dump(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "directory": directory,
                "fast_threshold": FAST_THRESHOLD,
                "medium_threshold": MEDIUM_THRESHOLD,
                "test_count": len(test_markers),
                "fast_tests": sum(
                    1 for marker in test_markers.values() if marker == "fast"
                ),
                "medium_tests": sum(
                    1 for marker in test_markers.values() if marker == "medium"
                ),
                "slow_tests": sum(
                    1 for marker in test_markers.values() if marker == "slow"
                ),
                "tests": {
                    name: {"marker": marker} for name, marker in test_markers.items()
                },
            },
            f,
            indent=2,
        )

    print(f"Timing report saved to {args.output}")
    print(f"Test counts by speed category:")
    print(
        f"  - Fast tests: {sum(1 for marker in test_markers.values() if marker == 'fast')}"
    )
    print(
        f"  - Medium tests: {sum(1 for marker in test_markers.values() if marker == 'medium')}"
    )
    print(
        f"  - Slow tests: {sum(1 for marker in test_markers.values() if marker == 'slow')}"
    )

    # Identify tests that might need isolation
    isolation_candidates = identify_isolation_candidates(directory)
    if isolation_candidates:
        print("\nTests that might need the isolation marker:")
        for test in isolation_candidates:
            print(f"  - {test}")

    # Update test files if requested
    if args.update or args.dry_run:
        test_files = find_test_files(directory)

        total_added = 0
        total_updated = 0
        total_unchanged = 0

        print(f"\nUpdating {len(test_files)} test files...")

        for i, file_path in enumerate(test_files):
            if i % 10 == 0:
                print(f"Processing file {i+1}/{len(test_files)}...")

            added, updated, unchanged = update_test_file(
                file_path, test_markers, args.dry_run
            )
            total_added += added
            total_updated += updated
            total_unchanged += unchanged

        action = "Would " if args.dry_run else ""
        print(
            f"\n{action}Add {total_added} markers, update {total_updated} markers, leave {total_unchanged} markers unchanged"
        )

    print("\nTest categorization complete")

    # Print tips for running tests by speed category
    print("\nTips for running tests by speed category:")
    print("  - Run fast tests: poetry run devsynth run-tests --fast")
    print("  - Run medium tests: poetry run devsynth run-tests --medium")
    print("  - Run slow tests: poetry run devsynth run-tests --slow")
    print(
        "  - Run fast and medium tests: poetry run devsynth run-tests --fast --medium"
    )


if __name__ == "__main__":
    main()
