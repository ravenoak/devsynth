#!/usr/bin/env python
"""
Script to fix missing pytest imports in test files.

This script scans test files for usage of pytest decorators without corresponding imports
and adds the necessary import statements.
"""

import os
import re
import sys
from pathlib import Path


def find_test_files(base_dir):
    """Find all Python test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def check_and_fix_file(file_path):
    """Check if a file uses pytest without importing it and fix if needed."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Check if the file uses pytest but doesn't import it
    uses_pytest = re.search(r"@pytest\.", content) is not None
    imports_pytest = re.search(r"import\s+pytest", content) is not None

    if uses_pytest and not imports_pytest:
        print(f"Fixing {file_path}")

        # Add import at the beginning of the file after any docstrings and existing imports
        lines = content.split("\n")

        # Find the position to insert the import
        insert_pos = 0
        in_docstring = False
        docstring_delimiter = None

        for i, line in enumerate(lines):
            # Skip docstrings
            if in_docstring:
                if docstring_delimiter in line:
                    in_docstring = False
                    insert_pos = i + 1
                continue

            # Check for docstring start
            if i == 0 and (line.startswith('"""') or line.startswith("'''")):
                in_docstring = True
                docstring_delimiter = line[:3]
                continue

            # If we find an import, update the position
            if line.startswith("import ") or line.startswith("from "):
                insert_pos = i + 1
                continue

            # If we find a non-empty, non-comment line that's not an import, stop
            if line and not line.startswith("#") and not line.isspace():
                break

        # Insert the import
        lines.insert(insert_pos, "import pytest")

        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True

    return False


def main():
    """Main function to run the script."""
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.path.join(os.getcwd(), "tests")

    if not os.path.isdir(base_dir):
        print(f"Error: {base_dir} is not a valid directory")
        sys.exit(1)

    test_files = find_test_files(base_dir)
    fixed_count = 0

    for file_path in test_files:
        if check_and_fix_file(file_path):
            fixed_count += 1

    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
