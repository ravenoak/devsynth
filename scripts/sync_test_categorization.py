#!/usr/bin/env python
"""
Script to synchronize test categorization tracking between progress and schedule files.

This script reconciles discrepancies between the progress file (.test_categorization_progress.json)
and schedule file (.test_categorization_schedule.json) to ensure consistent test counts
across all tools and documentation.

Usage:
    python scripts/sync_test_categorization.py [options]

Options:
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information about changes
    --update-schedule     Update schedule file based on progress file
    --update-progress     Update progress file based on actual markers in code
    --verify              Verify consistency between progress file, schedule file, and actual markers
    --report              Generate a report of discrepancies
"""

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector and enhanced test utilities
from . import common_test_collector as test_collector
from . import test_utils_extended as test_utils_ext


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Synchronize test categorization tracking between progress and schedule files."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information about changes"
    )
    parser.add_argument(
        "--update-schedule",
        action="store_true",
        help="Update schedule file based on progress file",
    )
    parser.add_argument(
        "--update-progress",
        action="store_true",
        help="Update progress file based on actual markers in code",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify consistency between progress file, schedule file, and actual markers",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a report of discrepancies"
    )
    parser.add_argument(
        "--report-file",
        default="test_categorization_sync_report.json",
        help="File to save the report to",
    )
    return parser.parse_args()


def update_schedule_from_progress(
    dry_run: bool = False, verbose: bool = False
) -> dict[str, Any]:
    """
    Update the schedule file based on the progress file.

    Args:
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about changes

    Returns:
        Dictionary containing update results
    """
    print("Updating schedule file from progress file...")

    # Load progress and schedule files
    progress = test_utils_ext.load_progress_file()
    schedule = test_utils_ext.load_schedule_file()

    if not progress or not schedule:
        print("Cannot update: missing progress or schedule file")
        return {"success": False, "error": "Missing progress or schedule file"}

    # Extract categorized tests from progress file
    progress_categorized = progress.get("categorized_tests", {})
    progress_counts = progress.get(
        "categorization_counts", {"fast": 0, "medium": 0, "slow": 0, "total": 0}
    )

    # Extract module test counts from schedule file
    schedule_module_counts = schedule.get("module_test_counts", {})

    # Collect all tests by module using the common test collector
    all_tests_by_module = {}
    for category in test_collector.TEST_CATEGORIES:
        category_tests = test_collector.collect_tests_by_category(category)

        for test_path in category_tests:
            # Extract the module path from the test path
            if "::" in test_path:
                module_path = test_path.split("::")[0]
                # Get the directory containing the file
                module_path = os.path.dirname(module_path)
            else:
                module_path = os.path.dirname(test_path)

            if module_path not in all_tests_by_module:
                all_tests_by_module[module_path] = []
            all_tests_by_module[module_path].append(test_path)

    # Update module test counts in schedule file
    changes = {
        "modules_updated": 0,
        "modules_added": 0,
        "modules_unchanged": 0,
        "total_tests_before": schedule.get("total_tests", 0),
        "total_categorized_before": schedule.get("total_categorized", 0),
        "total_uncategorized_before": schedule.get("total_uncategorized", 0),
    }

    for module_path, tests in all_tests_by_module.items():
        total_tests = len(tests)
        categorized_count = sum(1 for test in tests if test in progress_categorized)
        uncategorized_count = total_tests - categorized_count

        if module_path in schedule_module_counts:
            old_counts = schedule_module_counts[module_path]
            if (
                old_counts.get("total", 0) != total_tests
                or old_counts.get("categorized", 0) != categorized_count
                or old_counts.get("uncategorized", 0) != uncategorized_count
            ):

                if verbose:
                    print(f"Updating module {module_path}:")
                    print(
                        f"  Total tests: {old_counts.get('total', 0)} -> {total_tests}"
                    )
                    print(
                        f"  Categorized: {old_counts.get('categorized', 0)} -> {categorized_count}"
                    )
                    print(
                        f"  Uncategorized: {old_counts.get('uncategorized', 0)} -> {uncategorized_count}"
                    )

                if not dry_run:
                    schedule_module_counts[module_path] = {
                        "total": total_tests,
                        "categorized": categorized_count,
                        "uncategorized": uncategorized_count,
                    }

                changes["modules_updated"] += 1
            else:
                changes["modules_unchanged"] += 1
        elif uncategorized_count > 0:
            # Add new module to schedule
            if verbose:
                print(f"Adding module {module_path}:")
                print(f"  Total tests: {total_tests}")
                print(f"  Categorized: {categorized_count}")
                print(f"  Uncategorized: {uncategorized_count}")

            if not dry_run:
                schedule_module_counts[module_path] = {
                    "total": total_tests,
                    "categorized": categorized_count,
                    "uncategorized": uncategorized_count,
                }

            changes["modules_added"] += 1

    # Update total counts in schedule file
    total_tests = sum(len(tests) for tests in all_tests_by_module.values())
    total_categorized = len(progress_categorized)
    total_uncategorized = total_tests - total_categorized

    if verbose:
        print(f"Updating total counts:")
        print(f"  Total tests: {schedule.get('total_tests', 0)} -> {total_tests}")
        print(
            f"  Categorized: {schedule.get('total_categorized', 0)} -> {total_categorized}"
        )
        print(
            f"  Uncategorized: {schedule.get('total_uncategorized', 0)} -> {total_uncategorized}"
        )

    if not dry_run:
        schedule["total_tests"] = total_tests
        schedule["total_categorized"] = total_categorized
        schedule["total_uncategorized"] = total_uncategorized
        schedule["module_test_counts"] = schedule_module_counts

        # Save updated schedule file
        test_utils_ext.save_schedule_file(schedule)

    changes["total_tests_after"] = total_tests
    changes["total_categorized_after"] = total_categorized
    changes["total_uncategorized_after"] = total_uncategorized

    return {"success": True, "changes": changes}


def update_progress_from_code(
    dry_run: bool = False, verbose: bool = False
) -> dict[str, Any]:
    """
    Update the progress file based on actual markers in code.

    Args:
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information about changes

    Returns:
        Dictionary containing update results
    """
    print("Updating progress file from actual markers in code...")

    # Load progress file
    progress = test_utils_ext.load_progress_file()

    if not progress:
        print("Cannot update: missing progress file")
        return {"success": False, "error": "Missing progress file"}

    # Extract categorized tests from progress file
    progress_categorized = progress.get("categorized_tests", {})

    # Collect all tests using the common test collector
    all_tests = test_collector.collect_tests()

    # Check actual markers in code using the common test collector
    code_markers = {}
    for test_path in all_tests:
        has_marker, marker_type = test_collector.check_test_has_marker(test_path)
        if has_marker and marker_type in ["fast", "medium", "slow"]:
            code_markers[test_path] = marker_type

    # Compare with progress file
    changes = {
        "tests_added": 0,
        "tests_updated": 0,
        "tests_removed": 0,
        "tests_unchanged": 0,
        "total_before": len(progress_categorized),
        "fast_before": sum(
            1 for marker in progress_categorized.values() if marker == "fast"
        ),
        "medium_before": sum(
            1 for marker in progress_categorized.values() if marker == "medium"
        ),
        "slow_before": sum(
            1 for marker in progress_categorized.values() if marker == "slow"
        ),
    }

    # Add or update tests with markers in code
    for test_path, marker in code_markers.items():
        if test_path not in progress_categorized:
            if verbose:
                print(f"Adding test {test_path} with marker {marker}")

            if not dry_run:
                progress_categorized[test_path] = marker

            changes["tests_added"] += 1
        elif progress_categorized[test_path] != marker:
            if verbose:
                print(
                    f"Updating test {test_path} from {progress_categorized[test_path]} to {marker}"
                )

            if not dry_run:
                progress_categorized[test_path] = marker

            changes["tests_updated"] += 1
        else:
            changes["tests_unchanged"] += 1

    # Remove tests without markers in code
    tests_to_remove = []
    for test_path in progress_categorized:
        if test_path not in code_markers:
            if verbose:
                print(
                    f"Removing test {test_path} with marker {progress_categorized[test_path]}"
                )

            tests_to_remove.append(test_path)
            changes["tests_removed"] += 1

    if not dry_run:
        for test_path in tests_to_remove:
            del progress_categorized[test_path]

    # Update progress file
    if not dry_run:
        progress["categorized_tests"] = progress_categorized

        # Update counts
        fast_count = sum(
            1 for marker in progress_categorized.values() if marker == "fast"
        )
        medium_count = sum(
            1 for marker in progress_categorized.values() if marker == "medium"
        )
        slow_count = sum(
            1 for marker in progress_categorized.values() if marker == "slow"
        )
        total_count = len(progress_categorized)

        progress["categorization_counts"] = {
            "fast": fast_count,
            "medium": medium_count,
            "slow": slow_count,
            "total": total_count,
        }

        # Save updated progress file
        test_utils_ext.save_progress_file(progress)

    changes["total_after"] = len(progress_categorized)
    changes["fast_after"] = sum(
        1 for marker in progress_categorized.values() if marker == "fast"
    )
    changes["medium_after"] = sum(
        1 for marker in progress_categorized.values() if marker == "medium"
    )
    changes["slow_after"] = sum(
        1 for marker in progress_categorized.values() if marker == "slow"
    )

    return {"success": True, "changes": changes}


def verify_consistency(verbose: bool = False) -> dict[str, Any]:
    """
    Verify consistency between progress file, schedule file, and actual markers in code.

    Args:
        verbose: Whether to show detailed information about discrepancies

    Returns:
        Dictionary containing verification results
    """
    print(
        "Verifying consistency between progress file, schedule file, and actual markers in code..."
    )

    # Load progress and schedule files
    progress = test_utils_ext.load_progress_file()
    schedule = test_utils_ext.load_schedule_file()

    if not progress or not schedule:
        print("Cannot verify: missing progress or schedule file")
        return {"success": False, "error": "Missing progress or schedule file"}

    # Extract categorized tests from progress file
    progress_categorized = progress.get("categorized_tests", {})
    progress_counts = progress.get(
        "categorization_counts", {"fast": 0, "medium": 0, "slow": 0, "total": 0}
    )

    # Extract total counts from schedule file
    schedule_total = schedule.get("total_tests", 0)
    schedule_categorized = schedule.get("total_categorized", 0)
    schedule_uncategorized = schedule.get("total_uncategorized", 0)

    # Collect all tests using the common test collector
    all_tests = test_collector.collect_tests()

    # Check actual markers in code using the common test collector
    code_markers = {}
    for test_path in all_tests:
        has_marker, marker_type = test_collector.check_test_has_marker(test_path)
        if has_marker and marker_type in ["fast", "medium", "slow"]:
            code_markers[test_path] = marker_type

    # Calculate actual counts
    actual_total = len(all_tests)
    actual_categorized = len(code_markers)
    actual_uncategorized = actual_total - actual_categorized

    # Verify progress file counts
    progress_fast = sum(
        1 for marker in progress_categorized.values() if marker == "fast"
    )
    progress_medium = sum(
        1 for marker in progress_categorized.values() if marker == "medium"
    )
    progress_slow = sum(
        1 for marker in progress_categorized.values() if marker == "slow"
    )
    progress_total = len(progress_categorized)

    # Verify code marker counts
    code_fast = sum(1 for marker in code_markers.values() if marker == "fast")
    code_medium = sum(1 for marker in code_markers.values() if marker == "medium")
    code_slow = sum(1 for marker in code_markers.values() if marker == "slow")

    # Check for discrepancies
    discrepancies = {
        "progress_vs_code": {
            "tests_in_progress_not_in_code": [],
            "tests_in_code_not_in_progress": [],
            "tests_with_different_markers": [],
        },
        "progress_vs_counts": {
            "fast": progress_counts.get("fast", 0) != progress_fast,
            "medium": progress_counts.get("medium", 0) != progress_medium,
            "slow": progress_counts.get("slow", 0) != progress_slow,
            "total": progress_counts.get("total", 0) != progress_total,
        },
        "schedule_vs_actual": {
            "total": schedule_total != actual_total,
            "categorized": schedule_categorized != actual_categorized,
            "uncategorized": schedule_uncategorized != actual_uncategorized,
        },
    }

    # Find tests in progress file but not in code
    for test_path in progress_categorized:
        if test_path not in code_markers:
            discrepancies["progress_vs_code"]["tests_in_progress_not_in_code"].append(
                test_path
            )

    # Find tests in code but not in progress file
    for test_path in code_markers:
        if test_path not in progress_categorized:
            discrepancies["progress_vs_code"]["tests_in_code_not_in_progress"].append(
                test_path
            )

    # Find tests with different markers
    for test_path in progress_categorized:
        if (
            test_path in code_markers
            and progress_categorized[test_path] != code_markers[test_path]
        ):
            discrepancies["progress_vs_code"]["tests_with_different_markers"].append(
                {
                    "test_path": test_path,
                    "progress_marker": progress_categorized[test_path],
                    "code_marker": code_markers[test_path],
                }
            )

    # Print discrepancies if verbose
    if verbose:
        print("\nDiscrepancies between progress file and code:")
        print(
            f"  Tests in progress file but not in code: {len(discrepancies['progress_vs_code']['tests_in_progress_not_in_code'])}"
        )
        print(
            f"  Tests in code but not in progress file: {len(discrepancies['progress_vs_code']['tests_in_code_not_in_progress'])}"
        )
        print(
            f"  Tests with different markers: {len(discrepancies['progress_vs_code']['tests_with_different_markers'])}"
        )

        print("\nDiscrepancies in progress file counts:")
        print(
            f"  Fast: {progress_counts.get('fast', 0)} (reported) vs {progress_fast} (actual)"
        )
        print(
            f"  Medium: {progress_counts.get('medium', 0)} (reported) vs {progress_medium} (actual)"
        )
        print(
            f"  Slow: {progress_counts.get('slow', 0)} (reported) vs {progress_slow} (actual)"
        )
        print(
            f"  Total: {progress_counts.get('total', 0)} (reported) vs {progress_total} (actual)"
        )

        print("\nDiscrepancies in schedule file counts:")
        print(f"  Total: {schedule_total} (schedule) vs {actual_total} (actual)")
        print(
            f"  Categorized: {schedule_categorized} (schedule) vs {actual_categorized} (actual)"
        )
        print(
            f"  Uncategorized: {schedule_uncategorized} (schedule) vs {actual_uncategorized} (actual)"
        )

    return {
        "success": True,
        "actual_counts": {
            "total": actual_total,
            "categorized": actual_categorized,
            "uncategorized": actual_uncategorized,
            "fast": code_fast,
            "medium": code_medium,
            "slow": code_slow,
        },
        "progress_counts": {
            "total": progress_total,
            "fast": progress_fast,
            "medium": progress_medium,
            "slow": progress_slow,
            "reported_total": progress_counts.get("total", 0),
            "reported_fast": progress_counts.get("fast", 0),
            "reported_medium": progress_counts.get("medium", 0),
            "reported_slow": progress_counts.get("slow", 0),
        },
        "schedule_counts": {
            "total": schedule_total,
            "categorized": schedule_categorized,
            "uncategorized": schedule_uncategorized,
        },
        "discrepancies": discrepancies,
    }


def generate_report(results: dict[str, Any], report_file: str) -> None:
    """
    Generate a report of discrepancies.

    Args:
        results: Dictionary containing verification results
        report_file: File to save the report to
    """
    print(f"Generating report to {report_file}...")

    # Add timestamp to results
    results["timestamp"] = datetime.now().isoformat()

    # Save report
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Report saved to {report_file}")


def main():
    """Main function."""
    args = parse_args()

    results = {}

    if args.update_schedule:
        results["update_schedule"] = update_schedule_from_progress(
            args.dry_run, args.verbose
        )

    if args.update_progress:
        results["update_progress"] = update_progress_from_code(
            args.dry_run, args.verbose
        )

    if args.verify or args.report:
        results["verify"] = verify_consistency(args.verbose)

    if args.report:
        generate_report(results, args.report_file)

    # Print summary
    print("\nSummary:")

    if "update_schedule" in results:
        update_result = results["update_schedule"]
        if update_result["success"]:
            changes = update_result["changes"]
            print(
                f"  Schedule file update: {changes['modules_updated']} modules updated, {changes['modules_added']} added"
            )
            print(
                f"  Total tests: {changes['total_tests_before']} -> {changes['total_tests_after']}"
            )
            print(
                f"  Categorized: {changes['total_categorized_before']} -> {changes['total_categorized_after']}"
            )
            print(
                f"  Uncategorized: {changes['total_uncategorized_before']} -> {changes['total_uncategorized_after']}"
            )
        else:
            print(
                f"  Schedule file update failed: {update_result.get('error', 'Unknown error')}"
            )

    if "update_progress" in results:
        update_result = results["update_progress"]
        if update_result["success"]:
            changes = update_result["changes"]
            print(
                f"  Progress file update: {changes['tests_added']} tests added, {changes['tests_updated']} updated, {changes['tests_removed']} removed"
            )
            print(
                f"  Total tests: {changes['total_before']} -> {changes['total_after']}"
            )
            print(f"  Fast tests: {changes['fast_before']} -> {changes['fast_after']}")
            print(
                f"  Medium tests: {changes['medium_before']} -> {changes['medium_after']}"
            )
            print(f"  Slow tests: {changes['slow_before']} -> {changes['slow_after']}")
        else:
            print(
                f"  Progress file update failed: {update_result.get('error', 'Unknown error')}"
            )

    if "verify" in results:
        verify_result = results["verify"]
        if verify_result["success"]:
            actual = verify_result["actual_counts"]
            progress = verify_result["progress_counts"]
            schedule = verify_result["schedule_counts"]
            discrepancies = verify_result["discrepancies"]

            print(f"  Verification results:")
            print(
                f"    Actual counts: {actual['total']} total, {actual['categorized']} categorized, {actual['uncategorized']} uncategorized"
            )
            print(
                f"    Progress counts: {progress['total']} total, {progress['fast']} fast, {progress['medium']} medium, {progress['slow']} slow"
            )
            print(
                f"    Schedule counts: {schedule['total']} total, {schedule['categorized']} categorized, {schedule['uncategorized']} uncategorized"
            )

            print(f"    Discrepancies:")
            print(
                f"      Tests in progress file but not in code: {len(discrepancies['progress_vs_code']['tests_in_progress_not_in_code'])}"
            )
            print(
                f"      Tests in code but not in progress file: {len(discrepancies['progress_vs_code']['tests_in_code_not_in_progress'])}"
            )
            print(
                f"      Tests with different markers: {len(discrepancies['progress_vs_code']['tests_with_different_markers'])}"
            )
        else:
            print(
                f"  Verification failed: {verify_result.get('error', 'Unknown error')}"
            )

    if args.report:
        print(f"  Report generated: {args.report_file}")


if __name__ == "__main__":
    main()
