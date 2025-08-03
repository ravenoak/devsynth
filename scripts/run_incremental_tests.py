#!/usr/bin/env python3
"""
Run Incremental Tests

This script configures and runs the run_modified_tests.py script with
optimal settings for incremental testing. It provides several presets for different
incremental testing scenarios and allows for customization of the base commit
to compare against.

Usage:
    python scripts/run_incremental_tests.py [options]

Options:
    --preset PRESET       Incremental testing preset to use (default: recent)
                          Available presets: recent, sprint, feature, interface, all
    --base COMMIT         Base commit to compare against (overrides preset)
    --parallel            Run tests in parallel (overrides preset)
    --report              Generate HTML report (overrides preset)
    --verbose             Show detailed output
    --dry-run             Show what would be run without executing tests
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Presets for different incremental testing scenarios
PRESETS = {
    "recent": {
        "description": "Run tests for files modified in the last commit",
        "base": "HEAD~1",
        "all_tests": False,
        "parallel": True,
        "report": False,
        "speed": None,  # Run tests of all speeds
    },
    "sprint": {
        "description": "Run tests for files modified in the current sprint (last 5 commits)",
        "base": "HEAD~5",
        "all_tests": False,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
    },
    "feature": {
        "description": "Run tests for files modified in the current feature branch",
        "base": "origin/main",
        "all_tests": True,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
    },
    "interface": {
        "description": "Run interface tests for modified files",
        "base": "HEAD~3",
        "all_tests": False,
        "parallel": True,
        "report": True,
        "test_dir": "tests/unit/interface",
        "speed": None,  # Run tests of all speeds
    },
    "all": {
        "description": "Run all tests for modified files",
        "base": "HEAD~1",
        "all_tests": True,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
    }
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run incremental tests with optimal settings."
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="recent",
        help="Incremental testing preset to use (default: recent)"
    )
    parser.add_argument(
        "--base",
        help="Base commit to compare against (overrides preset)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (overrides preset)"
    )
    parser.add_argument(
        "--report",
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

def build_command(args):
    """
    Build the command to run the incremental tests script.
    
    Args:
        args: Command line arguments
        
    Returns:
        list: Command to run as a list of strings
    """
    # Start with the base command
    cmd = ["python", "scripts/run_modified_tests.py"]
    
    # Get the preset configuration
    preset = PRESETS[args.preset]
    
    # Add base commit (from args or preset)
    base = args.base if args.base else preset.get("base")
    if base:
        cmd.extend(["--base", base])
    
    # Add test directory if specified in preset
    if "test_dir" in preset:
        cmd.extend(["--test-dir", preset["test_dir"]])
    
    # Add all-tests flag
    if preset.get("all_tests", False):
        cmd.append("--all-tests")
    
    # Add parallel flag (from args or preset)
    parallel = args.parallel if args.parallel else preset.get("parallel", False)
    if parallel:
        cmd.append("--parallel")
    
    # Add report flag (from args or preset)
    report = args.report if args.report else preset.get("report", False)
    if report:
        cmd.append("--report")
    
    # Add speed filters
    speed = preset.get("speed")
    if speed == "fast":
        cmd.append("--fast")
    elif speed == "medium":
        cmd.append("--medium")
    elif speed == "slow":
        cmd.append("--slow")
    
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
    
    # Execute the command if not a dry run
    if not args.dry_run:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running incremental tests: {e}")
            sys.exit(1)
    else:
        print("Dry run - not executing tests")

if __name__ == "__main__":
    main()