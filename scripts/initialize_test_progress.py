#!/usr/bin/env python3
"""
Initialize Test Categorization Progress File

This script initializes the test categorization progress file with the proper structure
that is compatible with both execute_test_categorization.py and enhanced_test_categorization.py.

Usage:
    python scripts/initialize_test_progress.py [options]

Options:
    --progress FILE      Progress file (default: .test_categorization_progress.json)
    --force              Overwrite existing file if it exists
    --verbose            Show detailed information
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize test categorization progress file."
    )
    parser.add_argument(
        "--progress",
        default=".test_categorization_progress.json",
        help="Progress file (default: .test_categorization_progress.json)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file if it exists"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information"
    )
    return parser.parse_args()

def initialize_progress_file(progress_file, force=False, verbose=False):
    """
    Initialize the test categorization progress file.
    
    Args:
        progress_file: Path to the progress file
        force: Whether to overwrite existing file
        verbose: Whether to show detailed information
        
    Returns:
        Whether the initialization was successful
    """
    # Check if file already exists
    if os.path.exists(progress_file) and not force:
        print(f"Error: Progress file {progress_file} already exists. Use --force to overwrite.")
        return False
    
    # Create the standardized structure
    progress = {
        "tests": {},                  # Used by enhanced_test_categorization.py
        "categorized_tests": {},      # Used by execute_test_categorization.py
        "last_date": None,            # Used by execute_test_categorization.py
        "summary": {                  # Summary statistics
            "fast": 0,
            "medium": 0,
            "slow": 0,
            "total": 0
        },
        "metadata": {                 # Metadata about the file
            "created_at": datetime.now().isoformat(),
            "created_by": "initialize_test_progress.py",
            "version": "1.0",
            "compatible_with": [
                "execute_test_categorization.py",
                "enhanced_test_categorization.py",
                "create_test_categorization_schedule.py"
            ]
        }
    }
    
    # Write the file
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        if verbose:
            print(f"Progress file structure:")
            print(json.dumps(progress, indent=2))
        
        print(f"Progress file initialized: {progress_file}")
        return True
    except Exception as e:
        print(f"Error initializing progress file: {e}")
        return False

def main():
    """Main function."""
    args = parse_args()
    
    # Initialize the progress file
    success = initialize_progress_file(
        args.progress,
        force=args.force,
        verbose=args.verbose
    )
    
    if success:
        print("\nThe progress file has been initialized with a structure compatible with:")
        print("- execute_test_categorization.py")
        print("- enhanced_test_categorization.py")
        print("- create_test_categorization_schedule.py")
        
        print("\nYou can now use these scripts with the initialized progress file.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()