#!/usr/bin/env python3
"""
Fix Interface Module Syntax Errors

This script addresses syntax errors in the interface module test files by applying
targeted fixes for common error patterns:

1. Indentation errors (unexpected indent/unindent)
2. Placeholder variables that weren't replaced
3. Improperly structured test functions
4. Line continuation issues
5. Unclosed parentheses
6. Extra blank lines

Usage:
    python scripts/fix_interface_syntax.py [options]

Options:
    --module MODULE       Specific module to process (default: tests/unit/interface)
    --file FILE           Specific file to process
    --max-files N         Maximum number of files to process in a single run (default: 100)
    --dry-run             Show changes without modifying files
    --verbose             Show detailed information
    --report              Generate a report of syntax errors without fixing
    --apply               Apply fixes without confirmation
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
        "--module",
        default="tests/unit/interface",
        help="Specific module to process (default: tests/unit/interface)",
    )
    parser.add_argument("--file", help="Specific file to process")
    parser.add_argument(
        "--max-files",
        type=int,
        default=100,
        help="Maximum number of files to process in a single run (default: 100)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a report of syntax errors without fixing",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply fixes without confirmation"
    )
    return parser.parse_args()


def collect_test_files(module: str, file: str = None) -> list[str]:
    """
    Collect test files to process.

    Args:
        module: Module to collect tests from
        file: Specific file to process

    Returns:
        List of test file paths
    """
    print(f"Collecting test files from {module}...")

    if file:
        # Process a specific file
        file_path = os.path.join(module, file) if not os.path.isabs(file) else file
        if os.path.exists(file_path) and file_path.endswith(".py"):
            return [file_path]
        else:
            print(f"Error: File {file_path} does not exist or is not a Python file.")
            return []

    # Collect all test files in the module
    test_files = []
    for root, _, files in os.walk(module):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = os.path.join(root, file)
                test_files.append(file_path)

    print(f"Found {len(test_files)} test files")
    return test_files


def check_syntax(file_path: str) -> tuple[bool, str]:
    """
    Check if a file has syntax errors.

    Args:
        file_path: Path to the file to check

    Returns:
        Tuple of (has_error, error_message)
    """
    try:
        with open(file_path) as f:
            content = f.read()

        # Try to parse the file
        ast.parse(content, filename=file_path)
        return False, ""
    except SyntaxError as e:
        return True, f"SyntaxError: {e.msg} (line {e.lineno}, column {e.offset})"
    except IndentationError as e:
        return True, f"IndentationError: {e.msg} (line {e.lineno}, column {e.offset})"
    except Exception as e:
        return True, f"Error: {str(e)}"


def fix_indentation_errors(content: str, verbose: bool = False) -> str:
    """
    Fix indentation errors in the content.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing indentation errors...")

    # First, let's try a more comprehensive approach by completely restructuring the file
    try:
        # Parse the file to identify classes and functions
        tree = ast.parse(content)

        # If we can parse the file, we can use a more targeted approach
        return fix_indentation_with_ast(content, tree, verbose)
    except SyntaxError:
        # If we can't parse the file due to syntax errors, use a line-by-line approach
        if verbose:
            print("    Using line-by-line approach due to syntax errors")
        return fix_indentation_line_by_line(content, verbose)


def fix_indentation_with_ast(content: str, tree: ast.AST, verbose: bool = False) -> str:
    """
    Fix indentation using AST parsing.

    Args:
        content: File content to fix
        tree: AST tree of the content
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    # This is a placeholder for future implementation
    # Currently, we'll fall back to the line-by-line approach
    return fix_indentation_line_by_line(content, verbose)


def fix_indentation_line_by_line(content: str, verbose: bool = False) -> str:
    """
    Fix indentation errors line by line.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = []

    # Track indentation levels and context
    class_level = 0
    method_level = 0
    in_class = False
    in_method = False
    in_docstring = False
    docstring_indent = 0
    fixture_level = 0
    in_fixture = False
    current_indent = 0

    # First pass: identify classes and their indentation
    classes = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"class\s+\w+", stripped):
            indent = len(line) - len(line.lstrip())
            classes.append((i, indent))

    # Second pass: fix indentation
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            i += 1
            continue

        # Check for class definition
        if re.match(r"class\s+\w+", stripped):
            in_class = True
            in_method = False
            in_fixture = False
            class_level = len(line) - len(line.lstrip())
            current_indent = class_level
            fixed_lines.append(line)
            i += 1
            continue

        # Check for decorator (could be for a method or fixture)
        if stripped.startswith("@"):
            # If we're in a class, this should be indented at class_level + 4
            if in_class and not line.startswith(" " * (class_level + 4)):
                if verbose:
                    print(f"    Line {i+1}: Fixing decorator indentation")
                fixed_lines.append(" " * (class_level + 4) + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for fixture definition
        if re.match(r"def\s+\w+_state", stripped) or (
            i > 0 and lines[i - 1].strip().startswith("@pytest.fixture")
        ):
            if in_class:
                # This is a fixture within a class
                fixture_level = class_level + 4
                if not line.startswith(" " * fixture_level):
                    if verbose:
                        print(f"    Line {i+1}: Fixing fixture indentation in class")
                    fixed_lines.append(" " * fixture_level + stripped)
                else:
                    fixed_lines.append(line)
            else:
                # This is a fixture at module level
                fixture_level = 0
                fixed_lines.append(line)

            in_fixture = True
            in_method = False
            current_indent = fixture_level
            i += 1
            continue

        # Check for method definition
        if re.match(r"def\s+\w+", stripped):
            if in_class:
                # This is a method within a class
                method_level = class_level + 4
                if not line.startswith(" " * method_level):
                    if verbose:
                        print(f"    Line {i+1}: Fixing method indentation in class")
                    fixed_lines.append(" " * method_level + stripped)
                else:
                    fixed_lines.append(line)
            else:
                # This is a function at module level
                method_level = 0
                fixed_lines.append(line)

            in_method = True
            in_fixture = False
            current_indent = method_level
            i += 1
            continue

        # Check for try/except/finally blocks
        if stripped in ["try:", "except:", "except", "finally:"]:
            # These should be indented at the current body level
            body_indent = current_indent + 4
            if not line.startswith(" " * body_indent):
                if verbose:
                    print(f"    Line {i+1}: Fixing {stripped} indentation")
                fixed_lines.append(" " * body_indent + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for except with condition
        if stripped.startswith("except "):
            # These should be indented at the current body level
            body_indent = current_indent + 4
            if not line.startswith(" " * body_indent):
                if verbose:
                    print(f"    Line {i+1}: Fixing except condition indentation")
                fixed_lines.append(" " * body_indent + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for docstring
        if (
            stripped.startswith('"""')
            and stripped.endswith('"""')
            and len(stripped) > 3
        ):
            # Single line docstring
            if in_method or in_fixture:
                # This is a docstring within a method or fixture
                docstring_indent = current_indent + 4
                if not line.startswith(" " * docstring_indent):
                    if verbose:
                        print(
                            f"    Line {i+1}: Fixing single-line docstring indentation"
                        )
                    fixed_lines.append(" " * docstring_indent + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for multi-line docstring start
        if (
            stripped.startswith('"""')
            and not stripped.endswith('"""')
            or (stripped.endswith('"""') and not stripped.startswith('"""'))
        ):
            in_docstring = not in_docstring
            if in_method or in_fixture:
                # This is a docstring within a method or fixture
                docstring_indent = current_indent + 4
                if not line.startswith(" " * docstring_indent):
                    if verbose:
                        print(
                            f"    Line {i+1}: Fixing multi-line docstring indentation"
                        )
                    fixed_lines.append(" " * docstring_indent + stripped)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for docstring continuation
        if in_docstring:
            if (in_method or in_fixture) and not line.startswith(
                " " * docstring_indent
            ):
                if verbose:
                    print(f"    Line {i+1}: Fixing docstring continuation indentation")
                fixed_lines.append(" " * docstring_indent + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for method or fixture body
        if in_method or in_fixture:
            body_indent = current_indent + 4
            if not line.startswith(" " * body_indent) and not stripped.startswith("@"):
                if verbose:
                    print(
                        f"    Line {i+1}: Fixing {'method' if in_method else 'fixture'} body indentation"
                    )
                fixed_lines.append(" " * body_indent + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Default: keep the line as is
        fixed_lines.append(line)
        i += 1

    # Third pass: fix test_function structure
    content = "\n".join(fixed_lines)
    content = fix_test_function_indentation(content, verbose)

    # Fourth pass: fix try/except/finally blocks
    content = fix_try_except_blocks(content, verbose)

    # Fifth pass: remove duplicate fixtures
    content = remove_duplicate_fixtures(content, verbose)

    return content


def fix_try_except_blocks(content: str, verbose: bool = False) -> str:
    """
    Fix indentation and structure of try/except/finally blocks.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing try/except/finally blocks...")

    lines = content.split("\n")
    fixed_lines = []

    # Track block levels
    in_try_block = False
    try_level = 0
    block_level = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            i += 1
            continue

        # Check for try statement
        if stripped == "try:":
            in_try_block = True
            try_level = len(line) - len(line.lstrip())
            block_level = try_level + 4
            fixed_lines.append(line)
            i += 1
            continue

        # Check for except/finally statements
        if in_try_block and (
            stripped == "except:"
            or stripped.startswith("except ")
            or stripped == "finally:"
        ):
            # These should be at the same level as the try statement
            if not line.startswith(" " * try_level):
                if verbose:
                    print(
                        f"    Line {i+1}: Fixing {stripped} indentation to match try level"
                    )
                fixed_lines.append(" " * try_level + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Check for block body
        if in_try_block and not (
            stripped == "try:"
            or stripped == "except:"
            or stripped.startswith("except ")
            or stripped == "finally:"
        ):
            # These should be indented one level from the try/except/finally statement
            if not line.startswith(" " * block_level):
                if verbose:
                    print(
                        f"    Line {i+1}: Fixing try/except/finally block body indentation"
                    )
                fixed_lines.append(" " * block_level + stripped)
            else:
                fixed_lines.append(line)
            i += 1
            continue

        # Default: keep the line as is
        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def remove_duplicate_fixtures(content: str, verbose: bool = False) -> str:
    """
    Remove duplicate fixture definitions.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Removing duplicate fixtures...")

    # Find all fixture definitions
    fixture_pattern = r"@pytest\.fixture\s*\n\s*def\s+(\w+)\s*\([^)]*\):\s*\n(?:\s*#[^\n]*\n)*(?:\s*[^\n@]*\n)*\s*yield\s*\n(?:\s*#[^\n]*\n)*(?:\s*[^\n@]*\n)*"
    fixtures = {}

    for match in re.finditer(fixture_pattern, content):
        fixture_name = match.group(1)
        fixture_code = match.group(0)

        if fixture_name in fixtures:
            fixtures[fixture_name].append((match.start(), match.end(), fixture_code))
        else:
            fixtures[fixture_name] = [(match.start(), match.end(), fixture_code)]

    # Remove duplicate fixtures
    for fixture_name, occurrences in fixtures.items():
        if len(occurrences) > 1:
            if verbose:
                print(
                    f"    Found {len(occurrences)} occurrences of fixture '{fixture_name}'"
                )

            # Keep only the first occurrence
            to_remove = occurrences[1:]

            # Sort by start position in descending order to avoid index issues when removing
            to_remove.sort(key=lambda x: x[0], reverse=True)

            for start, end, _ in to_remove:
                if verbose:
                    print(
                        f"    Removing duplicate fixture '{fixture_name}' at position {start}"
                    )
                content = content[:start] + content[end:]

    return content


def fix_test_function_indentation(content: str, verbose: bool = False) -> str:
    """
    Fix indentation for test_function structures.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    # Find test_function definitions that are not properly indented
    pattern = r'def\s+test_function\s*\([^)]*\):\s*\n\s*#\s*Test\s+with\s+clean\s+state\s*\n\s*"""([^"]*)"""'

    matches = list(re.finditer(pattern, content))
    if not matches:
        return content

    lines = content.split("\n")
    fixed_lines = []

    # Track which lines to skip (they'll be replaced)
    skip_lines = set()

    for match in matches:
        docstring = match.group(1).strip()
        start_line = content[: match.start()].count("\n")
        end_line = content[: match.end()].count("\n")

        # Mark lines to skip
        for i in range(start_line, end_line + 1):
            skip_lines.add(i)

        # Find the indentation level
        indent = 0
        for i in range(start_line, -1, -1):
            if i < len(lines) and re.match(r"class\s+\w+", lines[i].strip()):
                # This test_function is inside a class
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                break

        # Create a properly structured and indented test function
        replacement = (
            f"{' ' * indent}def test_with_clean_state(clean_state):\n{' ' * (indent + 4)}\"\"\""
            + docstring
            + f'"""\n'
        )

        if verbose:
            print(
                f"    Replacing generic test_function with properly indented test_with_clean_state"
            )

        # Find where to insert the replacement
        for i in range(len(lines)):
            if i not in skip_lines:
                fixed_lines.append(lines[i])
            elif i == start_line:
                fixed_lines.append(replacement)

    return "\n".join(fixed_lines)


def fix_placeholder_variables(content: str, verbose: bool = False) -> str:
    """
    Fix placeholder variables in the content.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing placeholder variables...")

    # Replace $1, $2, etc. with appropriate values
    placeholders = {
        r"\$1": "module_name",
        r"\$2": "module",
        r"ClassName": "object",  # Replace ClassName with a generic object
        r"module_name": "module",  # Replace module_name with module
        r"target_module": "module",  # Replace target_module with module
        r"mock_function": "mock_func",  # Replace mock_function with mock_func
        r"target": "module",  # Replace target with module
    }

    fixed_content = content
    for placeholder, replacement in placeholders.items():
        if re.search(placeholder, fixed_content):
            if verbose:
                print(f"    Replacing {placeholder} with {replacement}")
            fixed_content = re.sub(placeholder, replacement, fixed_content)

    return fixed_content


def fix_test_function_structure(content: str, verbose: bool = False) -> str:
    """
    Fix improperly structured test functions.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing test function structure...")

    # Find test_function definitions that are not properly structured
    pattern = r'def\s+test_function\s*\([^)]*\):\s*\n\s*#\s*Test\s+with\s+clean\s+state\s*\n\s*"""([^"]*)"""'

    matches = list(re.finditer(pattern, content))
    if not matches:
        return content

    fixed_content = content
    for match in matches:
        docstring = match.group(1).strip()

        # Create a properly structured test function
        replacement = (
            f'def test_with_clean_state(clean_state):\n    """{docstring}"""\n'
        )

        if verbose:
            print(f"    Replacing generic test_function with test_with_clean_state")

        fixed_content = fixed_content.replace(match.group(0), replacement)

    return fixed_content


def fix_line_continuation(content: str, verbose: bool = False) -> str:
    """
    Fix line continuation issues.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing line continuation issues...")

    # Fix line breaks within list indexing operations
    pattern = r"(\w+)\.(\w+)\.call_args\[\s*\n\s*(\d+)\s*\]\[\s*\n\s*(\d+)\s*\]"

    matches = list(re.finditer(pattern, content))
    if not matches:
        return content

    fixed_content = content
    for match in matches:
        obj = match.group(1)
        attr = match.group(2)
        idx1 = match.group(3)
        idx2 = match.group(4)

        # Create a properly formatted indexing operation
        replacement = f"{obj}.{attr}.call_args[{idx1}][{idx2}]"

        if verbose:
            print(f"    Fixing line continuation in indexing operation")

        fixed_content = fixed_content.replace(match.group(0), replacement)

    return fixed_content


def fix_unclosed_parentheses(content: str, verbose: bool = False) -> str:
    """
    Fix unclosed parentheses.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing unclosed parentheses...")

    # Count opening and closing parentheses
    open_count = content.count("(")
    close_count = content.count(")")

    if open_count == close_count:
        return content

    # Try to find unclosed parentheses using tokenize
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(content.encode("utf-8")).readline))

        # Track parentheses
        stack = []
        for token in tokens:
            if token.string == "(":
                stack.append(token)
            elif token.string == ")":
                if stack:
                    stack.pop()

        # If there are unclosed parentheses, add closing parentheses at the end of the line
        if stack:
            lines = content.split("\n")
            for token in stack:
                line_idx = token.start[0] - 1
                if line_idx < len(lines):
                    if verbose:
                        print(f"    Adding closing parenthesis to line {line_idx + 1}")
                    lines[line_idx] = lines[line_idx] + ")"

            return "\n".join(lines)

    except Exception as e:
        if verbose:
            print(f"    Error analyzing tokens: {e}")

    # Fallback: add missing closing parentheses at the end of the file
    if open_count > close_count:
        missing = open_count - close_count
        if verbose:
            print(f"    Adding {missing} closing parentheses at the end of the file")
        return content + ")" * missing

    return content


def fix_extra_blank_lines(content: str, verbose: bool = False) -> str:
    """
    Fix extra blank lines.

    Args:
        content: File content to fix
        verbose: Whether to show detailed information

    Returns:
        Fixed content
    """
    if verbose:
        print("  Fixing extra blank lines...")

    # Replace multiple blank lines with a single blank line
    fixed_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)

    return fixed_content


def fix_file(
    file_path: str, dry_run: bool = True, verbose: bool = False
) -> tuple[bool, dict[str, Any]]:
    """
    Fix syntax errors in a file.

    Args:
        file_path: Path to the file to fix
        dry_run: Whether to show changes without modifying the file
        verbose: Whether to show detailed information

    Returns:
        Tuple of (success, results)
    """
    if verbose:
        print(f"Processing {file_path}...")

    try:
        # Check if the file has syntax errors
        has_error, error_message = check_syntax(file_path)

        if not has_error:
            if verbose:
                print("  No syntax errors found.")
            return True, {"status": "no_errors"}

        if verbose:
            print(f"  Found syntax error: {error_message}")

        # Read the file
        with open(file_path) as f:
            content = f.read()

        # Apply fixes in multiple passes
        original_content = content

        # Pass 1: Fix indentation errors
        content = fix_indentation_errors(content, verbose)

        # Pass 2: Fix placeholder variables
        content = fix_placeholder_variables(content, verbose)

        # Pass 3: Fix test function structure
        content = fix_test_function_structure(content, verbose)

        # Pass 4: Fix line continuation issues
        content = fix_line_continuation(content, verbose)

        # Pass 5: Fix unclosed parentheses
        content = fix_unclosed_parentheses(content, verbose)

        # Pass 6: Fix extra blank lines
        content = fix_extra_blank_lines(content, verbose)

        # Check if the content was modified
        modified = content != original_content

        # Check if the fixes resolved the syntax errors
        if modified:
            # Write the fixed content to a temporary file for syntax checking
            temp_file = file_path + ".temp"
            with open(temp_file, "w") as f:
                f.write(content)

            # Check if the fixed content has syntax errors
            has_error, error_message = check_syntax(temp_file)

            # Remove the temporary file
            os.remove(temp_file)

            if has_error:
                if verbose:
                    print(f"  Fixes did not resolve all syntax errors: {error_message}")
                return False, {"status": "fixes_failed", "error": error_message}

            # Write the fixed content to the file
            if not dry_run:
                with open(file_path, "w") as f:
                    f.write(content)
                print(f"  Fixed {file_path}")
            else:
                print(f"  Would fix {file_path} (dry run)")

            return True, {"status": "fixed"}
        else:
            if verbose:
                print("  No changes made.")
            return False, {"status": "no_changes", "error": error_message}

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, {"status": "error", "error": str(e)}


def generate_report(
    results: dict[str, dict[str, Any]],
    output_file: str = "interface_syntax_report.json",
):
    """
    Generate a report of syntax errors.

    Args:
        results: Dictionary of results by file
        output_file: Path to the output file
    """
    # Count issues by status
    status_counts = {
        "no_errors": 0,
        "fixed": 0,
        "fixes_failed": 0,
        "no_changes": 0,
        "error": 0,
    }

    for file_path, result in results.items():
        status = result.get("status", "error")
        status_counts[status] += 1

    # Create the report
    report = {
        "summary": {
            "total_files": len(results),
            "files_with_errors": len(results) - status_counts["no_errors"],
            "files_fixed": status_counts["fixed"],
            "files_with_unfixed_errors": status_counts["fixes_failed"]
            + status_counts["no_changes"],
            "files_with_processing_errors": status_counts["error"],
            "status_counts": status_counts,
        },
        "results_by_file": results,
    }

    # Write the report to a file
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report generated: {output_file}")
    print(f"Summary:")
    print(f"  Total files analyzed: {report['summary']['total_files']}")
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

    # Limit the number of files to process
    if args.max_files > 0 and len(test_files) > args.max_files:
        print(f"Limiting to {args.max_files} files (out of {len(test_files)} files)")
        test_files = test_files[: args.max_files]

    # Process each file
    results = {}
    fixed_files = []
    unfixed_files = []

    for file_path in test_files:
        # Fix the file
        success, result = fix_file(file_path, args.dry_run or args.report, args.verbose)

        # Store the results
        results[file_path] = result

        if success and result["status"] == "fixed":
            fixed_files.append(file_path)
        elif result["status"] in ["fixes_failed", "no_changes"]:
            unfixed_files.append(file_path)

    # Generate a report if requested
    if args.report:
        generate_report(results)

    # Print summary
    print("\nSummary:")
    print(f"  Total files processed: {len(test_files)}")
    print(f"  Files fixed: {len(fixed_files)}")
    print(f"  Files with unfixed errors: {len(unfixed_files)}")

    if args.dry_run and not args.report:
        print("\nNote: This was a dry run. Use without --dry-run to apply changes.")

    print("\nDone!")


if __name__ == "__main__":
    main()
