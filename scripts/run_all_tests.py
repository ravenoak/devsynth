#!/usr/bin/env python3
"""
Script to execute all unit, integration, and behavior tests for DevSynth.

This script runs all tests and generates a comprehensive report of the results.
It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/run_all_tests.py [--unit] [--integration] [--behavior] [--all]
                                   [--fast] [--medium] [--slow]

Options:
    --unit        Run only unit tests
    --integration Run only integration tests
    --behavior    Run only behavior tests
    --all         Run all tests (default)
    --fast        Run only fast tests (execution time < 1s)
    --medium      Run only medium tests (execution time between 1s and 5s)
    --slow        Run only slow tests (execution time > 5s)
    --report      Generate HTML report
    --verbose     Show verbose output
    --no-parallel Disable parallel test execution
    --segment     Run tests in smaller batches to improve performance
    --segment-size SIZE  Number of tests per batch when using --segment (default: 50)
"""

import argparse
import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Cache directory for test collection
COLLECTION_CACHE_DIR = ".test_collection_cache"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run DevSynth tests")
    
    # Test type group
    type_group = parser.add_argument_group("Test Type")
    type_group.add_argument("--unit", action="store_true", help="Run only unit tests")
    type_group.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    type_group.add_argument(
        "--behavior", action="store_true", help="Run only behavior tests"
    )
    type_group.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    # Speed category group
    speed_group = parser.add_argument_group("Speed Category")
    speed_group.add_argument(
        "--fast", action="store_true", help="Run only fast tests (execution time < 1s)"
    )
    speed_group.add_argument(
        "--medium", action="store_true", 
        help="Run only medium tests (execution time between 1s and 5s)"
    )
    speed_group.add_argument(
        "--slow", action="store_true", help="Run only slow tests (execution time > 5s)"
    )
    
    # Output options
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    
    # Performance options
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel test execution"
    )
    parser.add_argument(
        "--segment", action="store_true", 
        help="Run tests in smaller batches to improve performance"
    )
    parser.add_argument(
        "--segment-size", type=int, default=50,
        help="Number of tests per batch when using --segment (default: 50)"
    )

    args = parser.parse_args()

    # If no test type is specified, run all tests
    if not (args.unit or args.integration or args.behavior or args.all):
        args.all = True
        
    # If no speed category is specified, run all speed categories
    if not (args.fast or args.medium or args.slow):
        args.fast = args.medium = args.slow = True

    return args


def collect_tests_with_cache(test_type, speed_category=None):
    """
    Collect tests of the specified type and speed category, using cache when available.

    Args:
        test_type (str): Type of tests to run ('unit', 'integration', 'behavior', or 'all')
        speed_category (str): Speed category to run ('fast', 'medium', 'slow')

    Returns:
        list: List of test paths
    """
    # Determine test path
    if test_type == "unit":
        test_path = "tests/unit/"
    elif test_type == "integration":
        test_path = "tests/integration/"
    elif test_type == "behavior":
        test_path = "tests/behavior/"
    elif test_type == "all":
        test_path = "tests/"
    
    # Create cache key
    cache_key = f"{test_type}_{speed_category or 'all'}"
    cache_file = os.path.join(COLLECTION_CACHE_DIR, f"{cache_key}_tests.json")
    
    # Check if we have a cached collection
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            
            # Use cache if it's less than 1 hour old
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                print(f"Using cached test collection for {test_type} tests ({speed_category or 'all'})")
                return cached_data["tests"]
        except (json.JSONDecodeError, KeyError):
            # Invalid cache, ignore and collect tests
            pass
    
    # Ensure cache directory exists
    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)
    
    # Collect tests using pytest
    collect_cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "--collect-only",
        "-q"
    ]
    
    # Special handling for behavior tests - don't filter by speed marker if they're not categorized yet
    if test_type == "behavior" and speed_category:
        # Check if there are any behavior tests with speed markers
        check_cmd = collect_cmd.copy() + ["-m", speed_category]
        check_result = subprocess.run(check_cmd, check=False, capture_output=True, text=True)
        
        # If no tests are found with the speed marker, collect all behavior tests
        if "no tests ran" in check_result.stdout or not check_result.stdout.strip():
            print(f"No behavior tests found with {speed_category} marker. Collecting all behavior tests...")
            # Don't add speed marker to collect command
        else:
            # Add speed marker to collect command
            collect_cmd.extend(["-m", speed_category])
    elif speed_category:
        # For unit and integration tests, use speed markers as normal
        collect_cmd.extend(["-m", speed_category])
    
    try:
        collect_result = subprocess.run(collect_cmd, check=False, capture_output=True, text=True)
        test_list = []
        
        # Parse the output to get the list of tests
        for line in collect_result.stdout.split('\n'):
            if line.startswith('tests/'):
                test_list.append(line.strip())
        
        # Cache the results
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "tests": test_list
        }
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        
        return test_list
    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def run_tests(test_type, speed_categories=None, verbose=False, report=False, 
             parallel=True, segment=False, segment_size=50):
    """
    Run tests of the specified type and speed categories.

    Args:
        test_type (str): Type of tests to run ('unit', 'integration', 'behavior', or 'all')
        speed_categories (list): List of speed categories to run ('fast', 'medium', 'slow')
        verbose (bool): Whether to show verbose output
        report (bool): Whether to generate an HTML report
        parallel (bool): Whether to run tests in parallel using pytest-xdist
        segment (bool): Whether to run tests in smaller batches
        segment_size (int): Number of tests per batch when using segmentation

    Returns:
        tuple: (success, output) where success is a boolean indicating if all tests passed
               and output is the command output
    """
    print(f"\n{'='*80}")
    print(f"Running {test_type} tests with speed categories: {speed_categories or 'all'}...")
    print(f"{'='*80}")

    # Base command
    base_cmd = [sys.executable, "-m", "pytest"]

    # Determine test path
    if test_type == "unit":
        test_path = "tests/unit/"
    elif test_type == "integration":
        test_path = "tests/integration/"
    elif test_type == "behavior":
        test_path = "tests/behavior/"
    elif test_type == "all":
        test_path = "tests/"
    
    # Add test path to base command
    base_cmd.append(test_path)

    # Add verbose flag if requested
    if verbose:
        base_cmd.append("-v")
        
    # Add parallel execution if requested
    if parallel:
        base_cmd.append("-n")
        base_cmd.append("auto")  # Use auto to determine the optimal number of processes

    # Add report options if requested
    report_options = []
    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path(f"test_reports/{timestamp}/{test_type}")
        report_dir.parent.mkdir(parents=True, exist_ok=True)

        # Add HTML report options
        report_options = [
            f"--html=test_reports/{timestamp}/{test_type}/report.html",
            "--self-contained-html",
        ]

    # If no speed categories specified, run all tests
    if not speed_categories:
        cmd = base_cmd + report_options
        
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
    
    # Run tests for each speed category
    all_success = True
    all_output = ""
    
    for speed in speed_categories:
        print(f"\nRunning {speed} tests...")
        
        # Special handling for behavior tests - don't filter by speed marker if they're not categorized yet
        if test_type == "behavior":
            # Check if there are any behavior tests with speed markers
            has_speed_markers = False
            check_cmd = base_cmd + ["-m", speed, "--collect-only", "-q"]
            check_result = subprocess.run(check_cmd, check=False, capture_output=True, text=True)
            
            # If no tests are found with the speed marker, run all behavior tests
            if "no tests ran" in check_result.stdout or not check_result.stdout.strip():
                print(f"No behavior tests found with {speed} marker. Running all behavior tests...")
                speed_cmd = base_cmd + report_options
            else:
                has_speed_markers = True
                speed_cmd = base_cmd + ["-m", speed] + report_options
        else:
            # For unit and integration tests, use speed markers as normal
            speed_cmd = base_cmd + ["-m", speed] + report_options
        
        if segment:
            # Collect tests with caching
            test_list = collect_tests_with_cache(test_type, speed)
            
            if not test_list:
                print(f"No {speed} tests found for {test_type}")
                continue
            
            print(f"Found {len(test_list)} {speed} tests, running in batches of {segment_size}...")
            
            # Run tests in batches
            batch_success = True
            for i in range(0, len(test_list), segment_size):
                batch = test_list[i:i+segment_size]
                print(f"\nRunning batch {i//segment_size + 1}/{(len(test_list) + segment_size - 1)//segment_size}...")
                
                # Create command for this batch
                batch_cmd = base_cmd + ["-m", speed] + batch + report_options
                
                # Run the batch
                batch_result = subprocess.run(batch_cmd, check=False, capture_output=True, text=True)
                print(batch_result.stdout)
                if batch_result.stderr:
                    print("ERRORS:")
                    print(batch_result.stderr)
                
                batch_success = batch_success and batch_result.returncode == 0
                all_output += batch_result.stdout + batch_result.stderr
            
            all_success = all_success and batch_success
        else:
            # Run all tests for this speed category at once
            try:
                result = subprocess.run(speed_cmd, check=False, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("ERRORS:")
                    print(result.stderr)
                
                all_success = all_success and result.returncode == 0
                all_output += result.stdout + result.stderr
            except Exception as e:
                print(f"Error running {speed} tests: {e}")
                all_success = False
                all_output += str(e)
    
    return all_success, all_output


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

    # Ensure pytest-xdist is installed if parallel execution is requested
    if not args.no_parallel:
        try:
            import xdist  # noqa: F401
        except ImportError:
            print(
                "pytest-xdist is required for parallel test execution. Please install development dependencies:"
            )
            print("  poetry install --with dev,docs --all-extras")
            return 1

    all_success = True
    results = {}

    # Determine if parallel execution should be used
    parallel = not args.no_parallel
    
    # Determine which speed categories to run
    speed_categories = []
    if args.fast:
        speed_categories.append("fast")
    if args.medium:
        speed_categories.append("medium")
    if args.slow:
        speed_categories.append("slow")
    
    # Print test execution plan
    print("\n" + "=" * 80)
    print("TEST EXECUTION PLAN")
    print("=" * 80)
    
    test_types = []
    if args.all:
        test_types.append("all")
    else:
        if args.unit:
            test_types.append("unit")
        if args.integration:
            test_types.append("integration")
        if args.behavior:
            test_types.append("behavior")
    
    print(f"Test Types: {', '.join(test_types)}")
    print(f"Speed Categories: {', '.join(speed_categories)}")
    print(f"Parallel Execution: {'Disabled' if args.no_parallel else 'Enabled'}")
    print(f"Test Segmentation: {'Enabled' if args.segment else 'Disabled'}")
    if args.segment:
        print(f"Segment Size: {args.segment_size}")
    print(f"Report Generation: {'Enabled' if args.report else 'Disabled'}")
    print(f"Verbose Output: {'Enabled' if args.verbose else 'Disabled'}")
    
    start_time = time.time()
    
    # Run the specified tests
    if args.all or args.unit:
        unit_success, unit_output = run_tests(
            "unit", 
            speed_categories, 
            args.verbose, 
            args.report, 
            parallel,
            args.segment,
            args.segment_size
        )
        all_success = all_success and unit_success
        results["unit"] = unit_success

    if args.all or args.integration:
        integration_success, integration_output = run_tests(
            "integration", 
            speed_categories, 
            args.verbose, 
            args.report, 
            parallel,
            args.segment,
            args.segment_size
        )
        all_success = all_success and integration_success
        results["integration"] = integration_success

    if args.all or args.behavior:
        behavior_success, behavior_output = run_tests(
            "behavior", 
            speed_categories, 
            args.verbose, 
            args.report, 
            parallel,
            args.segment,
            args.segment_size
        )
        all_success = all_success and behavior_success
        results["behavior"] = behavior_success

    end_time = time.time()
    execution_time = end_time - start_time
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_type, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_type.upper()} TESTS: {status}")

    print("\nOVERALL STATUS:", "PASSED" if all_success else "FAILED")
    print(f"EXECUTION TIME: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)")

    if args.report:
        print(
            f"\nTest reports generated in test_reports/{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
        )

    # Print tips for faster test execution
    if execution_time > 60:  # If tests took more than a minute
        print("\nTips for faster test execution:")
        if not args.fast and not args.medium:
            print("- Run only fast tests during development: --fast")
        if not args.segment:
            print("- Enable test segmentation: --segment")
        if args.all:
            print("- Run only specific test types: --unit, --integration, or --behavior")
        if not parallel:
            print("- Enable parallel execution (if disabled): remove --no-parallel")

    # Return appropriate exit code
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
