#!/usr/bin/env python3
"""
Run Prioritized Tests

This script configures and runs the prioritize_high_risk_tests.py script with
optimal settings for test prioritization. It provides several presets for different
test prioritization scenarios and automatically determines the optimal number of
processes based on the available CPU cores.

Usage:
    python scripts/run_prioritized_tests.py [options]

Options:
    --preset PRESET       Prioritization preset to use (default: balanced)
                          Available presets: interface, critical, recent, thorough
    --category CAT        Test category to run (unit, integration, behavior, all)
    --module MODULE       Specific module to analyze (e.g., tests/unit/interface)
    --processes N         Override the number of processes
    --report              Generate a detailed risk report
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

# Presets for different test prioritization scenarios
PRESETS = {
    "interface": {
        "description": "Prioritize interface tests with high failure rate",
        "category": "unit",
        "module": "tests/unit/interface",
        "limit": 50,
        "min_risk": 60,
        "timeout": 120,
        "update_history": True,
        "report": True,
    },
    "critical": {
        "description": "Run only the highest-risk tests across all categories",
        "category": "all",
        "module": None,
        "limit": 100,
        "min_risk": 80,
        "timeout": 180,
        "update_history": True,
        "report": True,
    },
    "recent": {
        "description": "Prioritize tests affected by recent changes",
        "category": "all",
        "module": None,
        "limit": 200,
        "min_risk": 50,
        "timeout": 120,
        "update_history": True,
        "report": True,
        "recent_changes_weight": 0.5,  # Increase weight for recent changes
    },
    "thorough": {
        "description": "Run a thorough risk analysis with detailed reporting",
        "category": "all",
        "module": None,
        "limit": 500,
        "min_risk": 30,
        "timeout": 300,
        "update_history": True,
        "report": True,
    },
    "balanced": {
        "description": "Balanced approach for most scenarios",
        "category": "all",
        "module": None,
        "limit": 200,
        "min_risk": 50,
        "timeout": 180,
        "update_history": True,
        "report": True,
    }
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run prioritized tests with optimal settings."
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="balanced",
        help="Prioritization preset to use (default: balanced)"
    )
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "behavior", "performance", "property", "all"],
        help="Test category to run (overrides preset)"
    )
    parser.add_argument(
        "--module",
        help="Specific module to analyze (overrides preset)"
    )
    parser.add_argument(
        "--processes",
        type=int,
        help="Override the number of processes"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed risk report (overrides preset)"
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

def get_optimal_processes():
    """
    Determine the optimal number of processes based on available CPU cores.
    
    Returns:
        int: Optimal number of processes
    """
    # Use 75% of available cores, but at least 2 and at most 8
    cpu_count = multiprocessing.cpu_count()
    optimal = max(2, min(8, int(cpu_count * 0.75)))
    return optimal

def build_command(args):
    """
    Build the command to run the test prioritization script.
    
    Args:
        args: Command line arguments
        
    Returns:
        list: Command to run as a list of strings
    """
    # Start with the base command
    cmd = ["python", "scripts/prioritize_high_risk_tests.py"]
    
    # Get the preset configuration
    preset = PRESETS[args.preset]
    
    # Add category (from args or preset)
    category = args.category if args.category else preset.get("category")
    if category and category != "all":
        cmd.extend(["--category", category])
    
    # Add module (from args or preset)
    module = args.module if args.module else preset.get("module")
    if module:
        cmd.extend(["--module", module])
    
    # Add limit
    limit = preset.get("limit", 100)
    cmd.extend(["--limit", str(limit)])
    
    # Add min-risk
    min_risk = preset.get("min_risk", 0)
    cmd.extend(["--min-risk", str(min_risk)])
    
    # Add processes
    processes = args.processes if args.processes is not None else get_optimal_processes()
    cmd.extend(["--processes", str(processes)])
    
    # Add timeout
    timeout = preset.get("timeout", 60)
    cmd.extend(["--timeout", str(timeout)])
    
    # Add update-history
    if preset.get("update_history", False):
        cmd.append("--update-history")
    
    # Add report
    report = args.report if args.report else preset.get("report", False)
    if report:
        cmd.append("--report")
    
    # Add verbose output
    if args.verbose:
        cmd.append("--verbose")
    
    # Add dry-run
    if args.dry_run:
        cmd.append("--dry-run")
    
    return cmd

def main():
    """Main function."""
    args = parse_args()
    
    # Build the command
    cmd = build_command(args)
    
    # Print the command
    print(f"Running: {' '.join(cmd)}")
    print(f"Preset: {args.preset} - {PRESETS[args.preset]['description']}")
    print(f"Processes: {args.processes if args.processes is not None else get_optimal_processes()}")
    
    # Execute the command if not a dry run
    if not args.dry_run:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running prioritized tests: {e}")
            sys.exit(1)
    else:
        print("Dry run - not executing tests")

if __name__ == "__main__":
    main()