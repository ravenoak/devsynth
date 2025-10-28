#!/usr/bin/env python3
"""
Enhanced script to convert docstrings to NumPy format.

This script uses the AST module to parse Python files and modify docstrings
without affecting function signatures or introducing syntax errors.
"""

import ast
import os
import re
import sys

try:
    import astor
except ImportError:  # pragma: no cover - simple import guard
    astor = None
from typing import Any, Dict, List, Optional, Tuple


class DocstringConverter(ast.NodeVisitor):
    """AST visitor that converts docstrings to NumPy format."""

    def __init__(self):
        self.changes_made = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definitions and convert their docstrings."""
        # Process docstring if it exists
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        ):
            docstring = node.body[0].value.s
            converted_docstring = self.convert_to_numpy_format(docstring)

            # Only update if the docstring changed
            if converted_docstring != docstring:
                node.body[0].value.s = converted_docstring
                self.changes_made = True

        # Continue visiting child nodes
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definitions and convert their docstrings."""
        # Process class docstring if it exists
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        ):
            docstring = node.body[0].value.s
            converted_docstring = self.convert_to_numpy_format(docstring)

            # Only update if the docstring changed
            if converted_docstring != docstring:
                node.body[0].value.s = converted_docstring
                self.changes_made = True

        # Continue visiting child nodes
        self.generic_visit(node)
        return node

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visit module and convert its docstring."""
        # Process module docstring if it exists
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Str)
        ):
            docstring = node.body[0].value.s
            converted_docstring = self.convert_to_numpy_format(docstring)

            # Only update if the docstring changed
            if converted_docstring != docstring:
                node.body[0].value.s = converted_docstring
                self.changes_made = True

        # Continue visiting child nodes
        self.generic_visit(node)
        return node

    def convert_to_numpy_format(self, docstring: str) -> str:
        """
        Convert a docstring from Google style to NumPy style.

        Parameters
        ----------
        docstring : str
            The docstring to convert

        Returns
        -------
        str
            The converted docstring
        """
        # Remove 'r' prefix if present (raw string)
        if docstring.startswith('r"""') or docstring.startswith("r'''"):
            docstring = docstring[1:]

        # Replace "Args:" with "Parameters\n----------"
        docstring = re.sub(
            r"(\s+)Args:\s*\n", r"\1Parameters\n\1----------\n", docstring
        )

        # Replace "Returns:" with "Returns\n-------"
        docstring = re.sub(r"(\s+)Returns:\s*\n", r"\1Returns\n\1-------\n", docstring)

        # Replace "Raises:" with "Raises\n------"
        docstring = re.sub(r"(\s+)Raises:\s*\n", r"\1Raises\n\1------\n", docstring)

        # Format parameters: "param_name: description" to "param_name : type\n        description"
        def param_replacer(match):
            indent, name, colon, desc = match.groups()
            # Clean up description and remove extra whitespace
            desc = desc.strip()
            # Handle multi-line descriptions
            desc_lines = desc.split("\n")
            formatted_desc = desc_lines[0]
            if len(desc_lines) > 1:
                # Preserve indentation for multi-line descriptions
                additional_lines = "\n".join(
                    [f"{indent}    {line.strip()}" for line in desc_lines[1:]]
                )
                formatted_desc = f"{formatted_desc}\n{additional_lines}"

            return f"{indent}{name} : object\n{indent}    {formatted_desc}"

        # Improved regex pattern for parameters
        param_pattern = re.compile(
            r"(\s+)([a-zA-Z_][a-zA-Z0-9_]*)(: )(.+?)(?=\n\s+[a-zA-Z_][a-zA-Z0-9_]*:|"
            r"\n\s*\n|\n\s+Returns\n|\n\s+Raises\n|$)",
            re.DOTALL,
        )

        docstring = param_pattern.sub(param_replacer, docstring)

        # Remove duplicate blank lines
        docstring = re.sub(r"\n\s*\n\s*\n", r"\n\n", docstring)

        return docstring


def convert_file(
    file_path: str, output_path: str | None = None, backup: bool = True
) -> bool:
    """
    Convert docstrings in a Python file to NumPy format.

    Parameters
    ----------
    file_path : str
        Path to the Python file to convert
    output_path : Optional[str]
        Path to write the converted file (if None, overwrites the original)
    backup : bool
        Whether to create a backup of the original file

    Returns
    -------
    bool
        True if changes were made, False otherwise
    """
    try:
        # Read the file
        with open(file_path, encoding="utf-8") as f:
            source_code = f.read()

        # Parse the source code into an AST
        tree = ast.parse(source_code)

        # Convert docstrings
        converter = DocstringConverter()
        converter.visit(tree)

        # If no changes were made, return early
        if not converter.changes_made:
            print(f"No changes needed in {file_path}")
            return False

        # Generate the modified source code
        if astor is None:
            raise ImportError(
                "The 'astor' package is required. Install it with 'poetry add astor'."
            )
        modified_code = astor.to_source(tree)

        # Create a backup if requested
        if backup and output_path is None:
            backup_path = f"{file_path}.bak"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            print(f"Created backup at {backup_path}")

        # Write the modified code
        target_path = output_path or file_path
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(modified_code)

        print(f"Converted docstrings in {file_path} -> {target_path}")
        return True

    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_python_files(directory: str) -> list[str]:
    """
    Find all Python files in a directory and its subdirectories.

    Parameters
    ----------
    directory : str
        Directory to search for Python files

    Returns
    -------
    List[str]
        List of paths to Python files
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Main function to run the script."""
    # Check if astor is installed
    if astor is None:
        raise ImportError(
            "The 'astor' package is required. Install it with 'poetry add astor'."
        )

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Convert docstrings to NumPy format")
    parser.add_argument("path", help="Path to a Python file or directory")
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory (for directory input) or file (for file input)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backups of original files",
    )
    args = parser.parse_args()

    # Process the input path
    if os.path.isfile(args.path):
        # Convert a single file
        output_path = args.output
        convert_file(args.path, output_path, not args.no_backup)
    elif os.path.isdir(args.path):
        # Convert all Python files in the directory
        python_files = find_python_files(args.path)
        print(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            # Determine output path if specified
            output_path = None
            if args.output:
                rel_path = os.path.relpath(file_path, args.path)
                output_path = os.path.join(args.output, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

            convert_file(file_path, output_path, not args.no_backup)
    else:
        print(f"Path not found: {args.path}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
