#!/usr/bin/env python3
"""
Enhanced script to fix syntax errors in interface module test files.

This script builds on fix_interface_syntax.py with additional capabilities to handle:
1. Commented-out closing parentheses
2. Missing indented blocks after statements that require them
3. Invalid syntax like undefined variables and unreachable code
4. Placeholder variables like $2

Usage:
    python scripts/fix_interface_syntax_v2.py [--dry-run] [--verbose] [--file FILE]

Options:
    --dry-run       Don't actually write changes to files
    --verbose       Print detailed information about fixes
    --file FILE     Process only the specified file
"""

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fix syntax errors in interface module test files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write changes to files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed information about fixes",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process only the specified file",
    )
    parser.add_argument(
        "--module",
        type=str,
        default="interface",
        help="Module to process (default: interface)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="interface_syntax_report_v2.json",
        help="Output file for the report (default: interface_syntax_report_v2.json)",
    )
    return parser.parse_args()


def collect_test_files(module: str, file: str = None) -> list[str]:
    """Collect test files from the specified module.

    Args:
        module: The module to collect test files from
        file: Optional specific file to process

    Returns:
        List of file paths
    """
    if file:
        if os.path.exists(file):
            return [file]
        # Try to find the file in the tests directory
        test_file = os.path.join("tests", "unit", module, file)
        if os.path.exists(test_file):
            return [test_file]
        print(f"File not found: {file}")
        return []

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


def check_syntax(file_path: str) -> str | None:
    """Check if a file has syntax errors.

    Args:
        file_path: Path to the file to check

    Returns:
        Error message if there are syntax errors, None otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno}, column {e.offset})"
    except Exception as e:
        return f"Error: {str(e)}"


def fix_indentation_errors(content: str, verbose: bool = False) -> str:
    """Fix indentation errors in the content.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    try:
        tree = ast.parse(content)
        return fix_indentation_with_ast(content, tree, verbose)
    except SyntaxError:
        if verbose:
            print("  AST parsing failed, trying line-by-line indentation fix")
        return fix_indentation_line_by_line(content, verbose)


def fix_indentation_with_ast(content: str, tree: ast.AST, verbose: bool = False) -> str:
    """Fix indentation using AST.

    Args:
        content: The content to fix
        tree: The AST tree
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # This is a placeholder for more sophisticated AST-based indentation fixing
    # For now, we'll just return the original content
    return content


def fix_indentation_line_by_line(content: str, verbose: bool = False) -> str:
    """Fix indentation line by line.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []
    indent_stack = [0]  # Stack to track indentation levels
    expecting_indent = False
    indent_keywords = {
        "if",
        "else",
        "elif",
        "for",
        "while",
        "def",
        "class",
        "with",
        "try",
        "except",
        "finally",
    }

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            fixed_lines.append(line)
            continue

        # Check if this line should be indented
        if expecting_indent:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_stack[-1]:
                # Line needs indentation
                if verbose:
                    print(f"  Line {i+1}: Adding indentation")
                line = " " * (indent_stack[-1] + 4) + line.lstrip()
            expecting_indent = False

        # Check if the next line should be indented
        if stripped.endswith(":"):
            indent_stack.append(len(line) - len(line.lstrip()))
            expecting_indent = True

        # Check for closing blocks
        if stripped in ("return", "break", "continue", "pass") or stripped.startswith(
            "return "
        ):
            if len(indent_stack) > 1:
                indent_stack.pop()

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_try_except_blocks(content: str, verbose: bool = False) -> str:
    """Fix try/except blocks with missing indented blocks.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("try:"):
            indent = len(line) - len(line.lstrip())
            next_line_idx = i + 1

            # Check if the next line exists and has proper indentation
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if (
                    next_line.strip()
                    and len(next_line) - len(next_line.lstrip()) <= indent
                ):
                    # Missing indented block after try
                    if verbose:
                        print(f"  Line {i+1}: Adding pass statement after try")
                    fixed_lines.append(line)
                    fixed_lines.append(" " * (indent + 4) + "pass")
                    i += 1
                    continue

        elif stripped.startswith("with ") and stripped.endswith(":"):
            indent = len(line) - len(line.lstrip())
            next_line_idx = i + 1

            # Check if the next line exists and has proper indentation
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if (
                    next_line.strip()
                    and len(next_line) - len(next_line.lstrip()) <= indent
                ):
                    # Missing indented block after with
                    if verbose:
                        print(f"  Line {i+1}: Adding pass statement after with")
                    fixed_lines.append(line)
                    fixed_lines.append(" " * (indent + 4) + "pass")
                    i += 1
                    continue

        elif stripped.startswith("for ") and stripped.endswith(":"):
            indent = len(line) - len(line.lstrip())
            next_line_idx = i + 1

            # Check if the next line exists and has proper indentation
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]
                if (
                    next_line.strip()
                    and len(next_line) - len(next_line.lstrip()) <= indent
                ):
                    # Missing indented block after for
                    if verbose:
                        print(f"  Line {i+1}: Adding pass statement after for")
                    fixed_lines.append(line)
                    fixed_lines.append(" " * (indent + 4) + "pass")
                    i += 1
                    continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def remove_duplicate_fixtures(content: str, verbose: bool = False) -> str:
    """Remove duplicate fixture definitions.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixture_names = set()
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("@pytest.fixture"):
            # Look for the fixture name in the next line
            if i + 1 < len(lines) and "def " in lines[i + 1]:
                fixture_def = lines[i + 1]
                fixture_name = fixture_def.split("def ")[1].split("(")[0].strip()

                if fixture_name in fixture_names:
                    # Skip this duplicate fixture
                    if verbose:
                        print(
                            f"  Line {i+1}: Removing duplicate fixture {fixture_name}"
                        )

                    # Skip the decorator line
                    i += 1

                    # Skip the function definition line
                    i += 1

                    # Skip the function body until we find a line with the same indentation as the function definition
                    indent = len(fixture_def) - len(fixture_def.lstrip())
                    while i < len(lines):
                        if (
                            not lines[i].strip()
                            or len(lines[i]) - len(lines[i].lstrip()) > indent
                        ):
                            i += 1
                        else:
                            break

                    continue
                else:
                    fixture_names.add(fixture_name)

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_test_function_indentation(content: str, verbose: bool = False) -> str:
    """Fix indentation in test functions.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []
    in_test_function = False
    test_indent = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("def test_") and stripped.endswith(":"):
            # Start of a test function
            in_test_function = True
            test_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue

        if in_test_function:
            if not stripped:
                # Empty line, keep as is
                fixed_lines.append(line)
                continue

            current_indent = len(line) - len(line.lstrip())

            if (
                current_indent <= test_indent
                and stripped
                and not stripped.startswith("#")
            ):
                # End of the test function
                in_test_function = False
                fixed_lines.append(line)
                continue

            if current_indent <= test_indent and stripped.startswith("def "):
                # New function, end of the test function
                in_test_function = False

            if in_test_function and current_indent <= test_indent:
                # Line inside test function with incorrect indentation
                if verbose:
                    print(f"  Line {i+1}: Fixing indentation in test function")
                line = " " * (test_indent + 4) + stripped

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_placeholder_variables(content: str, verbose: bool = False) -> str:
    """Fix placeholder variables like $2.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # Pattern to match $n where n is a number
    pattern = r"\$(\d+)"

    def replace_placeholder(match):
        num = match.group(1)
        if verbose:
            print(f"  Replacing placeholder ${num} with 'module_{num}'")
        return f"module_{num}"

    fixed_content = re.sub(pattern, replace_placeholder, content)

    return fixed_content


def fix_test_function_structure(content: str, verbose: bool = False) -> str:
    """Fix structural issues in test functions.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Fix unreachable code after return statements
        if stripped.startswith("return ") or stripped == "return":
            fixed_lines.append(line)

            # Check if the next line exists and is indented at the same level
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()

                if next_stripped and len(next_line) - len(next_line.lstrip()) == len(
                    line
                ) - len(line.lstrip()):
                    # Unreachable code after return
                    if verbose:
                        print(f"  Line {i+2}: Moving unreachable code before return")

                    # Remove the last added line (return statement)
                    fixed_lines.pop()

                    # Add the next line before the return
                    fixed_lines.append(next_line)
                    fixed_lines.append(line)

                    # Skip the next line since we've already processed it
                    i += 1
                    continue
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_line_continuation(content: str, verbose: bool = False) -> str:
    """Fix line continuation issues.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for dictionary access split across lines
        if stripped.endswith("[") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.endswith("]"):
                # Dictionary access split across lines
                if verbose:
                    print(f"  Line {i+1}: Fixing split dictionary access")
                fixed_lines.append(line + next_line)
                i += 2
                continue

        # Check for function calls split across lines
        if "(" in stripped and ")" not in stripped and not stripped.endswith(","):
            # Function call might be split across lines
            combined_line = stripped
            j = i + 1

            while j < len(lines) and ")" not in lines[j].strip():
                combined_line += " " + lines[j].strip()
                j += 1

            if j < len(lines) and ")" in lines[j].strip():
                combined_line += " " + lines[j].strip()

                if verbose:
                    print(f"  Line {i+1}: Combining split function call")

                fixed_lines.append(" " * (len(line) - len(stripped)) + combined_line)
                i = j + 1
                continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_unclosed_parentheses(content: str, verbose: bool = False) -> str:
    """Fix unclosed parentheses, including commented-out closing parentheses.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # First, uncomment any commented-out closing parentheses
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#") and ")" in stripped:
            # Check if this is a commented-out closing parenthesis
            if re.search(r"#\s*\)", stripped):
                # Uncomment the closing parenthesis
                if verbose:
                    print(f"  Line {i+1}: Uncommenting closing parenthesis")
                fixed_lines.append(")")
                continue

        fixed_lines.append(line)

    fixed_content = "\n".join(fixed_lines)

    # Now check for any remaining unclosed parentheses
    try:
        ast.parse(fixed_content)
        return fixed_content
    except SyntaxError as e:
        if (
            "unexpected EOF while parsing" in str(e)
            or "unclosed" in str(e)
            or "was never closed" in str(e)
        ):
            # Still have unclosed parentheses, try to fix them
            if verbose:
                print(f"  Still have unclosed parentheses, trying to fix")

            # Count opening and closing parentheses
            open_count = fixed_content.count("(")
            close_count = fixed_content.count(")")

            if open_count > close_count:
                # Add missing closing parentheses
                missing = open_count - close_count
                if verbose:
                    print(f"  Adding {missing} closing parentheses")
                fixed_content += "\n" + ")" * missing

    return fixed_content


def fix_extra_blank_lines(content: str, verbose: bool = False) -> str:
    """Fix extra blank lines.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # Replace 3 or more consecutive blank lines with 2 blank lines
    if verbose:
        print("  Fixing extra blank lines")

    fixed_content = re.sub(r"\n{3,}", "\n\n", content)

    return fixed_content


def fix_undefined_variables(content: str, verbose: bool = False) -> str:
    """Fix undefined variables.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # Common undefined variables and their replacements
    replacements = {
        "expected_result": "'expected_result'",
        "target": "'target'",
    }

    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        fixed_line = line

        for var, replacement in replacements.items():
            # Only replace if it's a standalone variable (not part of another word)
            pattern = r"\b" + var + r"\b"
            if re.search(pattern, line):
                if verbose:
                    print(
                        f"  Line {i+1}: Replacing undefined variable {var} with {replacement}"
                    )
                fixed_line = re.sub(pattern, replacement, fixed_line)

        fixed_lines.append(fixed_line)

    return "\n".join(fixed_lines)


def fix_missing_comma(content: str, verbose: bool = False) -> str:
    """Fix missing commas in lists, dictionaries, and function calls.

    Args:
        content: The content to fix
        verbose: Whether to print verbose output

    Returns:
        Fixed content
    """
    # This is a complex problem that would require more sophisticated parsing
    # For now, we'll just look for common patterns

    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for missing comma in dictionary
        if re.search(r"\w+\s*:\s*\w+\s*\w+\s*:", stripped):
            # Might be missing a comma between dictionary items
            fixed_line = re.sub(r"(\w+\s*:\s*\w+)\s+(\w+\s*:)", r"\1, \2", stripped)
            if verbose and fixed_line != stripped:
                print(f"  Line {i+1}: Adding missing comma in dictionary")
            fixed_lines.append(" " * (len(line) - len(stripped)) + fixed_line)
            continue

        # Check for missing comma in list
        if re.search(r"\[\s*\w+\s+\w+", stripped) or re.search(
            r"\w+\s+\w+\s*\]", stripped
        ):
            # Might be missing a comma in a list
            fixed_line = re.sub(r"(\w+)\s+(\w+)", r"\1, \2", stripped)
            if verbose and fixed_line != stripped:
                print(f"  Line {i+1}: Adding missing comma in list")
            fixed_lines.append(" " * (len(line) - len(stripped)) + fixed_line)
            continue

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_file(
    file_path: str, dry_run: bool = True, verbose: bool = False
) -> dict[str, Any]:
    """Fix syntax errors in a file.

    Args:
        file_path: Path to the file to fix
        dry_run: Whether to actually write changes to the file
        verbose: Whether to print verbose output

    Returns:
        Dictionary with the results of the fix
    """
    if verbose:
        print(f"Processing {file_path}")

    # Check if the file has syntax errors
    error = check_syntax(file_path)
    if not error:
        if verbose:
            print("  No syntax errors found")
        return {"status": "no_errors"}

    if verbose:
        print(f"  Found syntax error: {error}")

    # Read the file content
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Apply fixes
    original_content = content

    # Fix undefined variables first
    content = fix_undefined_variables(content, verbose)

    # Fix placeholder variables
    content = fix_placeholder_variables(content, verbose)

    # Fix unclosed parentheses
    content = fix_unclosed_parentheses(content, verbose)

    # Fix indentation errors
    content = fix_indentation_errors(content, verbose)

    # Fix try/except blocks
    content = fix_try_except_blocks(content, verbose)

    # Fix test function indentation
    content = fix_test_function_indentation(content, verbose)

    # Fix test function structure
    content = fix_test_function_structure(content, verbose)

    # Fix line continuation
    content = fix_line_continuation(content, verbose)

    # Fix missing commas
    content = fix_missing_comma(content, verbose)

    # Remove duplicate fixtures
    content = remove_duplicate_fixtures(content, verbose)

    # Fix extra blank lines
    content = fix_extra_blank_lines(content, verbose)

    # Check if the content has changed
    if content == original_content:
        if verbose:
            print("  No changes made")
        return {"status": "no_changes"}

    # Check if the fixed content has syntax errors
    try:
        ast.parse(content)
        if verbose:
            print("  Syntax errors fixed")

        # Write the fixed content to the file
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            if verbose:
                print("  Changes written to file")

        return {"status": "fixed"}
    except SyntaxError as e:
        if verbose:
            print(f"  Failed to fix syntax errors: {e}")
        return {"status": "fixes_failed", "error": str(e)}
    except Exception as e:
        if verbose:
            print(f"  Error: {e}")
        return {"status": "error", "error": str(e)}


def generate_report(
    results: dict[str, dict[str, Any]],
    output_file: str = "interface_syntax_report_v2.json",
) -> None:
    """Generate a report of the results.

    Args:
        results: Dictionary mapping file paths to results
        output_file: Path to the output file
    """
    # Count the number of files in each status
    status_counts = {}
    for result in results.values():
        status = result["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    # Create the report
    report = {
        "summary": {
            "total_files": len(results),
            "files_with_errors": len(results) - status_counts.get("no_errors", 0),
            "files_fixed": status_counts.get("fixed", 0),
            "files_with_unfixed_errors": status_counts.get("fixes_failed", 0),
            "files_with_processing_errors": status_counts.get("error", 0),
            "status_counts": status_counts,
        },
        "results_by_file": results,
    }

    # Write the report to a file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Report written to {output_file}")

    # Print a summary
    print("\nSummary:")
    print(f"  Total files: {report['summary']['total_files']}")
    print(f"  Files with errors: {report['summary']['files_with_errors']}")
    print(f"  Files fixed: {report['summary']['files_fixed']}")
    print(
        f"  Files with unfixed errors: {report['summary']['files_with_unfixed_errors']}"
    )
    print(
        f"  Files with processing errors: {report['summary']['files_with_processing_errors']}"
    )


def main():
    """Main function."""
    args = parse_args()

    # Collect test files
    test_files = collect_test_files(args.module, args.file)
    if not test_files:
        print("No test files found")
        return

    print(f"Found {len(test_files)} test files")

    # Process each file
    results = {}
    for file_path in test_files:
        result = fix_file(file_path, args.dry_run, args.verbose)
        results[file_path] = result

    # Generate a report
    generate_report(results, args.output)


if __name__ == "__main__":
    main()
