#!/usr/bin/env python3
"""
Script to execute all unit, integration, and behavior tests for DevSynth.

This script runs all tests and generates a comprehensive report of the results.
It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/run_all_tests.py [--unit] [--integration] [--behavior] [--all]

Options:
    --unit        Run only unit tests
    --integration Run only integration tests
    --behavior    Run only behavior tests
    --all         Run all tests (default)
    --report      Generate HTML report
    --verbose     Show verbose output
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run DevSynth tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--behavior", action="store_true", help="Run only behavior tests"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")

    args = parser.parse_args()

    # If no test type is specified, run all tests
    if not (args.unit or args.integration or args.behavior or args.all):
        args.all = True

    return args


def run_tests(test_type, verbose=False, report=False):
    """
    Run tests of the specified type.

    Args:
        test_type (str): Type of tests to run ('unit', 'integration', 'behavior', or 'all')
        verbose (bool): Whether to show verbose output
        report (bool): Whether to generate an HTML report

    Returns:
        tuple: (success, output) where success is a boolean indicating if all tests passed
               and output is the command output
    """
    print(f"\n{'='*80}")
    print(f"Running {test_type} tests...")
    print(f"{'='*80}")

    cmd = [sys.executable, "-m", "pytest"]

    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "behavior":
        cmd.append("tests/behavior/")
    elif test_type == "all":
        cmd.append("tests/")

    if verbose:
        cmd.append("-v")

    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"test_reports/{timestamp}/{test_type}")
        report_dir.parent.mkdir(parents=True, exist_ok=True)

        # Add HTML report options
        cmd.extend(
            [
                f"--html=test_reports/{timestamp}/{test_type}/report.html",
                "--self-contained-html",
            ]
        )

    # Run the tests
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)

        success = result.returncode == 0
        return success, result.stdout + result.stderr
    except Exception as e:
        print(f"Error running tests: {e}")
        return False, str(e)


def main():
    """Main function to run tests based on command line arguments."""
    args = parse_args()

    # Ensure pytest-html is installed if report is requested
    if args.report:
        try:
            import pytest_html  # noqa: F401
        except ImportError:
            print(
                "pytest-html is required for HTML reports. Please install development dependencies:"
            )
            print("  poetry install --with dev,docs --all-extras")
            return 1

    all_success = True
    results = {}

    # Run the specified tests
    if args.all or args.unit:
        unit_success, unit_output = run_tests("unit", args.verbose, args.report)
        all_success = all_success and unit_success
        results["unit"] = unit_success

    if args.all or args.integration:
        integration_success, integration_output = run_tests(
            "integration", args.verbose, args.report
        )
        all_success = all_success and integration_success
        results["integration"] = integration_success

    if args.all or args.behavior:
        behavior_success, behavior_output = run_tests(
            "behavior", args.verbose, args.report
        )
        all_success = all_success and behavior_success
        results["behavior"] = behavior_success

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_type, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_type.upper()} TESTS: {status}")

    print("\nOVERALL STATUS:", "PASSED" if all_success else "FAILED")

    if args.report:
        print(
            f"\nTest reports generated in test_reports/{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
        )

    # Return appropriate exit code
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
