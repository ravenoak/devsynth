#!/usr/bin/env python3
"""
Run Distributed Tests

This script configures and runs the distributed_test_runner_enhanced.py script with
optimal settings for parallel execution. It provides several presets for different
test execution scenarios and automatically determines the optimal number of workers
based on the available CPU cores.

Usage:
    python scripts/run_distributed_tests.py [options]

Options:
    --preset PRESET       Execution preset to use (default: balanced)
                          Available presets: fast, thorough, ci, interface
    --category CAT        Test category to run (unit, integration, behavior, all)
    --speed SPEED         Test speed category (fast, medium, slow, all)
    --workers N           Override the number of worker processes
    --html                Generate HTML report
    --verbose             Show detailed output
    --dry-run             Show what would be run without executing tests
"""

import os
import sys
import json
import argparse
import multiprocessing
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Presets for different test execution scenarios
PRESETS = {
    "fast": {
        "description": "Run fast tests for quick feedback during development",
        "category": "unit",
        "speed": "fast",
        "batch_size": 10,
        "timeout": 120,
        "balance_load": True,
        "use_history": True,
        "html": False,
    },
    "thorough": {
        "description": "Run all tests with thorough coverage",
        "category": "all",
        "speed": "all",
        "batch_size": 20,
        "timeout": 300,
        "balance_load": True,
        "use_history": True,
        "html": True,
    },
    "ci": {
        "description": "Run tests optimized for CI environments",
        "category": "all",
        "speed": "all",
        "batch_size": 30,
        "timeout": 600,
        "balance_load": True,
        "use_history": True,
        "html": True,
    },
    "interface": {
        "description": "Run interface tests with high failure rate",
        "category": "unit",
        "module": "tests/unit/interface",
        "batch_size": 5,
        "timeout": 180,
        "balance_load": True,
        "use_history": True,
        "html": True,
    },
    "balanced": {
        "description": "Balanced approach for most scenarios",
        "category": "all",
        "speed": "all",
        "batch_size": 20,
        "timeout": 300,
        "balance_load": True,
        "use_history": True,
        "html": True,
    }
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run distributed tests with optimal settings."
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="balanced",
        help="Execution preset to use (default: balanced)"
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "performance", "property", "all"],
        help="Test category to run (overrides preset)"
    )
    parser.add_argument(
        "--speed",
        choices=["fast", "medium", "slow", "all", "unmarked"],
        help="Test speed category (overrides preset)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Override the number of worker processes"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report (overrides preset)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing tests"
    )
    return parser.parse_args()

def get_optimal_workers():
    """
    Determine the optimal number of worker processes based on available CPU cores.
    
    Returns:
        int: Optimal number of worker processes
    """
    # Use 75% of available cores, but at least 2 and at most 8
    cpu_count = multiprocessing.cpu_count()
    optimal = max(2, min(8, int(cpu_count * 0.75)))
    return optimal

def build_command(args):
    """
    Build the command to run the distributed test runner.
    
    Args:
        args: Command line arguments
        
    Returns:
        list: Command to run as a list of strings
    """
    # Start with the base command
    cmd = ["python", "scripts/distributed_test_runner_enhanced.py"]
    
    # Get the preset configuration
    preset = PRESETS[args.preset]
    
    # Add workers
    workers = args.workers if args.workers is not None else get_optimal_workers()
    cmd.extend(["--workers", str(workers)])
    
    # Add category (from args or preset)
    category = args.category if args.category else preset.get("category")
    if category and category != "all":
        cmd.extend(["--category", category])
    
    # Add speed (from args or preset)
    speed = args.speed if args.speed else preset.get("speed")
    if speed and speed != "all":
        cmd.extend(["--speed", speed])
    
    # Add module if specified in preset
    if "module" in preset:
        cmd.extend(["--test-dir", preset["module"]])
    
    # Add batch size
    batch_size = preset.get("batch_size", 20)
    cmd.extend(["--batch-size", str(batch_size)])
    
    # Add timeout
    timeout = preset.get("timeout", 300)
    cmd.extend(["--timeout", str(timeout)])
    
    # Add load balancing
    if preset.get("balance_load", False):
        cmd.append("--balance-load")
    
    # Add history usage
    if preset.get("use_history", False):
        cmd.append("--use-history")
    
    # Add HTML report generation
    html = args.html if args.html else preset.get("html", False)
    if html:
        cmd.append("--html")
    
    # Add verbose output
    if args.verbose:
        cmd.append("--verbose")
    
    return cmd

def main():
    """Main function."""
    args = parse_args()
    
    # Build the command
    cmd = build_command(args)
    
    # Print the command
    print(f"Running: {' '.join(cmd)}")
    print(f"Preset: {args.preset} - {PRESETS[args.preset]['description']}")
    print(f"Workers: {args.workers if args.workers is not None else get_optimal_workers()}")
    
    # Execute the command if not a dry run
    if not args.dry_run:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running distributed tests: {e}")
            sys.exit(1)
    else:
        print("Dry run - not executing tests")

if __name__ == "__main__":
    main()