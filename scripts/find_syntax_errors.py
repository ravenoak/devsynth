#!/usr/bin/env python3
"""
Script to find syntax errors in Python files.

This script checks for syntax errors in Python files and prints the file names
along with the syntax errors.

Usage:
    python scripts/find_syntax_errors.py [--module MODULE]

Options:
    --module MODULE    Module to check (default: interface)
"""

import os
import sys
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Find syntax errors in Python files."
    )
    parser.add_argument(
        "--module",
        type=str,
        default="interface",
        help="Module to check (default: interface)",
    )
    return parser.parse_args()


def collect_test_files(module: str) -> List[str]:
    """Collect test files from the specified module.

    Args:
        module: The module to collect test files from

    Returns:
        List of file paths
    """
    test_dir = os.path.join("tests", "unit", module)
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return []

    test_files = []
    for root, _, files in os.walk(test_dir):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                test_files.append(os.path.join(root, f))

    return sorted(test_files)


def check_syntax(file_path: str) -> Optional[str]:
    """Check if a file has syntax errors.

    Args:
        file_path: Path to the file to check

    Returns:
        Error message if there are syntax errors, None otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno}, column {e.offset})"
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    """Main function."""
    args = parse_args()
    
    # Collect test files
    test_files = collect_test_files(args.module)
    if not test_files:
        print("No test files found")
        return
    
    print(f"Found {len(test_files)} test files")
    
    # Check each file for syntax errors
    files_with_errors = []
    for file_path in test_files:
        error = check_syntax(file_path)
        if error:
            files_with_errors.append((file_path, error))
    
    # Print the results
    if files_with_errors:
        print(f"\nFound {len(files_with_errors)} files with syntax errors:")
        for file_path, error in files_with_errors:
            print(f"  {file_path}: {error}")
    else:
        print("\nNo syntax errors found")


if __name__ == "__main__":
    main()