#!/usr/bin/env python3

"""
Script to verify code examples in markdown documentation.

This script extracts code blocks from markdown files, identifies their language,
and verifies the syntax of the code. It reports any errors found.

Usage:
    python verify_code_examples.py [--verbose] path1 [path2 ...]

Arguments:
    paths: List of markdown files or directories to scan.

Options:
    --verbose, -v: Enable verbose output.
"""

import argparse
import ast
import pathlib
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

# Regex to capture code blocks
# It looks for a block starting with ```<language> and ending with ```
# and captures both the language and the content.
CODE_BLOCK_REGEX = re.compile(r"```(\w+)\s*\n(.*?)```", re.MULTILINE | re.DOTALL)

# Supported languages and their verification commands
LANGUAGE_VERIFIERS = {
    "python": lambda code: verify_python(code),
    "bash": lambda code: verify_bash(code),
    "sh": lambda code: verify_bash(code),
    "javascript": lambda code: verify_javascript(code),
    "js": lambda code: verify_javascript(code),
    "typescript": lambda code: verify_typescript(code),
    "ts": lambda code: verify_typescript(code),
}


def extract_code_blocks(content: str) -> list[tuple[str, str]]:
    """
    Extracts code blocks from markdown content.

    Args:
        content: The markdown content to extract code blocks from.

    Returns:
        A list of tuples containing (language, code).
    """
    matches = CODE_BLOCK_REGEX.findall(content)
    return matches


def verify_python(code: str) -> list[str]:
    """
    Verifies Python code syntax.

    Args:
        code: The Python code to verify.

    Returns:
        A list of error messages, or an empty list if no errors were found.
    """
    errors = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f"Python syntax error: {str(e)}")
    return errors


def verify_bash(code: str) -> list[str]:
    """
    Verifies Bash code syntax.

    Args:
        code: The Bash code to verify.

    Returns:
        A list of error messages, or an empty list if no errors were found.
    """
    errors = []
    try:
        # Use bash -n to check syntax without executing
        result = subprocess.run(
            ["bash", "-n"], input=code.encode(), capture_output=True, check=False
        )
        if result.returncode != 0:
            errors.append(f"Bash syntax error: {result.stderr.decode().strip()}")
    except Exception as e:
        errors.append(f"Error verifying Bash code: {str(e)}")
    return errors


def verify_javascript(code: str) -> list[str]:
    """
    Verifies JavaScript code syntax.

    Args:
        code: The JavaScript code to verify.

    Returns:
        A list of error messages, or an empty list if no errors were found.
    """
    errors = []
    try:
        # Use node -c to check syntax without executing
        result = subprocess.run(
            ["node", "--check"], input=code.encode(), capture_output=True, check=False
        )
        if result.returncode != 0:
            errors.append(f"JavaScript syntax error: {result.stderr.decode().strip()}")
    except Exception as e:
        errors.append(f"Error verifying JavaScript code: {str(e)}")
    return errors


def verify_typescript(code: str) -> list[str]:
    """
    Verifies TypeScript code syntax.

    Args:
        code: The TypeScript code to verify.

    Returns:
        A list of error messages, or an empty list if no errors were found.
    """
    errors = []
    try:
        # This requires the TypeScript compiler (tsc) to be installed
        # Save code to a temporary file
        temp_file = pathlib.Path("temp_ts_code.ts")
        temp_file.write_text(code)

        # Use tsc to check syntax without emitting JavaScript
        result = subprocess.run(
            ["tsc", "--noEmit", str(temp_file)], capture_output=True, check=False
        )

        # Clean up temporary file
        temp_file.unlink()

        if result.returncode != 0:
            errors.append(f"TypeScript syntax error: {result.stderr.decode().strip()}")
    except Exception as e:
        errors.append(f"Error verifying TypeScript code: {str(e)}")
    return errors


def verify_code_block(language: str, code: str) -> list[str]:
    """
    Verifies a code block based on its language.

    Args:
        language: The language of the code block.
        code: The code to verify.

    Returns:
        A list of error messages, or an empty list if no errors were found.
    """
    language = language.lower()
    if language in LANGUAGE_VERIFIERS:
        return LANGUAGE_VERIFIERS[language](code)
    return []  # Skip verification for unsupported languages


def main():
    parser = argparse.ArgumentParser(
        description="Verify code examples in markdown files."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=pathlib.Path,
        help="List of markdown files or directories to scan.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )

    args = parser.parse_args()

    files_to_check: list[pathlib.Path] = []
    for path_arg in args.paths:
        if path_arg.is_file():
            if path_arg.suffix == ".md":
                files_to_check.append(path_arg)
            elif args.verbose:
                print(f"Skipping non-markdown file: {path_arg}")
        elif path_arg.is_dir():
            if args.verbose:
                print(f"Scanning directory: {path_arg}")
            files_to_check.extend(list(path_arg.rglob("*.md")))
        else:
            print(f"Warning: Path '{path_arg}' is not a file or directory. Skipping.")

    if not files_to_check and args.verbose:
        print("No markdown files found to check.")

    total_errors = 0
    files_with_errors = 0
    total_code_blocks = 0

    for md_file in files_to_check:
        if args.verbose:
            print(f"Processing file: {md_file}")
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {md_file}: {e}")
            total_errors += 1
            files_with_errors += 1
            continue

        code_blocks = extract_code_blocks(content)
        total_code_blocks += len(code_blocks)

        file_has_errors = False
        for language, code in code_blocks:
            errors = verify_code_block(language, code)
            if errors:
                if not file_has_errors:
                    print(f"\nErrors in {md_file}:")
                    file_has_errors = True
                    files_with_errors += 1

                print(f"  Code block ({language}):")
                for error in errors:
                    print(f"    - {error}")
                total_errors += len(errors)

    if args.verbose:
        print(
            f"\nProcessed {len(files_to_check)} files with {total_code_blocks} code blocks."
        )

    if total_errors > 0:
        print(f"\nFound {total_errors} errors in {files_with_errors} files.")
        sys.exit(1)
    else:
        print("\nAll code examples verified successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
