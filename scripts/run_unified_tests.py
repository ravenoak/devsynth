#!/usr/bin/env python3
"""
Unified Test Execution Workflow

This script provides a unified interface for running tests with optimal performance.
It combines the functionality of various test scripts to provide a comprehensive
solution for test execution, including:

- Incremental testing (run only tests affected by recent changes)
- Balanced distribution (distribute tests evenly across processes)
- Test prioritization (run tests most likely to fail first)
- Test categorization (run tests based on speed markers)
- Test filtering (run tests matching specific patterns)

Usage:
    python scripts/run_unified_tests.py [options]

Options:
    --mode MODE           Test execution mode (default: incremental)
                          Available modes: incremental, balanced, all, fast, critical
    --base COMMIT         Base commit to compare against for incremental mode (default: HEAD~1)
    --test-dir DIR        Directory containing tests (default: tests)
    --category CAT        Only run tests in the specified category (default: all)
                          Available categories: unit, integration, behavior, all
    --speed SPEED         Only run tests with the specified speed marker (default: all)
                          Available speeds: fast, medium, slow, all
    --pattern PATTERN     Only run tests matching the specified pattern
    --prioritize          Prioritize tests based on failure history
    --parallel            Run tests in parallel
    --processes N         Number of processes to use for parallel execution (default: auto)
    --report              Generate HTML report
    --verbose             Show detailed output
    --dry-run             Show what would be run without executing tests
    --max-tests N         Maximum number of tests to run (default: all)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import test utilities
try:
    from . import common_test_collector, test_utils, test_utils_extended

    EXTENDED_UTILS_AVAILABLE = True
except ImportError:
    print("Warning: test_utils_extended.py not found. Using original implementation.")
    from . import common_test_collector, test_utils

    EXTENDED_UTILS_AVAILABLE = False

# Test execution modes
MODES = {
    "incremental": {
        "description": "Run only tests affected by recent changes",
        "script": "scripts/run_incremental_tests_enhanced.py",
        "preset": "recent",
        "default_args": ["--prioritize", "--balanced"],
    },
    "balanced": {
        "description": "Run tests with balanced distribution across processes",
        "script": "scripts/run_balanced_tests.py",
        "default_args": [],
    },
    "all": {"description": "Run all tests", "script": "pytest", "default_args": []},
    "fast": {
        "description": "Run only fast tests for quick feedback",
        "script": "scripts/run_incremental_tests_enhanced.py",
        "preset": "fast",
        "default_args": ["--prioritize", "--balanced"],
    },
    "critical": {
        "description": "Run tests most likely to fail based on history",
        "script": "scripts/prioritize_high_risk_tests.py",
        "default_args": ["--max-tests", "100"],
    },
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unified test execution workflow.")
    parser.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="incremental",
        help="Test execution mode (default: incremental)",
    )
    parser.add_argument(
        "--base",
        default="HEAD~1",
        help="Base commit to compare against for incremental mode (default: HEAD~1)",
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests (default: tests)",
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="all",
        help="Only run tests in the specified category (default: all)",
    )
    parser.add_argument(
        "--speed",
        choices=["fast", "medium", "slow", "all"],
        default="all",
        help="Only run tests with the specified speed marker (default: all)",
    )
    parser.add_argument(
        "--pattern", help="Only run tests matching the specified pattern"
    )
    parser.add_argument(
        "--prioritize",
        action="store_true",
        help="Prioritize tests based on failure history",
    )
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument(
        "--processes",
        type=int,
        default=0,
        help="Number of processes to use for parallel execution (default: auto)",
    )
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing tests",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=0,
        help="Maximum number of tests to run (default: all)",
    )
    return parser.parse_args()


def check_dependencies():
    """
    Check if all required dependencies are available.

    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    # Check for required scripts
    required_scripts = {
        "scripts/run_incremental_tests_enhanced.py": "Enhanced incremental tests runner",
        "scripts/run_balanced_tests.py": "Balanced test distribution",
        "scripts/prioritize_high_risk_tests.py": "Test prioritization",
    }

    missing_scripts = []
    for script, description in required_scripts.items():
        if not os.path.exists(script):
            missing_scripts.append(f"{script} ({description})")

    if missing_scripts:
        print("Warning: The following required scripts are missing:")
        for script in missing_scripts:
            print(f"  - {script}")
        print("Some functionality may be limited.")

    # Check for pytest
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print("Error: pytest is not installed or not working properly.")
        return False

    return True


def build_command(args):
    """
    Build the command to run tests based on the specified mode and options.

    Args:
        args: Command line arguments

    Returns:
        list: Command to run as a list of strings
    """
    mode = MODES[args.mode]
    script = mode["script"]

    # Start with the base command
    if script.startswith("scripts/"):
        cmd = [sys.executable, script]
    else:
        cmd = [sys.executable, "-m", script]
    if script == "pytest":
        cmd.append("--maxfail=1")

    # Add default arguments for the mode
    cmd.extend(mode.get("default_args", []))

    # Add preset if specified for the mode
    if "preset" in mode:
        cmd.extend(["--preset", mode["preset"]])

    # Add common arguments based on command-line options
    if args.mode == "incremental":
        # Arguments specific to incremental mode
        if args.base != "HEAD~1":
            cmd.extend(["--base", args.base])

    if args.mode == "balanced" or args.mode == "all":
        # Arguments for balanced and all modes
        if args.category != "all":
            cmd.extend(["--category", args.category])

        if args.speed != "all":
            cmd.extend(["--speed", args.speed])

    if args.pattern and args.mode == "all":
        # Add pattern for pytest
        cmd.extend(["-k", args.pattern])

    if args.prioritize and args.mode not in ["incremental", "fast", "critical"]:
        # Add prioritize flag (already included in incremental, fast, and critical modes)
        cmd.append("--prioritize")

    if args.parallel:
        # Add parallel flag
        cmd.append("--parallel")

        # Add processes if specified
        if args.processes > 0 and args.mode in ["balanced", "all"]:
            cmd.extend(["--processes", str(args.processes)])

    if args.report:
        # Add report flag
        cmd.append("--report")

    if args.verbose:
        # Add verbose flag
        cmd.append("--verbose")

    if args.max_tests > 0 and args.mode not in ["critical"]:
        # Add max-tests flag (already included in critical mode)
        cmd.extend(["--max-tests", str(args.max_tests)])

    return cmd


def log_run(cmd, mode, description):
    """
    Log the test run to a history file.

    Args:
        cmd: Command that was run
        mode: Test execution mode
        description: Description of the mode
    """
    history_dir = ".test_history"
    os.makedirs(history_dir, exist_ok=True)

    history_file = os.path.join(history_dir, "unified_test_runs.json")

    # Load existing history
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
        except json.JSONDecodeError:
            # Invalid file, start with empty history
            pass

    # Add new entry
    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(cmd),
            "mode": mode,
            "description": description,
        }
    )

    # Keep only the last 100 entries
    if len(history) > 100:
        history = history[-100:]

    # Save history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def print_test_statistics():
    """Print statistics about test categorization and markers."""
    if not EXTENDED_UTILS_AVAILABLE:
        print(
            "Warning: test_utils_extended.py not found. Cannot display test statistics."
        )
        return

    print("\nTest Statistics:")
    print("-" * 50)

    # Get marker counts
    marker_counts = common_test_collector.get_marker_counts()

    # Get total test counts
    test_counts = common_test_collector.get_test_counts()

    # Calculate percentages
    total_tests = test_counts.get("total", 0)
    if total_tests > 0:
        fast_percent = marker_counts["total"]["fast"] / total_tests * 100
        medium_percent = marker_counts["total"]["medium"] / total_tests * 100
        slow_percent = marker_counts["total"]["slow"] / total_tests * 100
        total_with_markers = (
            marker_counts["total"]["fast"]
            + marker_counts["total"]["medium"]
            + marker_counts["total"]["slow"]
        )
        total_percent = total_with_markers / total_tests * 100

        print(f"Total tests: {total_tests}")
        print(f"Tests with markers: {total_with_markers} ({total_percent:.2f}%)")
        print(f"  - Fast tests: {marker_counts['total']['fast']} ({fast_percent:.2f}%)")
        print(
            f"  - Medium tests: {marker_counts['total']['medium']} ({medium_percent:.2f}%)"
        )
        print(f"  - Slow tests: {marker_counts['total']['slow']} ({slow_percent:.2f}%)")

    # Get failure rates if available
    if hasattr(common_test_collector, "get_test_failure_rates"):
        failure_rates = common_test_collector.get_test_failure_rates()
        frequently_failing = common_test_collector.get_frequently_failing_tests()

        if frequently_failing:
            print("\nFrequently failing tests:")
            for test, rate in sorted(
                frequently_failing.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                print(f"  - {test}: {rate*100:.1f}% failure rate")


def main():
    """Main function."""
    args = parse_args()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Print test statistics
    if not args.dry_run:
        print_test_statistics()

    # Build the command
    cmd = build_command(args)

    # Print the command
    print(f"\nRunning: {' '.join(cmd)}")
    print(f"Mode: {args.mode} - {MODES[args.mode]['description']}")

    # Execute the command if not a dry run
    if not args.dry_run:
        try:
            # Log the run
            log_run(cmd, args.mode, MODES[args.mode]["description"])

            # Execute the command
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running tests: {e}")
            sys.exit(1)
    else:
        print("Dry run - not executing tests")


if __name__ == "__main__":
    main()
