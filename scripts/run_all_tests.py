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
import logging
import sys
import time

from devsynth.logging_setup import DevSynthLogger, configure_logging

from devsynth.exceptions import DevSynthError
from devsynth.testing.run_tests import run_tests

configure_logging()
logger = DevSynthLogger(__name__)


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

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.report:
        try:
            import pytest_html  # noqa: F401
        except ImportError:
            logger.error(
                "pytest-html is required for HTML reports. Please install development dependencies:"
            )
            logger.error("  poetry install --with dev,docs --all-extras")
            return 1

    if not args.no_parallel:
        try:
            import xdist  # noqa: F401
        except ImportError:
            logger.error(
                "pytest-xdist is required for parallel test execution. Please install development dependencies:"
            )
            logger.error("  poetry install --with dev,docs --all-extras")
            return 1

    parallel = not args.no_parallel
    speed_categories = []
    if args.fast:
        speed_categories.append("fast")
    if args.medium:
        speed_categories.append("medium")
    if args.slow:
        speed_categories.append("slow")

    separator = "=" * 80
    logger.info("\n%s", separator)
    logger.info("TEST EXECUTION PLAN")
    logger.info(separator)
    logger.info("Targets: %s", ", ".join(args.targets))
    logger.info("Speed Categories: %s", ", ".join(speed_categories))
    logger.info("Parallel Execution: %s", "Disabled" if args.no_parallel else "Enabled")
    logger.info("Test Segmentation: %s", "Enabled" if args.segment else "Disabled")
    if args.segment:
        logger.info("Segment Size: %d", args.segment_size)
    logger.info("Report Generation: %s", "Enabled" if args.report else "Disabled")
    logger.info("Verbose Output: %s", "Enabled" if args.verbose else "Disabled")

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

    logger.info("\n%s", separator)
    logger.info("TEST SUMMARY")
    logger.info(separator)
    for target, success in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info("%s: %s", target.upper(), status)

    logger.info("OVERALL STATUS: %s", "PASSED" if overall_success else "FAILED")
    logger.info(
        "EXECUTION TIME: %.2f seconds (%.2f minutes)",
        execution_time,
        execution_time / 60,
    )

    if execution_time > 60:
        logger.info("\nTips for faster test execution:")
        if not args.fast and not args.medium:
            logger.info("- Run only fast tests during development: --fast")
        if not args.segment:
            logger.info("- Enable test segmentation: --segment")
        if args.targets == ["all-tests"]:
            logger.info(
                "- Run only specific test types with --target (unit-tests, integration-tests, behavior-tests)"
            )
        if not parallel:
            logger.info(
                "- Enable parallel execution (if disabled): remove --no-parallel"
            )

    return 0 if overall_success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DevSynthError:
        logger.exception("Test execution failed")
        sys.exit(1)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during test execution")
        sys.exit(1)
