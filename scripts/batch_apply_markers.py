#!/usr/bin/env python3
"""
Batch Apply Markers

This script automates the process of applying markers to tests in batches by running
the add_missing_markers_enhanced.py script multiple times with increasing offsets.

Usage:
    python scripts/batch_apply_markers.py [options]

Options:
    --category CATEGORY   Test category to process (unit, integration, behavior, all)
    --batch-size N        Number of tests to process in each batch (default: 25)
    --total-batches N     Total number of batches to process (default: 10)
    --start-batch N       Batch number to start from (default: 0)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Apply markers to tests in batches."
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "all"],
        default="unit",
        help="Test category to process (default: unit)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Number of tests to process in each batch (default: 25)"
    )
    parser.add_argument(
        "--total-batches",
        type=int,
        default=10,
        help="Total number of batches to process (default: 10)"
    )
    parser.add_argument(
        "--start-batch",
        type=int,
        default=0,
        help="Batch number to start from (default: 0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information"
    )
    return parser.parse_args()

def run_batch(batch_number, batch_size, category, dry_run, verbose):
    """
    Run a batch of tests with the add_missing_markers_enhanced.py script.
    
    Args:
        batch_number: Batch number (used to calculate offset)
        batch_size: Number of tests to process in the batch
        category: Test category to process
        dry_run: Whether to show changes without modifying files
        verbose: Whether to show detailed information
        
    Returns:
        True if the batch was processed successfully, False otherwise
    """
    # Calculate the offset
    offset = batch_number * batch_size
    
    # Build the command
    cmd = [
        sys.executable,
        "scripts/add_missing_markers_enhanced.py",
        f"--category={category}",
        f"--max-tests={batch_size}",
        f"--batch-size={batch_size}",
        f"--skip-tests={offset}"
    ]
    
    # Add optional arguments
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")
    
    # Print the command
    print(f"\n=== Running batch {batch_number + 1} (offset: {offset}) ===")
    print(f"Command: {' '.join(cmd)}")
    
    # Run the command
    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True)
        end_time = time.time()
        
        print(f"Batch {batch_number + 1} completed in {end_time - start_time:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running batch {batch_number + 1}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error running batch {batch_number + 1}: {e}")
        return False

def main():
    """Main function."""
    args = parse_args()
    
    # Print the configuration
    print(f"=== Batch Apply Markers ===")
    print(f"Category: {args.category}")
    print(f"Batch size: {args.batch_size}")
    print(f"Total batches: {args.total_batches}")
    print(f"Start batch: {args.start_batch}")
    print(f"Dry run: {args.dry_run}")
    print(f"Verbose: {args.verbose}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Process each batch
    successful_batches = 0
    failed_batches = 0
    
    for i in range(args.start_batch, args.start_batch + args.total_batches):
        success = run_batch(
            batch_number=i,
            batch_size=args.batch_size,
            category=args.category,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        if success:
            successful_batches += 1
        else:
            failed_batches += 1
    
    # Print the summary
    print(f"\n=== Summary ===")
    print(f"Total batches: {args.total_batches}")
    print(f"Successful batches: {successful_batches}")
    print(f"Failed batches: {failed_batches}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return the exit code
    return 0 if failed_batches == 0 else 1

if __name__ == "__main__":
    sys.exit(main())