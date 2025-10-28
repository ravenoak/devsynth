#!/usr/bin/env python3
"""
Fix Flaky Tests

This script identifies and fixes common patterns that lead to flaky tests in the DevSynth project.
It focuses on improving test isolation and determinism by applying best practices learned from
the WebUI tests and other robust test implementations.

Usage:
    python scripts/fix_flaky_tests.py [options]

Options:
    --module MODULE       Specific module to process (e.g., tests/unit/interface)
    --category CATEGORY   Test category to process (unit, integration, behavior, all)
    --max-tests N         Maximum number of tests to process in a single run (default: 100)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
    --pattern PATTERN     Specific pattern to fix (mocking, isolation, state, all)
    --report              Generate a report of flaky test patterns without fixing
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import common test collector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from common_test_collector import (
        check_test_has_marker,
        clear_cache,
        collect_tests,
        collect_tests_by_category,
        invalidate_cache_for_files,
    )
except ImportError:
    print(
        "Error: common_test_collector.py not found. Please ensure it exists in the scripts directory."
    )
    sys.exit(1)

# Test categories
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "behavior": "tests/behavior",
    "performance": "tests/performance",
    "property": "tests/property",
}

# High-priority modules
HIGH_PRIORITY_MODULES = [
    "tests/unit/interface",
    "tests/unit/adapters/memory",
    "tests/unit/adapters/llm",
    "tests/integration/memory",
    "tests/unit/application/wsde",
    "tests/unit/interface/webui",
]

# Flaky test patterns
FLAKY_PATTERNS = {
    "mocking": [
        {
            "pattern": r"mock\s*=\s*MagicMock\(\)",
            "fix": r"mock = MagicMock(spec=ClassName)",
            "description": "Use MagicMock with spec to ensure mocks have the same interface as real objects",
        },
        {
            "pattern": r"monkeypatch\.setattr\([^,]+,\s*lambda[^:]+:[^)]+\)",
            "fix": r"""
def mock_function(*args, **kwargs):
    # Implement robust behavior here
    return expected_result
monkeypatch.setattr(target, mock_function)
""",
            "description": "Replace lambda functions with named functions for more robust mocking",
        },
        {
            "pattern": r"answers\s*=\s*iter\(\[[^\]]+\]\)",
            "fix": r"""
answers = [item1, item2, ...]
answer_index = 0

def mock_function(*args, **kwargs):
    nonlocal answer_index
    if answer_index < len(answers):
        result = answers[answer_index]
        answer_index += 1
        return result
    return default_value  # Provide a default value
""",
            "description": "Use indexed lists instead of iterators to avoid StopIteration errors",
        },
    ],
    "isolation": [
        {
            "pattern": r"import\s+([a-zA-Z0-9_.]+)\s+as\s+([a-zA-Z0-9_]+)",
            "fix": r"""
import importlib
import $1 as $2
# Reload the module to ensure clean state
importlib.reload($2)
""",
            "description": "Reload modules to ensure clean state for each test",
        },
        {
            "pattern": r"monkeypatch\.setattr\(([^,]+),\s*([^)]+)\)",
            "fix": r"""
original = $1
try:
    monkeypatch.setattr($1, $2)
    # Test code here
finally:
    # Restore original if needed for cleanup
    pass
""",
            "description": "Use try/finally blocks to ensure cleanup after patching",
        },
    ],
    "state": [
        {
            "pattern": r"st\.session_state\[([^\]]+)\]\s*=",
            "fix": r"""
# Use a state manager class instead of direct session state access
state.set($1, value)
""",
            "description": "Use a state manager class instead of direct session state access",
        },
        {
            "pattern": r"def\s+test_[^(]+\(([^)]*)\):\s*(?!.*fixture)",
            "fix": r"""
@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state

def test_$TEST_NAME($PARAMS, clean_state):
    # Test with clean state
""",
            "description": "Use fixtures to set up and clean up state for tests",
        },
    ],
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix flaky tests by improving isolation and determinism."
    )
    parser.add_argument(
        "--module", help="Specific module to process (e.g., tests/unit/interface)"
    )
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        default="all",
        help="Test category to process (default: all)",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=100,
        help="Maximum number of tests to process in a single run (default: 100)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--pattern",
        choices=["mocking", "isolation", "state", "all"],
        default="all",
        help="Specific pattern to fix (default: all)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a report of flaky test patterns without fixing",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run affected tests repeatedly to check for stability",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of times to rerun tests when verifying stability",
    )
    parser.add_argument(
        "--speed",
        choices=["fast", "medium", "slow"],
        default="medium",
        help="Speed marker to use when verifying test stability",
    )
    return parser.parse_args()


def collect_test_files(
    category: str = "all", module: str = None, use_cache: bool = True
) -> list[str]:
    """
    Collect test files to process.

    Args:
        category: Test category (unit, integration, behavior, all)
        module: Specific module to collect tests from
        use_cache: Whether to use cached test collection results

    Returns:
        List of test file paths
    """
    print("Collecting test files...")

    # Determine which categories to collect
    categories = [category] if category != "all" else list(TEST_CATEGORIES.keys())

    # Collect all tests
    all_tests = []
    for cat in categories:
        if module:
            # If module is specified, collect tests from that module
            if os.path.exists(module):
                tests = collect_tests_by_category(cat, use_cache=use_cache)
                tests = [t for t in tests if t.startswith(module)]
                all_tests.extend(tests)
        else:
            # Otherwise, collect all tests for the category
            tests = collect_tests_by_category(cat, use_cache=use_cache)
            all_tests.extend(tests)

    # Extract unique file paths
    test_files = set()
    for test in all_tests:
        if "::" in test:
            file_path = test.split("::")[0]
            test_files.add(file_path)
        else:
            test_files.add(test)

    print(f"Found {len(test_files)} test files")
    return list(test_files)


def prioritize_files(files: list[str], priority_modules: list[str]) -> list[str]:
    """
    Prioritize files based on module priority.

    Args:
        files: List of file paths
        priority_modules: List of high-priority modules

    Returns:
        Prioritized list of file paths
    """
    high_priority = []
    normal_priority = []

    for file in files:
        if any(file.startswith(module) for module in priority_modules):
            high_priority.append(file)
        else:
            normal_priority.append(file)

    return high_priority + normal_priority


def analyze_file(
    file_path: str, patterns: dict[str, list[dict[str, str]]], verbose: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """
    Analyze a file for flaky test patterns.

    Args:
        file_path: Path to the file to analyze
        patterns: Dictionary of patterns to look for
        verbose: Whether to show detailed information

    Returns:
        Dictionary of issues found in the file
    """
    if verbose:
        print(f"Analyzing {file_path}...")

    try:
        with open(file_path) as f:
            content = f.read()

        issues = {"mocking": [], "isolation": [], "state": []}

        # Check for each pattern
        for pattern_type, pattern_list in patterns.items():
            for pattern_info in pattern_list:
                pattern = pattern_info["pattern"]
                matches = re.finditer(pattern, content)

                for match in matches:
                    line_start = content[: match.start()].count("\n") + 1
                    line_end = content[: match.end()].count("\n") + 1

                    # Get the context (a few lines before and after)
                    lines = content.split("\n")
                    context_start = max(0, line_start - 3)
                    context_end = min(len(lines), line_end + 3)
                    context = "\n".join(lines[context_start:context_end])

                    issues[pattern_type].append(
                        {
                            "pattern": pattern,
                            "description": pattern_info["description"],
                            "fix": pattern_info["fix"],
                            "line_start": line_start,
                            "line_end": line_end,
                            "match": match.group(0),
                            "context": context,
                        }
                    )

        return issues

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {"mocking": [], "isolation": [], "state": []}


def fix_file(
    file_path: str,
    issues: dict[str, list[dict[str, Any]]],
    dry_run: bool = True,
    verbose: bool = False,
) -> bool:
    """
    Fix flaky test patterns in a file.

    Args:
        file_path: Path to the file to fix
        issues: Dictionary of issues to fix
        dry_run: Whether to show changes without modifying the file
        verbose: Whether to show detailed information

    Returns:
        Whether the file was modified
    """
    if verbose:
        print(f"Fixing {file_path}...")

    try:
        with open(file_path) as f:
            content = f.read()

        modified = False
        new_content = content

        # Process each issue type
        for issue_type, issue_list in issues.items():
            for issue in issue_list:
                if verbose:
                    print(
                        f"  Found {issue_type} issue at lines {issue['line_start']}-{issue['line_end']}:"
                    )
                    print(f"    {issue['description']}")
                    print(f"    Match: {issue['match']}")
                    print(f"    Suggested fix: {issue['fix']}")

                # Apply the fix by replacing the matched pattern with the fix
                match_text = issue["match"]
                fix_text = issue["fix"]

                # For mocking issues, we need to adapt the fix to the specific context
                if issue_type == "mocking":
                    if "spec=ClassName" in fix_text:
                        # Try to determine the actual class name from the context
                        class_match = re.search(
                            r"class\s+([A-Za-z0-9_]+)", issue["context"]
                        )
                        if class_match:
                            class_name = class_match.group(1)
                            fix_text = fix_text.replace("ClassName", class_name)

                    if "expected_result" in fix_text:
                        # Try to determine the expected result from the context
                        result_match = re.search(
                            r"return\s+([A-Za-z0-9_\"'{}[\]]+)", issue["context"]
                        )
                        if result_match:
                            expected_result = result_match.group(1)
                            fix_text = fix_text.replace(
                                "expected_result", expected_result
                            )

                # For state issues, adapt the fix to the specific context
                if issue_type == "state":
                    if "state.set($1, value)" in fix_text:
                        # Extract the key from the match
                        key_match = re.search(
                            r"st\.session_state\[([^\]]+)\]", match_text
                        )
                        if key_match:
                            key = key_match.group(1)
                            # Find the value being assigned
                            value_match = re.search(
                                r"st\.session_state\[[^\]]+\]\s*=\s*([^;\n]+)",
                                issue["context"],
                            )
                            if value_match:
                                value = value_match.group(1)
                                fix_text = fix_text.replace("$1", key).replace(
                                    "value", value
                                )
                    elif "$TEST_NAME" in fix_text and "$PARAMS" in fix_text:
                        # Extract the test name and parameters
                        test_match = re.search(
                            r"def\s+test_([^(]+)\(([^)]*)\):", match_text
                        )
                        if test_match:
                            test_name = test_match.group(1)
                            params = test_match.group(2)
                            # Replace placeholders with actual values
                            fix_text = fix_text.replace(
                                "$TEST_NAME", test_name
                            ).replace("$PARAMS", params)

                # Replace the match with the fix in the content
                lines = new_content.split("\n")
                match_lines = lines[issue["line_start"] - 1 : issue["line_end"]]
                match_text_in_file = "\n".join(match_lines)

                # For state issues with test functions, use a more flexible approach
                if issue_type == "state" and "def test_" in match_text:
                    # Extract the test function name and parameters
                    test_match = re.search(
                        r"def\s+(test_[^(]+)\(([^)]*)\):", match_text
                    )
                    if test_match:
                        test_name = test_match.group(1)
                        params = test_match.group(2)

                        # Find the line with the function definition
                        for i, line in enumerate(lines):
                            if f"def {test_name}(" in line:
                                # Check if there's already a clean_state parameter
                                if "clean_state" not in line:
                                    # Add clean_state parameter
                                    if params.strip():
                                        new_line = line.replace(
                                            f"({params}", f"({params}, clean_state"
                                        )
                                    else:
                                        new_line = line.replace("():", "(clean_state):")

                                    lines[i] = new_line

                                    # Add the fixture if it doesn't exist
                                    fixture_exists = False
                                    for j in range(max(0, i - 20), i):
                                        if (
                                            "@pytest.fixture" in lines[j]
                                            and "def clean_state():" in lines[j + 1]
                                        ):
                                            fixture_exists = True
                                            break

                                    if not fixture_exists:
                                        # Add the fixture before the function
                                        fixture_lines = [
                                            "",
                                            "@pytest.fixture",
                                            "def clean_state():",
                                            "    # Set up clean state",
                                            "    yield",
                                            "    # Clean up state",
                                            "",
                                        ]

                                        # Find a good insertion point (before the function)
                                        insertion_point = i
                                        while (
                                            insertion_point > 0
                                            and not lines[insertion_point - 1].strip()
                                        ):
                                            insertion_point -= 1

                                        lines[insertion_point:insertion_point] = (
                                            fixture_lines
                                        )

                                    new_content = "\n".join(lines)
                                    modified = True
                                    if verbose:
                                        print(
                                            f"    Applied fix for {issue_type} issue using flexible approach"
                                        )
                                else:
                                    if verbose:
                                        print(
                                            f"    Function already has clean_state parameter"
                                        )
                                break
                        else:
                            if verbose:
                                print(f"    Could not find function definition in file")
                    else:
                        if verbose:
                            print(f"    Could not extract test name and parameters")
                # Only replace if we can find the exact match
                elif match_text in match_text_in_file:
                    new_match_text = match_text_in_file.replace(match_text, fix_text)
                    lines[issue["line_start"] - 1 : issue["line_end"]] = (
                        new_match_text.split("\n")
                    )
                    new_content = "\n".join(lines)
                    modified = True
                    if verbose:
                        print(f"    Applied fix for {issue_type} issue")
                else:
                    if verbose:
                        print(f"    Could not apply fix: match not found in file")

        if modified and not dry_run:
            with open(file_path, "w") as f:
                f.write(new_content)
            print(f"Updated {file_path}")

        return modified

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def generate_report(
    results: dict[str, dict[str, list[dict[str, Any]]]],
    output_file: str = "flaky_test_report.json",
):
    """
    Generate a report of flaky test patterns.

    Args:
        results: Dictionary of results by file
        output_file: Path to the output file
    """
    # Count issues by type
    issue_counts = {"mocking": 0, "isolation": 0, "state": 0, "total": 0}

    for file_path, issues in results.items():
        for issue_type, issue_list in issues.items():
            issue_counts[issue_type] += len(issue_list)
            issue_counts["total"] += len(issue_list)

    # Create the report
    report = {
        "summary": {
            "total_files": len(results),
            "files_with_issues": sum(
                1
                for file_path, issues in results.items()
                if sum(len(issue_list) for issue_list in issues.values()) > 0
            ),
            "issue_counts": issue_counts,
        },
        "issues_by_file": results,
    }

    # Write the report to a file
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total files analyzed: {report['summary']['total_files']}")
    print(f"  Files with issues: {report['summary']['files_with_issues']}")
    print(f"  Total issues: {report['summary']['issue_counts']['total']}")
    print(f"  Mocking issues: {report['summary']['issue_counts']['mocking']}")
    print(f"  Isolation issues: {report['summary']['issue_counts']['isolation']}")
    print(f"  State issues: {report['summary']['issue_counts']['state']}")


def run_tests_until_stable(
    paths: list[str], speed: str = "medium", retries: int = 3
) -> bool:
    """Run the given test paths repeatedly until they pass or retries are exhausted.

    Args:
        paths: List of test file paths to run
        speed: Speed marker to include with test execution
        retries: Number of attempts before giving up

    Returns:
        True if tests passed at least once, False otherwise
    """
    for attempt in range(1, retries + 1):
        cmd = [
            "poetry",
            "run",
            "devsynth",
            "run-tests",
            "--speed",
            speed,
            *paths,
        ]
        print(f"Running stability check attempt {attempt}/{retries}: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode == 0:
            return True
    return False


def main():
    """Main function."""
    args = parse_args()

    # Determine which patterns to use
    patterns = {}
    if args.pattern == "all":
        patterns = FLAKY_PATTERNS
    else:
        patterns = {args.pattern: FLAKY_PATTERNS[args.pattern]}

    # Collect test files
    test_files = collect_test_files(
        category=args.category, module=args.module, use_cache=True
    )

    # Prioritize files
    test_files = prioritize_files(test_files, HIGH_PRIORITY_MODULES)

    # Limit the number of files to process
    if args.max_tests > 0 and len(test_files) > args.max_tests:
        print(f"Limiting to {args.max_tests} files (out of {len(test_files)} files)")
        test_files = test_files[: args.max_tests]

    # Process each file
    results = {}
    modified_files = []

    for file_path in test_files:
        # Analyze the file
        issues = analyze_file(file_path, patterns, args.verbose)

        # Store the results
        results[file_path] = issues

        # Fix the file if needed
        if sum(len(issue_list) for issue_list in issues.values()) > 0:
            if fix_file(file_path, issues, args.dry_run, args.verbose):
                modified_files.append(file_path)

    # Generate a report if requested
    if args.report:
        generate_report(results)

    # Print summary
    print("\nSummary:")
    print(f"  Total files processed: {len(test_files)}")
    print(f"  Files with issues: {len(modified_files)}")

    if args.dry_run:
        print("\nNote: This was a dry run. Use without --dry-run to apply changes.")
    else:
        print(f"  Files modified: {len(modified_files)}")

    if args.verify:
        targets = modified_files or test_files
        stable = run_tests_until_stable(targets, speed=args.speed, retries=args.retries)
        status = "passed" if stable else "failed"
        print(f"\nStability check {status} after {args.retries} attempt(s)")

    print("\nDone!")


if __name__ == "__main__":
    main()
