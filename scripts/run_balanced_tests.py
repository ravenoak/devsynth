#!/usr/bin/env python
"""
Script to run tests with balanced load distribution.

This script optimizes test segmentation by intelligently distributing tests
across segments based on their execution time. It uses a bin packing algorithm
to create balanced segments, which can significantly improve test performance
when running tests in parallel.

Usage:
    python scripts/run_balanced_tests.py [options]

Options:
    --test-dir DIR      Directory containing tests (default: tests)
    --category CAT      Only run tests in the specified category (default: all)
    --speed SPEED       Only run tests with the specified speed marker (default: all)
    --processes N       Number of processes to use (default: number of CPU cores)
    --verbose           Show verbose output
    --report            Generate HTML report
    --no-cache          Disable caching (always collect fresh data)
"""

import argparse
import json
import multiprocessing
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import test_utils


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests with balanced load distribution."
    )

    # Add common arguments
    parser = test_utils.add_common_arguments(parser)

    # Add specific arguments for this script
    parser.add_argument(
        "--processes",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of processes to use (default: number of CPU cores)",
    )

    return parser.parse_args()


def get_test_times(tests: list[str], use_cache: bool = True) -> dict[str, float]:
    """
    Get execution times for a list of tests.

    Args:
        tests: List of test paths
        use_cache: Whether to use cached timing results

    Returns:
        Dictionary mapping test paths to execution times
    """
    print(f"Getting execution times for {len(tests)} tests...")

    test_times = {}

    for i, test in enumerate(tests):
        if i % 10 == 0:
            print(f"Processing test {i+1}/{len(tests)}...")

        execution_time, _, _ = test_utils.measure_test_time(test, use_cache=use_cache)
        test_times[test] = execution_time

    return test_times


def distribute_tests(
    tests: list[str], test_times: dict[str, float], num_processes: int
) -> list[list[str]]:
    """
    Distribute tests across processes using a bin packing algorithm.

    Args:
        tests: List of test paths
        test_times: Dictionary mapping test paths to execution times
        num_processes: Number of processes to distribute tests across

    Returns:
        List of lists, where each inner list contains the tests for one process
    """
    # Sort tests by execution time (descending)
    sorted_tests = sorted(tests, key=lambda t: test_times.get(t, 0.0), reverse=True)

    # Initialize bins (one for each process)
    bins = [[] for _ in range(num_processes)]
    bin_times = [0.0] * num_processes

    # Distribute tests using a greedy bin packing algorithm
    for test in sorted_tests:
        # Find the bin with the smallest total execution time
        min_bin = min(range(num_processes), key=lambda i: bin_times[i])

        # Add the test to that bin
        bins[min_bin].append(test)
        bin_times[min_bin] += test_times.get(test, 0.0)

    # Print the distribution
    print("\nTest distribution across processes:")
    for i, (bin_tests, bin_time) in enumerate(zip(bins, bin_times)):
        print(f"Process {i+1}: {len(bin_tests)} tests, {bin_time:.2f} seconds")

    return bins


def run_tests_in_parallel(test_bins: list[list[str]], args) -> int:
    """
    Run tests in parallel using multiple processes.

    Args:
        test_bins: List of lists, where each inner list contains the tests for one process
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not test_bins or all(not bin_tests for bin_tests in test_bins):
        print("No tests to run.")
        return 0

    print(f"\nRunning tests in {len(test_bins)} parallel processes...")

    # Create a directory for XML reports
    xml_dir = os.path.join(test_utils.TEST_CACHE_DIR, "xml_reports")
    os.makedirs(xml_dir, exist_ok=True)

    # Start a process for each bin
    processes = []
    for i, bin_tests in enumerate(test_bins):
        if not bin_tests:
            continue

        # Create a unique XML report file for this process
        xml_report = os.path.join(xml_dir, f"junit_report_process_{i+1}.xml")

        # Build the pytest command
        cmd = [sys.executable, "-m", "pytest", "--maxfail=1"]
        cmd.extend(bin_tests)

        # Add options based on command-line arguments
        if args.verbose:
            cmd.append("-v")

        if args.report:
            # Create a unique HTML report for this process
            html_report = os.path.join(
                test_utils.TEST_CACHE_DIR, f"html_report_process_{i+1}.html"
            )
            cmd.extend(["--html", html_report, "--self-contained-html"])

        # Add JUnit XML output
        cmd.extend(["--junitxml", xml_report])

        # Start the process
        print(f"Starting process {i+1} with {len(bin_tests)} tests...")
        process = subprocess.Popen(cmd)
        processes.append(process)

    # Wait for all processes to complete
    exit_codes = []
    for i, process in enumerate(processes):
        exit_code = process.wait()
        exit_codes.append(exit_code)
        print(f"Process {i+1} completed with exit code {exit_code}")

    # Combine XML reports if HTML report is requested
    if args.report:
        try:
            import xml.etree.ElementTree as ET

            # Create a combined XML report
            combined_xml = os.path.join(xml_dir, "junit_report_combined.xml")

            # Create a root element for the combined report
            root = ET.Element("testsuites")

            # Add each process's report to the combined report
            for i in range(len(test_bins)):
                xml_report = os.path.join(xml_dir, f"junit_report_process_{i+1}.xml")
                if os.path.exists(xml_report):
                    try:
                        tree = ET.parse(xml_report)
                        process_root = tree.getroot()

                        # Add all test suites from this process to the combined report
                        for testsuite in process_root:
                            root.append(testsuite)
                    except Exception as e:
                        print(f"Error parsing XML report for process {i+1}: {e}")

            # Write the combined report
            tree = ET.ElementTree(root)
            tree.write(combined_xml)

            # Generate a combined HTML report
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--maxfail=1",
                f"--junitxml={combined_xml}",
                "--html=test_report.html",
                "--self-contained-html",
            ]
            subprocess.run(cmd)

            print("Combined HTML report generated: test_report.html")
        except Exception as e:
            print(f"Error combining XML reports: {e}")

    # Return non-zero if any process failed
    return 1 if any(code != 0 for code in exit_codes) else 0


def main():
    """Main function."""
    args = parse_args()

    # Get the test directory based on category
    test_dir = test_utils.get_test_directory(args.category)

    # Collect tests
    tests = test_utils.collect_tests(test_dir, args.speed, not args.no_cache)

    if not tests:
        print("No tests found.")
        return 0

    # Get test execution times
    test_times = get_test_times(tests, not args.no_cache)

    # Distribute tests across processes
    test_bins = distribute_tests(tests, test_times, args.processes)

    # Run tests in parallel
    return run_tests_in_parallel(test_bins, args)


if __name__ == "__main__":
    sys.exit(main())
