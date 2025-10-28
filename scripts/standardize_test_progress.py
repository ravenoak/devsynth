#!/usr/bin/env python3
"""
Standardize Test Categorization Progress File

This script standardizes the test categorization progress file to make it compatible
with both execute_test_categorization.py and enhanced_test_categorization.py.

The standardized structure includes both:
- "tests": {} (used by enhanced_test_categorization.py)
- "categorized_tests": {} (used by execute_test_categorization.py)
- "last_date": null (used by execute_test_categorization.py)

Usage:
    python scripts/standardize_test_progress.py [options]

Options:
    --progress FILE      Progress file (default: .test_categorization_progress.json)
    --backup             Create a backup of the original file
    --verbose            Show detailed information
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Standardize test categorization progress file."
    )
    parser.add_argument(
        "--progress",
        default=".test_categorization_progress.json",
        help="Progress file (default: .test_categorization_progress.json)",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create a backup of the original file"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    return parser.parse_args()


def load_progress(progress_file):
    """Load the test categorization progress."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading progress file: {e}")
            return {"tests": {}, "categorized_tests": {}, "last_date": None}
    return {"tests": {}, "categorized_tests": {}, "last_date": None}


def save_progress(progress, progress_file):
    """Save the test categorization progress."""
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Progress saved to {progress_file}")


def standardize_progress(progress):
    """
    Standardize the progress file structure.

    Ensures the progress file has both:
    - "tests": {} (used by enhanced_test_categorization.py)
    - "categorized_tests": {} (used by execute_test_categorization.py)
    - "last_date": null (used by execute_test_categorization.py)

    Args:
        progress: The progress data

    Returns:
        Standardized progress data
    """
    # Initialize with standard structure
    standardized = {"tests": {}, "categorized_tests": {}, "last_date": None}

    # Copy existing data
    if "tests" in progress:
        standardized["tests"] = progress["tests"]

    if "categorized_tests" in progress:
        standardized["categorized_tests"] = progress["categorized_tests"]

    if "last_date" in progress:
        standardized["last_date"] = progress["last_date"]

    # Synchronize data between the two structures
    # If tests has data but categorized_tests doesn't, copy from tests to categorized_tests
    if standardized["tests"] and not standardized["categorized_tests"]:
        for test_path, test_data in standardized["tests"].items():
            standardized["categorized_tests"][test_path] = {
                "speed_category": test_data.get("marker", "medium"),
                "execution_time": test_data.get("execution_time", 0),
                "categorized_at": test_data.get(
                    "timestamp", datetime.now().isoformat()
                ),
            }

        # Update last_date
        if not standardized["last_date"]:
            standardized["last_date"] = datetime.now().isoformat()

    # If categorized_tests has data but tests doesn't, copy from categorized_tests to tests
    elif standardized["categorized_tests"] and not standardized["tests"]:
        for test_path, test_data in standardized["categorized_tests"].items():
            standardized["tests"][test_path] = {
                "marker": test_data.get("speed_category", "medium"),
                "execution_time": test_data.get("execution_time", 0),
                "timestamp": test_data.get(
                    "categorized_at", datetime.now().isoformat()
                ),
            }

    # Add summary if it doesn't exist
    if "summary" not in standardized:
        # Count tests by marker
        fast_count = sum(
            1
            for test_data in standardized["tests"].values()
            if test_data.get("marker") == "fast"
        )
        medium_count = sum(
            1
            for test_data in standardized["tests"].values()
            if test_data.get("marker") == "medium"
        )
        slow_count = sum(
            1
            for test_data in standardized["tests"].values()
            if test_data.get("marker") == "slow"
        )

        standardized["summary"] = {
            "fast": fast_count,
            "medium": medium_count,
            "slow": slow_count,
            "total": len(standardized["tests"]),
        }

    return standardized


def main():
    """Main function."""
    args = parse_args()

    progress_file = args.progress

    # Create backup if requested
    if args.backup and os.path.exists(progress_file):
        backup_file = f"{progress_file}.bak"
        shutil.copy2(progress_file, backup_file)
        print(f"Backup created: {backup_file}")

    # Load progress
    progress = load_progress(progress_file)

    if args.verbose:
        print("Original progress structure:")
        print(json.dumps(progress, indent=2))

    # Standardize progress
    standardized = standardize_progress(progress)

    if args.verbose:
        print("\nStandardized progress structure:")
        print(json.dumps(standardized, indent=2))

    # Save standardized progress
    save_progress(standardized, progress_file)

    print("\nProgress file standardized successfully!")
    print(
        f"The file now has a structure compatible with both execute_test_categorization.py and enhanced_test_categorization.py."
    )


if __name__ == "__main__":
    main()
