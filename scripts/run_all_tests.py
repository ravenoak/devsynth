#!/usr/bin/env python3
"""Script to execute DevSynth tests.

This script wraps the shared :func:`devsynth.testing.run_tests` helper and
provides a command line interface similar to the DevSynth CLI.

Usage:
    python scripts/run_all_tests.py [--target TARGET]
                                   [--fast] [--medium] [--slow]
                                   [--report] [--verbose]
                                   [--no-parallel] [--segment]
                                   [--segment-size SIZE]
"""

import argparse
import sys
import time

from devsynth.testing.run_tests import run_tests


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run DevSynth tests")

    parser.add_argument(
        "--target",
        choices=["unit-tests", "integration-tests", "behavior-tests", "all-tests"],
        help="Test target to run",
    )
    # Backwards compatibility flags
    parser.add_argument("--unit", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--integration", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--behavior", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--all", action="store_true", help=argparse.SUPPRESS)

    speed_group = parser.add_argument_group("Speed Category")
    speed_group.add_argument(
        "--fast", action="store_true", help="Run only fast tests (execution time < 1s)"
    )
    speed_group.add_argument(
        "--medium",
        action="store_true",
        help="Run only medium tests (execution time between 1s and 5s)",
    )
    speed_group.add_argument(
        "--slow", action="store_true", help="Run only slow tests (execution time > 5s)"
    )

    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")

    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel test execution"
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
        help="Number of tests per batch when using segmentation",
    )

    args = parser.parse_args()

    if not args.target:
        targets = []
        if args.unit:
            targets.append("unit-tests")
        if args.integration:
            targets.append("integration-tests")
        if args.behavior:
            targets.append("behavior-tests")
        if args.all or not targets:
            targets = ["all-tests"]
        args.targets = targets
    else:
        args.targets = [args.target]

    if not (args.fast or args.medium or args.slow):
        args.fast = args.medium = args.slow = True

    return args


def main() -> int:
    """Main function to run tests based on command line arguments."""
    args = parse_args()

    if args.report:
        try:
            import pytest_html  # noqa: F401
        except ImportError:
            print(
                "pytest-html is required for HTML reports. Please install development dependencies:"
            )
            print("  poetry install --with dev,docs --all-extras")
            return 1

    if not args.no_parallel:
        try:
            import xdist  # noqa: F401
        except ImportError:
            print(
                "pytest-xdist is required for parallel test execution. Please install development dependencies:"
            )
            print("  poetry install --with dev,docs --all-extras")
            return 1

    parallel = not args.no_parallel
    speed_categories = []
    if args.fast:
        speed_categories.append("fast")
    if args.medium:
        speed_categories.append("medium")
    if args.slow:
        speed_categories.append("slow")

    print("\n" + "=" * 80)
    print("TEST EXECUTION PLAN")
    print("=" * 80)
    print(f"Targets: {', '.join(args.targets)}")
    print(f"Speed Categories: {', '.join(speed_categories)}")
    print(f"Parallel Execution: {'Disabled' if args.no_parallel else 'Enabled'}")
    print(f"Test Segmentation: {'Enabled' if args.segment else 'Disabled'}")
    if args.segment:
        print(f"Segment Size: {args.segment_size}")
    print(f"Report Generation: {'Enabled' if args.report else 'Disabled'}")
    print(f"Verbose Output: {'Enabled' if args.verbose else 'Disabled'}")

    start_time = time.time()
    overall_success = True
    results = {}

    for target in args.targets:
        success, _ = run_tests(
            target,
            speed_categories,
            args.verbose,
            args.report,
            parallel,
            args.segment,
            args.segment_size,
        )
        overall_success = overall_success and success
        results[target] = success

    end_time = time.time()
    execution_time = end_time - start_time

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for target, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{target.upper()}: {status}")

    print(f"\nOVERALL STATUS: {'PASSED' if overall_success else 'FAILED'}")
    print(
        f"EXECUTION TIME: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)"
    )

    if execution_time > 60:
        print("\nTips for faster test execution:")
        if not args.fast and not args.medium:
            print("- Run only fast tests during development: --fast")
        if not args.segment:
            print("- Enable test segmentation: --segment")
        if args.targets == ["all-tests"]:
            print(
                "- Run only specific test types with --target (unit-tests, integration-tests, behavior-tests)"
            )
        if not parallel:
            print("- Enable parallel execution (if disabled): remove --no-parallel")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
