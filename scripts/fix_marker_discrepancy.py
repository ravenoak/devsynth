#!/usr/bin/env python
"""
Script to fix marker discrepancy between apply_speed_markers.py and common_test_collector.py.

This script orchestrates the execution of standardize_marker_placement.py and
verify_marker_detection.py to resolve the discrepancy in marker counts. It:

1. Runs standardize_marker_placement.py to ensure consistent marker placement
2. Runs verify_marker_detection.py to check if the discrepancy is resolved
3. If discrepancies remain, it attempts to fix them
4. Generates a comprehensive report of the results

Usage:
    python scripts/fix_marker_discrepancy.py [options]

Options:
    --dry-run             Show changes without modifying files
    --verbose             Show verbose output
    --report-file FILE    Save the report to the specified file (default: marker_discrepancy_report.json)
    --max-iterations N    Maximum number of iterations to attempt fixes (default: 3)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix marker discrepancy between apply_speed_markers.py and common_test_collector.py."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--report-file",
        type=str,
        default="marker_discrepancy_report.json",
        help="Save the report to the specified file",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of iterations to attempt fixes",
    )
    return parser.parse_args()


def run_standardize_markers(
    dry_run: bool = False, verbose: bool = False
) -> tuple[bool, dict[str, Any]]:
    """
    Run standardize_marker_placement.py to ensure consistent marker placement.

    Args:
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show verbose output

    Returns:
        Tuple containing:
        - Whether the script ran successfully
        - Dictionary containing the script output
    """
    print("\n=== Running standardize_marker_placement.py ===")

    cmd = [sys.executable, "scripts/standardize_marker_placement.py"]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = time.time()

        # Parse the output to extract key information
        output = result.stdout

        # Extract the number of standardized markers and modified files
        standardized_markers = 0
        modified_files = 0

        for line in output.split("\n"):
            if "standardize" in line.lower() and "markers in" in line.lower():
                parts = line.split()
                try:
                    standardized_markers = int(parts[1])
                    modified_files = int(parts[3])
                except (IndexError, ValueError):
                    pass

        return True, {
            "success": True,
            "standardized_markers": standardized_markers,
            "modified_files": modified_files,
            "execution_time": end_time - start_time,
            "output": output,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error running standardize_marker_placement.py: {e}")
        return False, {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


def run_verify_markers(
    fix: bool = False,
    verbose: bool = False,
    report_file: str = "marker_detection_report.json",
) -> tuple[bool, dict[str, Any]]:
    """
    Run verify_marker_detection.py to check if the discrepancy is resolved.

    Args:
        fix: Whether to attempt to fix any discrepancies found
        verbose: Whether to show verbose output
        report_file: Path to save the verification report

    Returns:
        Tuple containing:
        - Whether the script ran successfully
        - Dictionary containing the script output and verification results
    """
    print("\n=== Running verify_marker_detection.py ===")

    cmd = [
        sys.executable,
        "scripts/verify_marker_detection.py",
        f"--report-file={report_file}",
    ]
    if fix:
        cmd.append("--fix")
    if verbose:
        cmd.append("--verbose")

    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = time.time()

        # Load the verification report
        verification_report = {}
        if os.path.exists(report_file):
            try:
                with open(report_file) as f:
                    verification_report = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading verification report: {e}")

        # Extract discrepancy information
        discrepancies = verification_report.get("discrepancies", {})
        total_difference = discrepancies.get("total_difference", 0)

        return True, {
            "success": True,
            "execution_time": end_time - start_time,
            "output": result.stdout,
            "verification_report": verification_report,
            "total_difference": total_difference,
            "discrepancies_resolved": total_difference == 0,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error running verify_marker_detection.py: {e}")
        return False, {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


def run_apply_speed_markers(
    dry_run: bool = True, verbose: bool = False
) -> tuple[bool, dict[str, Any]]:
    """
    Run apply_speed_markers.py to generate a fresh marker report.

    Args:
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show verbose output

    Returns:
        Tuple containing:
        - Whether the script ran successfully
        - Dictionary containing the script output
    """
    print("\n=== Running apply_speed_markers.py ===")

    cmd = [sys.executable, "scripts/apply_speed_markers.py"]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = time.time()

        # Load the marker report
        marker_report = {}
        report_path = "test_markers_report.json"
        if os.path.exists(report_path):
            try:
                with open(report_path) as f:
                    marker_report = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading marker report: {e}")

        return True, {
            "success": True,
            "execution_time": end_time - start_time,
            "output": result.stdout,
            "marker_report": marker_report,
        }
    except subprocess.CalledProcessError as e:
        print(f"Error running apply_speed_markers.py: {e}")
        return False, {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


def main():
    """Main function."""
    args = parse_args()

    print("=== Starting Marker Discrepancy Fix Process ===")
    print(f"Dry run: {args.dry_run}")
    print(f"Verbose: {args.verbose}")
    print(f"Report file: {args.report_file}")
    print(f"Max iterations: {args.max_iterations}")

    # Initialize the report
    report = {"timestamp": time.time(), "args": vars(args), "iterations": []}

    # Run the initial standardization
    standardize_success, standardize_result = run_standardize_markers(
        args.dry_run, args.verbose
    )

    if not standardize_success:
        print("Error: Failed to run standardize_marker_placement.py. Aborting.")
        report["error"] = "Failed to run standardize_marker_placement.py"
        report["standardize_result"] = standardize_result

        with open(args.report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to {args.report_file}")
        return

    # Run the initial verification
    verify_success, verify_result = run_verify_markers(
        False, args.verbose, "marker_detection_report.json"
    )

    if not verify_success:
        print("Error: Failed to run verify_marker_detection.py. Aborting.")
        report["error"] = "Failed to run verify_marker_detection.py"
        report["standardize_result"] = standardize_result
        report["verify_result"] = verify_result

        with open(args.report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to {args.report_file}")
        return

    # Add the initial results to the report
    report["iterations"].append(
        {
            "iteration": 1,
            "standardize_result": standardize_result,
            "verify_result": verify_result,
        }
    )

    # Check if discrepancies are resolved
    if verify_result.get("discrepancies_resolved", False):
        print("\n=== Discrepancies Resolved! ===")
        report["status"] = "resolved"
        report["total_iterations"] = 1
    else:
        print("\n=== Discrepancies Remain ===")

        # Attempt to fix discrepancies
        iteration = 2
        while iteration <= args.max_iterations:
            print(f"\n=== Iteration {iteration} ===")

            # Run verification with fix option
            if not args.dry_run:
                verify_success, verify_result = run_verify_markers(
                    True, args.verbose, f"marker_detection_report_{iteration}.json"
                )
            else:
                print("Skipping fix attempt in dry run mode")
                verify_success, verify_result = run_verify_markers(
                    False, args.verbose, f"marker_detection_report_{iteration}.json"
                )

            if not verify_success:
                print(
                    f"Error: Failed to run verify_marker_detection.py in iteration {iteration}. Aborting."
                )
                report["error"] = (
                    f"Failed to run verify_marker_detection.py in iteration {iteration}"
                )
                break

            # Run standardization again
            standardize_success, standardize_result = run_standardize_markers(
                args.dry_run, args.verbose
            )

            if not standardize_success:
                print(
                    f"Error: Failed to run standardize_marker_placement.py in iteration {iteration}. Aborting."
                )
                report["error"] = (
                    f"Failed to run standardize_marker_placement.py in iteration {iteration}"
                )
                break

            # Run verification again to check if discrepancies are resolved
            verify_success, verify_result = run_verify_markers(
                False, args.verbose, f"marker_detection_report_{iteration}_after.json"
            )

            if not verify_success:
                print(
                    f"Error: Failed to run verify_marker_detection.py after fix in iteration {iteration}. Aborting."
                )
                report["error"] = (
                    f"Failed to run verify_marker_detection.py after fix in iteration {iteration}"
                )
                break

            # Add the iteration results to the report
            report["iterations"].append(
                {
                    "iteration": iteration,
                    "standardize_result": standardize_result,
                    "verify_result": verify_result,
                }
            )

            # Check if discrepancies are resolved
            if verify_result.get("discrepancies_resolved", False):
                print(f"\n=== Discrepancies Resolved in Iteration {iteration}! ===")
                report["status"] = "resolved"
                report["total_iterations"] = iteration
                break

            iteration += 1

        # Check if we reached the maximum iterations without resolving discrepancies
        if iteration > args.max_iterations and not verify_result.get(
            "discrepancies_resolved", False
        ):
            print(
                f"\n=== Failed to Resolve Discrepancies After {args.max_iterations} Iterations ==="
            )
            report["status"] = "unresolved"
            report["total_iterations"] = args.max_iterations

    # Run apply_speed_markers.py to generate a fresh marker report
    apply_success, apply_result = run_apply_speed_markers(True, args.verbose)

    if apply_success:
        report["apply_result"] = apply_result

    # Save the report
    with open(args.report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to {args.report_file}")

    # Print summary
    print("\n=== Summary ===")
    print(f"Status: {report.get('status', 'unknown')}")
    print(f"Total iterations: {report.get('total_iterations', 0)}")

    if report.get("status") == "resolved":
        print("\nDiscrepancies have been resolved!")

        # Print marker counts
        if "apply_result" in report and "marker_report" in report["apply_result"]:
            marker_report = report["apply_result"]["marker_report"]
            print(f"\nMarker counts:")
            print(f"  Fast tests: {marker_report.get('fast_tests', 0)}")
            print(f"  Medium tests: {marker_report.get('medium_tests', 0)}")
            print(f"  Slow tests: {marker_report.get('slow_tests', 0)}")
            print(
                f"  Total: {marker_report.get('fast_tests', 0) + marker_report.get('medium_tests', 0) + marker_report.get('slow_tests', 0)}"
            )
    else:
        print("\nDiscrepancies could not be fully resolved.")
        print("Please check the report for details and consider manual intervention.")


if __name__ == "__main__":
    main()
