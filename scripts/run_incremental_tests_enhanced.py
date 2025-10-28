#!/usr/bin/env python3
"""
Enhanced Incremental Tests Runner

This script configures and runs the run_modified_tests_enhanced.py script with
optimal settings for incremental testing. It provides several presets for different
incremental testing scenarios and allows for customization of the base commit
to compare against.

Usage:
    python scripts/run_incremental_tests_enhanced.py [options]

Options:
    --preset PRESET       Incremental testing preset to use (default: recent)
                          Available presets: recent, sprint, feature, interface, fast, all
    --base COMMIT         Base commit to compare against (overrides preset)
    --parallel            Run tests in parallel (overrides preset)
    --report              Generate HTML report (overrides preset)
    --verbose             Show detailed output
    --dry-run             Show what would be run without executing tests
    --prioritize          Prioritize tests based on failure history
    --balanced            Use balanced distribution for parallel execution
    --max-tests N         Maximum number of tests to run (default: from preset)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Presets for different incremental testing scenarios
PRESETS = {
    "recent": {
        "description": "Run tests for files modified in the last commit",
        "base": "HEAD~1",
        "all_tests": False,
        "parallel": True,
        "report": False,
        "speed": None,  # Run tests of all speeds
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
    "sprint": {
        "description": "Run tests for files modified in the current sprint (last 5 commits)",
        "base": "HEAD~5",
        "all_tests": False,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
    "feature": {
        "description": "Run tests for files modified in the current feature branch",
        "base": "origin/main",
        "all_tests": True,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
    "interface": {
        "description": "Run interface tests for modified files",
        "base": "HEAD~3",
        "all_tests": False,
        "parallel": True,
        "report": True,
        "test_dir": "tests/unit/interface",
        "speed": None,  # Run tests of all speeds
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
    "fast": {
        "description": "Run only fast tests for modified files (quick feedback)",
        "base": "HEAD~1",
        "all_tests": False,
        "parallel": True,
        "report": False,
        "speed": "fast",
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
    "all": {
        "description": "Run all tests for modified files",
        "base": "HEAD~1",
        "all_tests": True,
        "parallel": True,
        "report": True,
        "speed": None,  # Run tests of all speeds
        "prioritize": True,
        "balanced": True,
        "max_tests": 0,  # No limit
    },
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
        help="Incremental testing preset to use (default: recent)",
    )
    parser.add_argument(
        "--base", help="Base commit to compare against (overrides preset)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (overrides preset)",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate HTML report (overrides preset)"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing tests",
    )
    parser.add_argument(
        "--prioritize",
        action="store_true",
        help="Prioritize tests based on failure history (overrides preset)",
    )
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="Use balanced distribution for parallel execution (overrides preset)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=0,
        help="Maximum number of tests to run (overrides preset)",
    )
    return parser.parse_args()


def build_command(args):
    """
    Build the command to run the enhanced incremental tests script.

    Args:
        args: Command line arguments

    Returns:
        list: Command to run as a list of strings
    """
    # Start with the base command
    cmd = ["python", "scripts/run_modified_tests_enhanced.py"]

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

    # Add prioritize flag (from args or preset)
    prioritize = args.prioritize if args.prioritize else preset.get("prioritize", False)
    if prioritize:
        cmd.append("--prioritize")

    # Add balanced flag (from args or preset)
    balanced = args.balanced if args.balanced else preset.get("balanced", False)
    if balanced:
        cmd.append("--balanced")

    # Add max-tests (from args or preset)
    max_tests = args.max_tests if args.max_tests > 0 else preset.get("max_tests", 0)
    if max_tests > 0:
        cmd.extend(["--max-tests", str(max_tests)])

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


def check_script_exists():
    """
    Check if the enhanced script exists, and create it if it doesn't.

    Returns:
        bool: True if the script exists or was created, False otherwise
    """
    script_path = "scripts/run_modified_tests_enhanced.py"
    if not os.path.exists(script_path):
        print(f"Warning: {script_path} not found.")

        # Check if the original script exists
        original_path = "scripts/run_modified_tests.py"
        if not os.path.exists(original_path):
            print(f"Error: {original_path} not found. Cannot create enhanced script.")
            return False

        print("Creating enhanced script from original...")

        # Create a simple wrapper that calls the original script
        with open(script_path, "w") as f:
            f.write(
                """#!/usr/bin/env python
'''
Enhanced wrapper for run_modified_tests.py.
This is a temporary wrapper until the enhanced script is fully implemented.
'''
import sys
import os
import subprocess

if __name__ == '__main__':
    # Forward all arguments to the original script
    cmd = [sys.executable, 'scripts/run_modified_tests.py'] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
"""
            )

        print(f"Created temporary wrapper at {script_path}")
        os.chmod(script_path, 0o755)  # Make executable

    return True


def log_run(cmd, preset_name, preset_description):
    """
    Log the test run to a history file.

    Args:
        cmd: Command that was run
        preset_name: Name of the preset used
        preset_description: Description of the preset
    """
    history_dir = ".test_history"
    os.makedirs(history_dir, exist_ok=True)

    history_file = os.path.join(history_dir, "incremental_test_runs.json")

    # Load existing history
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
        except json.JSONDecodeError:
            # Invalid file, start with empty history
            pass

    # Add new entry
    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(cmd),
            "preset": preset_name,
            "description": preset_description,
        }
    )

    # Keep only the last 100 entries
    if len(history) > 100:
        history = history[-100:]

    # Save history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def main():
    """Main function."""
    args = parse_args()

    # Check if the enhanced script exists
    if not check_script_exists():
        sys.exit(1)

    # Build the command
    cmd = build_command(args)

    # Print the command
    print(f"Running: {' '.join(cmd)}")
    print(f"Preset: {args.preset} - {PRESETS[args.preset]['description']}")

    # Execute the command if not a dry run
    if not args.dry_run:
        try:
            # Log the run
            log_run(cmd, args.preset, PRESETS[args.preset]["description"])

            # Execute the command
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running incremental tests: {e}")
            sys.exit(1)
    else:
        print("Dry run - not executing tests")


if __name__ == "__main__":
    main()
