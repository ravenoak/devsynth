#!/usr/bin/env python3
"""
Pre-commit hook script to check for alignment issues between SDLC artifacts.

This script checks for basic alignment issues like missing references to requirements
in specifications, missing references to specifications in tests, and missing references
to tests in code.

Usage:
    1. Install as a pre-commit hook:
       cp scripts/alignment_check.py .git/hooks/pre-commit
       chmod +x .git/hooks/pre-commit
    
    2. Run manually:
       python scripts/alignment_check.py [--files file1 file2 ...]
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Set, Tuple

# Regular expressions for finding references
REQ_REF_PATTERN = re.compile(r'FR-\d+|NFR-\d+')
SPEC_REF_PATTERN = re.compile(r'SPEC-\d+')
TEST_REF_PATTERN = re.compile(r'TEST-\d+')

# File patterns for different artifact types
REQUIREMENT_FILES = ['docs/requirements/', 'docs/system_requirements_specification.md']
SPECIFICATION_FILES = ['docs/specifications/']
TEST_FILES = ['tests/']
CODE_FILES = ['src/']

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Check alignment between SDLC artifacts')
    parser.add_argument('--files', nargs='+', help='Specific files to check')
    return parser.parse_args()

def get_changed_files() -> List[str]:
    """Get list of files changed in the current commit."""
    try:
        # Get staged files
        import subprocess
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()
    except Exception as e:
        print(f"Error getting changed files: {e}")
        return []

def is_file_of_type(file_path: str, type_patterns: List[str]) -> bool:
    """Check if a file matches any of the given patterns."""
    return any(pattern in file_path for pattern in type_patterns)

def extract_references(file_path: str, pattern: re.Pattern) -> Set[str]:
    """Extract references matching the given pattern from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return set(pattern.findall(content))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return set()

def check_requirement_references(files: List[str]) -> List[str]:
    """Check if specifications reference requirements."""
    issues = []
    
    # Get all requirement IDs
    all_requirements = set()
    for file in files:
        if is_file_of_type(file, REQUIREMENT_FILES):
            all_requirements.update(extract_references(file, REQ_REF_PATTERN))
    
    # Check specifications for requirement references
    for file in files:
        if is_file_of_type(file, SPECIFICATION_FILES):
            spec_requirements = extract_references(file, REQ_REF_PATTERN)
            if not spec_requirements:
                issues.append(f"Specification {file} does not reference any requirements")
    
    return issues

def check_specification_references(files: List[str]) -> List[str]:
    """Check if tests reference specifications."""
    issues = []
    
    # Get all specification IDs
    all_specifications = set()
    for file in files:
        if is_file_of_type(file, SPECIFICATION_FILES):
            all_specifications.update(extract_references(file, SPEC_REF_PATTERN))
    
    # Check tests for specification references
    for file in files:
        if is_file_of_type(file, TEST_FILES):
            test_specifications = extract_references(file, SPEC_REF_PATTERN)
            if not test_specifications:
                issues.append(f"Test {file} does not reference any specifications")
    
    return issues

def check_test_references(files: List[str]) -> List[str]:
    """Check if code references tests."""
    issues = []
    
    # Get all test IDs
    all_tests = set()
    for file in files:
        if is_file_of_type(file, TEST_FILES):
            all_tests.update(extract_references(file, TEST_REF_PATTERN))
    
    # Check code for test references
    for file in files:
        if is_file_of_type(file, CODE_FILES) and file.endswith('.py'):
            code_tests = extract_references(file, TEST_REF_PATTERN)
            if not code_tests:
                issues.append(f"Code {file} does not reference any tests")
    
    return issues

def check_alignment(files: List[str]) -> List[str]:
    """Check alignment between SDLC artifacts."""
    issues = []
    
    # Only check files that exist
    existing_files = [f for f in files if os.path.isfile(f)]
    
    # Run checks
    issues.extend(check_requirement_references(existing_files))
    issues.extend(check_specification_references(existing_files))
    issues.extend(check_test_references(existing_files))
    
    return issues

def main():
    """Main function."""
    args = parse_args()
    
    # Get files to check
    if args.files:
        files = args.files
    else:
        files = get_changed_files()
    
    if not files:
        print("No files to check")
        return 0
    
    # Check alignment
    issues = check_alignment(files)
    
    # Print issues
    if issues:
        print("Alignment issues found:")
        for issue in issues:
            print(f"  - {issue}")
        
        print("\nYou can bypass this check with git commit --no-verify")
        return 1
    
    print("No alignment issues found")
    return 0

if __name__ == "__main__":
    sys.exit(main())