#!/usr/bin/env python3
"""
Test Count Reconciliation Script

This script reconciles test counts across different sources to ensure consistency:
1. Actual test files (using common_test_collector.py)
2. Documentation files (test_suite_overview.md, test_categorization_guide.md)
3. Progress tracking files (.test_categorization_progress.json)
4. Schedule files (.test_categorization_schedule.json)

It identifies discrepancies and can update documentation and tracking files to
reflect the actual state of the test suite.

Usage:
    python scripts/reconcile_test_counts.py [options]

Options:
    --analyze              Analyze discrepancies without making changes
    --update-docs          Update documentation files with accurate counts
    --update-tracking      Update tracking files with accurate counts
    --update-all           Update both documentation and tracking files
    --verbose              Show detailed information
    --no-cache             Don't use cached test collection results
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


def clean_count_string(s):
    """Clean a string by removing commas and markdown formatting."""
    return s.replace(",", "").replace("*", "")


# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        collect_tests,
        collect_tests_by_category,
        get_marker_counts,
        get_test_counts,
    )
except ImportError:
    print(
        "Error: common_test_collector.py not found. Please ensure it exists in the scripts directory."
    )
    sys.exit(1)

# Documentation files
TEST_SUITE_OVERVIEW = Path("docs/developer_guides/test_suite_overview.md")
TEST_CATEGORIZATION_GUIDE = Path("docs/developer_guides/test_categorization_guide.md")
PROJECT_STATUS = Path("PROJECT_STATUS.md")

# Tracking files
PROGRESS_FILE = Path(".test_categorization_progress.json")
SCHEDULE_FILE = Path(".test_categorization_schedule.json")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Reconcile test counts across different sources."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze discrepancies without making changes",
    )
    parser.add_argument(
        "--update-docs",
        action="store_true",
        help="Update documentation files with accurate counts",
    )
    parser.add_argument(
        "--update-tracking",
        action="store_true",
        help="Update tracking files with accurate counts",
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="Update both documentation and tracking files",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached test collection results",
    )
    return parser.parse_args()


def get_actual_test_counts(use_cache: bool = True) -> dict[str, Any]:
    """
    Get actual test counts from the test files.

    Args:
        use_cache: Whether to use cached test collection results

    Returns:
        Dictionary with test counts and marker counts
    """
    print("Collecting actual test counts...")

    # Get test counts by category
    test_counts = get_test_counts(use_cache=use_cache)

    # Get marker counts
    marker_counts = get_marker_counts(use_cache=use_cache)

    # Calculate unmarked tests
    unmarked_counts = {}
    for category in test_counts:
        if category != "total":
            unmarked_counts[category] = test_counts[category]
            for marker_type in ["fast", "medium", "slow"]:
                if marker_type in marker_counts.get(category, {}):
                    unmarked_counts[category] -= marker_counts[category][marker_type]

    unmarked_counts["total"] = sum(unmarked_counts.values())

    # Combine all counts
    result = {
        "test_counts": test_counts,
        "marker_counts": marker_counts,
        "unmarked_counts": unmarked_counts,
    }

    return result


def get_doc_test_counts() -> dict[str, dict[str, Any]]:
    """
    Get test counts from documentation files.

    Returns:
        Dictionary mapping file names to test count dictionaries
    """
    print("Collecting test counts from documentation...")

    result = {}

    # Parse test_suite_overview.md
    if TEST_SUITE_OVERVIEW.exists():
        with open(TEST_SUITE_OVERVIEW) as f:
            content = f.read()

        # Extract total test count
        total_match = re.search(
            r"DevSynth test suite consists of \*\*([0-9,\*]+) total tests\*\*", content
        )
        total_count = (
            int(clean_count_string(total_match.group(1))) if total_match else None
        )

        # Extract category counts
        category_counts = {}
        category_table = re.search(
            r"\| Category \| Count \| Description \|\n\|.*\|\n((?:\|.*\|\n)+)", content
        )
        if category_table:
            for line in category_table.group(1).strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 3:
                    category = parts[1].strip().lower()
                    count = int(clean_count_string(parts[2].strip()))
                    category_counts[category] = count

        # Extract speed counts
        speed_counts = {}
        speed_table = re.search(
            r"\| Speed \| Count \| Description \|\n\|.*\|\n((?:\|.*\|\n)+)", content
        )
        if speed_table:
            for line in speed_table.group(1).strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 3:
                    speed = parts[1].strip().lower()
                    count = int(clean_count_string(parts[2].strip()))
                    speed_counts[speed] = count

        # Extract status counts
        status_counts = {}
        status_table = re.search(
            r"\| Status \| Count \| Percentage \|\n\|.*\|\n((?:\|.*\|\n)+)", content
        )
        if status_table:
            for line in status_table.group(1).strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 3:
                    status = parts[1].strip().lower()
                    count = int(clean_count_string(parts[2].strip()))
                    status_counts[status] = count

        result["test_suite_overview"] = {
            "total": total_count,
            "category_counts": category_counts,
            "speed_counts": speed_counts,
            "status_counts": status_counts,
        }

    # Parse test_categorization_guide.md
    if TEST_CATEGORIZATION_GUIDE.exists():
        with open(TEST_CATEGORIZATION_GUIDE) as f:
            content = f.read()

        # Extract total test count
        total_match = re.search(
            r"DevSynth has a large test suite with ([0-9,\*]+) tests", content
        )
        total_count = (
            int(clean_count_string(total_match.group(1))) if total_match else None
        )

        # Extract speed counts
        speed_counts = {}
        speed_table = re.search(
            r"\| Speed \| Count \| Percentage \| Target \|\n\|.*\|\n((?:\|.*\|\n)+)",
            content,
        )
        if speed_table:
            for line in speed_table.group(1).strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 4:
                    speed = parts[1].strip().lower()
                    count = int(clean_count_string(parts[2].strip()))
                    speed_counts[speed] = count

        result["test_categorization_guide"] = {
            "total": total_count,
            "speed_counts": speed_counts,
        }

    # Parse PROJECT_STATUS.md
    if PROJECT_STATUS.exists():
        with open(PROJECT_STATUS) as f:
            content = f.read()

        # Extract test counts
        test_count_match = re.search(
            r"Resolving test failures \(approximately ([0-9,\*]+) failing tests out of ([0-9,\*]+) total tests",
            content,
        )
        if test_count_match:
            failing_count = int(clean_count_string(test_count_match.group(1)))
            total_count = int(clean_count_string(test_count_match.group(2)))

            result["project_status"] = {"total": total_count, "failing": failing_count}

    return result


def get_tracking_file_counts() -> dict[str, dict[str, Any]]:
    """
    Get test counts from tracking files.

    Returns:
        Dictionary mapping file names to test count dictionaries
    """
    print("Collecting test counts from tracking files...")

    result = {}

    # Parse progress file
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                progress_data = json.load(f)

            # Extract counts
            categorized_counts = {"fast": 0, "medium": 0, "slow": 0}

            for test_path, info in progress_data.get("tests", {}).items():
                marker = info.get("marker")
                if marker in categorized_counts:
                    categorized_counts[marker] += 1

            result["progress_file"] = {
                "categorized_counts": categorized_counts,
                "total_categorized": sum(categorized_counts.values()),
            }
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading progress file: {e}")

    # Parse schedule file
    if SCHEDULE_FILE.exists():
        try:
            with open(SCHEDULE_FILE) as f:
                schedule_data = json.load(f)

            # Extract counts
            total_tests = schedule_data.get("total_tests", 0)
            categorized_tests = schedule_data.get("categorized_tests", 0)
            remaining_tests = schedule_data.get("remaining_tests", 0)

            result["schedule_file"] = {
                "total": total_tests,
                "categorized": categorized_tests,
                "remaining": remaining_tests,
            }
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading schedule file: {e}")

    return result


def analyze_discrepancies(
    actual_counts: dict[str, Any],
    doc_counts: dict[str, dict[str, Any]],
    tracking_counts: dict[str, dict[str, Any]],
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Analyze discrepancies between different sources of test counts.

    Args:
        actual_counts: Actual test counts from test files
        doc_counts: Test counts from documentation files
        tracking_counts: Test counts from tracking files
        verbose: Whether to show detailed information

    Returns:
        Dictionary with discrepancies
    """
    print("Analyzing discrepancies...")

    discrepancies = {
        "total_counts": [],
        "category_counts": [],
        "speed_counts": [],
        "status_counts": [],
        "tracking_counts": [],
    }

    # Get actual counts
    actual_total = actual_counts["test_counts"]["total"]
    actual_category_counts = {
        k: v for k, v in actual_counts["test_counts"].items() if k != "total"
    }
    actual_speed_counts = {
        "fast": actual_counts["marker_counts"]["total"].get("fast", 0),
        "medium": actual_counts["marker_counts"]["total"].get("medium", 0),
        "slow": actual_counts["marker_counts"]["total"].get("slow", 0),
        "unmarked": actual_counts["unmarked_counts"]["total"],
    }

    # Compare total counts
    if "test_suite_overview" in doc_counts:
        doc_total = doc_counts["test_suite_overview"]["total"]
        if doc_total != actual_total:
            discrepancies["total_counts"].append(
                {
                    "source": "test_suite_overview.md",
                    "actual": actual_total,
                    "documented": doc_total,
                    "difference": doc_total - actual_total,
                }
            )

    if "test_categorization_guide" in doc_counts:
        doc_total = doc_counts["test_categorization_guide"]["total"]
        if doc_total != actual_total:
            discrepancies["total_counts"].append(
                {
                    "source": "test_categorization_guide.md",
                    "actual": actual_total,
                    "documented": doc_total,
                    "difference": doc_total - actual_total,
                }
            )

    if "project_status" in doc_counts:
        doc_total = doc_counts["project_status"]["total"]
        if doc_total != actual_total:
            discrepancies["total_counts"].append(
                {
                    "source": "PROJECT_STATUS.md",
                    "actual": actual_total,
                    "documented": doc_total,
                    "difference": doc_total - actual_total,
                }
            )

    if "schedule_file" in tracking_counts:
        tracking_total = tracking_counts["schedule_file"]["total"]
        if tracking_total != actual_total:
            discrepancies["total_counts"].append(
                {
                    "source": ".test_categorization_schedule.json",
                    "actual": actual_total,
                    "documented": tracking_total,
                    "difference": tracking_total - actual_total,
                }
            )

    # Compare category counts
    if "test_suite_overview" in doc_counts:
        doc_category_counts = doc_counts["test_suite_overview"]["category_counts"]
        for category, actual_count in actual_category_counts.items():
            if (
                category in doc_category_counts
                and doc_category_counts[category] != actual_count
            ):
                discrepancies["category_counts"].append(
                    {
                        "source": "test_suite_overview.md",
                        "category": category,
                        "actual": actual_count,
                        "documented": doc_category_counts[category],
                        "difference": doc_category_counts[category] - actual_count,
                    }
                )

    # Compare speed counts
    if "test_suite_overview" in doc_counts:
        doc_speed_counts = doc_counts["test_suite_overview"]["speed_counts"]
        for speed, actual_count in actual_speed_counts.items():
            if speed in doc_speed_counts and doc_speed_counts[speed] != actual_count:
                discrepancies["speed_counts"].append(
                    {
                        "source": "test_suite_overview.md",
                        "speed": speed,
                        "actual": actual_count,
                        "documented": doc_speed_counts[speed],
                        "difference": doc_speed_counts[speed] - actual_count,
                    }
                )

    if "test_categorization_guide" in doc_counts:
        doc_speed_counts = doc_counts["test_categorization_guide"]["speed_counts"]
        for speed, actual_count in actual_speed_counts.items():
            if speed in doc_speed_counts and doc_speed_counts[speed] != actual_count:
                discrepancies["speed_counts"].append(
                    {
                        "source": "test_categorization_guide.md",
                        "speed": speed,
                        "actual": actual_count,
                        "documented": doc_speed_counts[speed],
                        "difference": doc_speed_counts[speed] - actual_count,
                    }
                )

    # Compare tracking counts
    if "progress_file" in tracking_counts:
        progress_counts = tracking_counts["progress_file"]["categorized_counts"]
        for speed, actual_count in actual_speed_counts.items():
            if speed in progress_counts and progress_counts[speed] != actual_count:
                discrepancies["tracking_counts"].append(
                    {
                        "source": ".test_categorization_progress.json",
                        "speed": speed,
                        "actual": actual_count,
                        "tracked": progress_counts[speed],
                        "difference": progress_counts[speed] - actual_count,
                    }
                )

    if "schedule_file" in tracking_counts:
        schedule_counts = tracking_counts["schedule_file"]
        actual_categorized = sum(
            actual_speed_counts[s] for s in ["fast", "medium", "slow"]
        )
        if schedule_counts["categorized"] != actual_categorized:
            discrepancies["tracking_counts"].append(
                {
                    "source": ".test_categorization_schedule.json",
                    "type": "categorized",
                    "actual": actual_categorized,
                    "tracked": schedule_counts["categorized"],
                    "difference": schedule_counts["categorized"] - actual_categorized,
                }
            )

        actual_remaining = actual_speed_counts["unmarked"]
        if schedule_counts["remaining"] != actual_remaining:
            discrepancies["tracking_counts"].append(
                {
                    "source": ".test_categorization_schedule.json",
                    "type": "remaining",
                    "actual": actual_remaining,
                    "tracked": schedule_counts["remaining"],
                    "difference": schedule_counts["remaining"] - actual_remaining,
                }
            )

    return discrepancies


def update_documentation(
    actual_counts: dict[str, Any], discrepancies: dict[str, Any], verbose: bool = False
) -> bool:
    """
    Update documentation files with accurate test counts.

    Args:
        actual_counts: Actual test counts from test files
        discrepancies: Discrepancies between different sources
        verbose: Whether to show detailed information

    Returns:
        Whether any updates were made
    """
    print("Updating documentation files...")

    updated = False

    # Get actual counts
    actual_total = actual_counts["test_counts"]["total"]
    actual_category_counts = {
        k: v for k, v in actual_counts["test_counts"].items() if k != "total"
    }
    actual_speed_counts = {
        "fast": actual_counts["marker_counts"]["total"].get("fast", 0),
        "medium": actual_counts["marker_counts"]["total"].get("medium", 0),
        "slow": actual_counts["marker_counts"]["total"].get("slow", 0),
        "unmarked": actual_counts["unmarked_counts"]["total"],
    }

    # Update test_suite_overview.md
    if TEST_SUITE_OVERVIEW.exists():
        with open(TEST_SUITE_OVERVIEW) as f:
            content = f.read()

        # Update total test count
        content = re.sub(
            r"DevSynth test suite consists of \*\*([0-9,]+) total tests\*\*",
            f"DevSynth test suite consists of **{actual_total:,} total tests**",
            content,
        )

        # Update category counts
        category_table = re.search(
            r"(\| Category \| Count \| Description \|\n\|.*\|\n)((?:\|.*\|\n)+)",
            content,
        )
        if category_table:
            header = category_table.group(1)
            rows = []

            # Add rows for each category
            for category, count in sorted(actual_category_counts.items()):
                if category != "total":
                    rows.append(
                        f"| {category.capitalize()} | {count:,} | Tests for {category} components |"
                    )

            # Add total row
            rows.append(f"| **Total** | **{actual_total:,}** | |")

            # Replace table
            new_table = header + "\n".join(rows) + "\n"
            content = content.replace(category_table.group(0), new_table)

        # Update speed counts
        speed_table = re.search(
            r"(\| Speed \| Count \| Description \|\n\|.*\|\n)((?:\|.*\|\n)+)", content
        )
        if speed_table:
            header = speed_table.group(1)
            rows = []

            # Add rows for each speed category
            for speed, count in sorted(actual_speed_counts.items()):
                description = ""
                if speed == "fast":
                    description = "Tests that execute in less than 1 second"
                elif speed == "medium":
                    description = "Tests that execute between 1-5 seconds"
                elif speed == "slow":
                    description = "Tests that execute in more than 5 seconds"
                elif speed == "unmarked":
                    description = "Tests that have not yet been categorized by speed"

                rows.append(f"| {speed.capitalize()} | {count:,} | {description} |")

            # Add total row
            rows.append(f"| **Total** | **{actual_total:,}** | |")

            # Replace table
            new_table = header + "\n".join(rows) + "\n"
            content = content.replace(speed_table.group(0), new_table)

        # Update last updated date
        content = re.sub(
            r"_Last updated: .*_",
            f'_Last updated: {datetime.now().strftime("%B %d, %Y")}_',
            content,
        )

        # Write updated content
        with open(TEST_SUITE_OVERVIEW, "w") as f:
            f.write(content)

        updated = True
        print(f"Updated {TEST_SUITE_OVERVIEW}")

    # Update test_categorization_guide.md
    if TEST_CATEGORIZATION_GUIDE.exists():
        with open(TEST_CATEGORIZATION_GUIDE) as f:
            content = f.read()

        # Update total test count
        content = re.sub(
            r"DevSynth has a large test suite with ([0-9,]+) tests",
            f"DevSynth has a large test suite with {actual_total:,} tests",
            content,
        )

        # Update speed counts
        speed_table = re.search(
            r"(\| Speed \| Count \| Percentage \| Target \|\n\|.*\|\n)((?:\|.*\|\n)+)",
            content,
        )
        if speed_table:
            header = speed_table.group(1)
            rows = []

            # Add rows for each speed category
            for speed, count in sorted(actual_speed_counts.items()):
                percentage = count / actual_total * 100 if actual_total > 0 else 0
                target = ""
                if speed == "fast":
                    target = "~40%"
                elif speed == "medium":
                    target = "~40%"
                elif speed == "slow":
                    target = "~20%"
                elif speed == "unmarked":
                    target = "0%"

                rows.append(
                    f"| {speed.capitalize()} | {count:,} | {percentage:.1f}% | {target} |"
                )

            # Add total row
            rows.append(f"| **Total** | **{actual_total:,}** | **100%** | **100%** |")

            # Replace table
            new_table = header + "\n".join(rows) + "\n"
            content = content.replace(speed_table.group(0), new_table)

        # Update categorization status text
        categorized_count = sum(
            actual_speed_counts[s] for s in ["fast", "medium", "slow"]
        )
        categorized_percentage = (
            categorized_count / actual_total * 100 if actual_total > 0 else 0
        )

        content = re.sub(
            r"We have begun applying speed categorization to the tests.*?So far, we have categorized ([0-9,]+) tests \(([0-9.]+)% of total\)",
            f"We have begun applying speed categorization to the tests using the `incremental_test_categorization.py` script and the test categorization schedule. So far, we have categorized {categorized_count:,} tests ({categorized_percentage:.1f}% of total)",
            content,
            flags=re.DOTALL,
        )

        # Update last updated date
        content = re.sub(
            r"_Last updated: .*_",
            f'_Last updated: {datetime.now().strftime("%B %d, %Y")}_',
            content,
        )

        # Write updated content
        with open(TEST_CATEGORIZATION_GUIDE, "w") as f:
            f.write(content)

        updated = True
        print(f"Updated {TEST_CATEGORIZATION_GUIDE}")

    # Update PROJECT_STATUS.md
    if PROJECT_STATUS.exists():
        with open(PROJECT_STATUS) as f:
            content = f.read()

        # Update test counts
        content = re.sub(
            r"Resolving test failures \(approximately ([0-9,]+) failing tests out of ([0-9,]+) total tests",
            f"Resolving test failures (approximately 348 failing tests out of {actual_total:,} total tests",
            content,
        )

        # Write updated content
        with open(PROJECT_STATUS, "w") as f:
            f.write(content)

        updated = True
        print(f"Updated {PROJECT_STATUS}")

    return updated


def update_tracking_files(
    actual_counts: dict[str, Any], discrepancies: dict[str, Any], verbose: bool = False
) -> bool:
    """
    Update tracking files with accurate test counts.

    Args:
        actual_counts: Actual test counts from test files
        discrepancies: Discrepancies between different sources
        verbose: Whether to show detailed information

    Returns:
        Whether any updates were made
    """
    print("Updating tracking files...")

    updated = False

    # Get actual counts
    actual_total = actual_counts["test_counts"]["total"]
    actual_speed_counts = {
        "fast": actual_counts["marker_counts"]["total"].get("fast", 0),
        "medium": actual_counts["marker_counts"]["total"].get("medium", 0),
        "slow": actual_counts["marker_counts"]["total"].get("slow", 0),
        "unmarked": actual_counts["unmarked_counts"]["total"],
    }

    # Update schedule file
    if SCHEDULE_FILE.exists():
        try:
            with open(SCHEDULE_FILE) as f:
                schedule_data = json.load(f)

            # Update counts
            schedule_data["total_tests"] = actual_total
            schedule_data["categorized_tests"] = sum(
                actual_speed_counts[s] for s in ["fast", "medium", "slow"]
            )
            schedule_data["remaining_tests"] = actual_speed_counts["unmarked"]

            # Write updated data
            with open(SCHEDULE_FILE, "w") as f:
                json.dump(schedule_data, f, indent=2)

            updated = True
            print(f"Updated {SCHEDULE_FILE}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error updating schedule file: {e}")

    return updated


def print_discrepancies(discrepancies: dict[str, Any], verbose: bool = False):
    """
    Print discrepancies between different sources of test counts.

    Args:
        discrepancies: Discrepancies between different sources
        verbose: Whether to show detailed information
    """
    print("\nDiscrepancies found:")

    # Print total count discrepancies
    if discrepancies["total_counts"]:
        print("\nTotal test count discrepancies:")
        for disc in discrepancies["total_counts"]:
            print(
                f"  {disc['source']}: {disc['documented']:,} (Actual: {disc['actual']:,}, Difference: {disc['difference']:+,})"
            )

    # Print category count discrepancies
    if discrepancies["category_counts"]:
        print("\nCategory count discrepancies:")
        for disc in discrepancies["category_counts"]:
            print(
                f"  {disc['source']} - {disc['category']}: {disc['documented']:,} (Actual: {disc['actual']:,}, Difference: {disc['difference']:+,})"
            )

    # Print speed count discrepancies
    if discrepancies["speed_counts"]:
        print("\nSpeed count discrepancies:")
        for disc in discrepancies["speed_counts"]:
            print(
                f"  {disc['source']} - {disc['speed']}: {disc['documented']:,} (Actual: {disc['actual']:,}, Difference: {disc['difference']:+,})"
            )

    # Print tracking count discrepancies
    if discrepancies["tracking_counts"]:
        print("\nTracking file discrepancies:")
        for disc in discrepancies["tracking_counts"]:
            if "type" in disc:
                print(
                    f"  {disc['source']} - {disc['type']}: {disc['tracked']:,} (Actual: {disc['actual']:,}, Difference: {disc['difference']:+,})"
                )
            else:
                print(
                    f"  {disc['source']} - {disc['speed']}: {disc['tracked']:,} (Actual: {disc['actual']:,}, Difference: {disc['difference']:+,})"
                )

    # Print summary
    total_discrepancies = sum(len(discs) for discs in discrepancies.values())
    print(f"\nTotal discrepancies: {total_discrepancies}")


def main():
    """Main function."""
    args = parse_args()

    # Get actual test counts
    actual_counts = get_actual_test_counts(use_cache=not args.no_cache)

    # Get counts from documentation
    doc_counts = get_doc_test_counts()

    # Get counts from tracking files
    tracking_counts = get_tracking_file_counts()

    # Analyze discrepancies
    discrepancies = analyze_discrepancies(
        actual_counts, doc_counts, tracking_counts, verbose=args.verbose
    )

    # Print discrepancies
    print_discrepancies(discrepancies, verbose=args.verbose)

    # Update documentation if requested
    if args.update_docs or args.update_all:
        updated = update_documentation(
            actual_counts, discrepancies, verbose=args.verbose
        )
        if not updated:
            print("No documentation updates needed.")

    # Update tracking files if requested
    if args.update_tracking or args.update_all:
        updated = update_tracking_files(
            actual_counts, discrepancies, verbose=args.verbose
        )
        if not updated:
            print("No tracking file updates needed.")

    # Print summary
    print("\nSummary:")
    print(f"  Total tests: {actual_counts['test_counts']['total']:,}")
    print(f"  Tests by category:")
    for category, count in sorted(actual_counts["test_counts"].items()):
        if category != "total":
            print(f"    {category}: {count:,}")

    print(f"  Tests by speed:")
    for speed in ["fast", "medium", "slow", "unmarked"]:
        if speed == "unmarked":
            count = actual_counts["unmarked_counts"]["total"]
        else:
            count = actual_counts["marker_counts"]["total"].get(speed, 0)
        print(f"    {speed}: {count:,}")

    print("\nDone!")


if __name__ == "__main__":
    main()
