#!/usr/bin/env python3
"""
Script to fix type annotation issues by replacing the pipe operator (|) with Union from typing.
This script addresses a critical issue identified in the DevSynth codebase.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def ensure_union_import(content):
    """Ensure that Union is imported from typing if it's not already."""
    # Check if Union is already imported
    if (
        re.search(r"from\s+typing\s+import\s+[^(]*\bUnion\b", content)
        or re.search(r"from\s+typing\s+import\s+\([^)]*\bUnion\b[^)]*\)", content)
        or re.search(r"import\s+typing", content)
    ):
        return content

    # Add Union to existing typing import
    if re.search(r"from\s+typing\s+import", content):
        # If there's a multi-line import with parentheses
        if re.search(r"from\s+typing\s+import\s+\(", content):
            return re.sub(
                r"(from\s+typing\s+import\s+\()([^)]*?)(\))", r"\1\2, Union\3", content
            )
        # If there's a single-line import
        else:
            return re.sub(
                r"(from\s+typing\s+import\s+[^(][^\n]*)", r"\1, Union", content
            )

    # If there's no typing import, add it
    # Find the last import statement
    import_matches = list(
        re.finditer(r"^import\s+.*$|^from\s+.*\s+import", content, re.MULTILINE)
    )
    if import_matches:
        last_import = import_matches[-1]
        last_import_end = last_import.end()
        return (
            content[:last_import_end]
            + "\nfrom typing import Union"
            + content[last_import_end:]
        )

    # If there are no imports, add it at the beginning after any module docstring
    docstring_match = re.search(r'^""".*?"""', content, re.DOTALL)
    if docstring_match:
        docstring_end = docstring_match.end()
        return (
            content[:docstring_end]
            + "\n\nfrom typing import Union"
            + content[docstring_end:]
        )

    # Otherwise, add it at the very beginning
    return "from typing import Union\n\n" + content


def fix_type_annotations(content):
    """Replace pipe operator (|) with Union in type annotations."""
    # Pattern to match type annotations with pipe operator
    # This pattern looks for type annotations like "x: Type1 | Type2"
    pattern = r'(\w+\s*:\s*)([A-Za-z0-9_"\'\.]+)\s*\|\s*([A-Za-z0-9_"\'\.]+)'

    # Replace with Union
    fixed_content = re.sub(pattern, r"\1Union[\2, \3]", content)

    # Handle the case where we already have Union but still using pipe operator
    # e.g., Union[Type1] | None -> Union[Type1, None]
    union_pattern = r'(\w+\s*:\s*)Union\[([^\]]+)\]\s*\|\s*([A-Za-z0-9_"\'\.]+)'
    fixed_content = re.sub(union_pattern, r"\1Union[\2, \3]", fixed_content)

    return fixed_content


def process_file(file_path, dry_run=False):
    """Process a single Python file to fix type annotations."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Skip files that don't have pipe operator in type annotations
    if "|" not in content or not re.search(
        r'\w+\s*:\s*[A-Za-z0-9_"\'\.]+\s*\|', content
    ):
        return False

    # Fix type annotations
    fixed_content = fix_type_annotations(content)

    # Ensure Union is imported
    if fixed_content != content:
        fixed_content = ensure_union_import(fixed_content)

    if fixed_content != content:
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
        return True

    return False


def find_python_files(directory):
    """Find all Python files in the given directory recursively."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


def main():
    parser = argparse.ArgumentParser(
        description="Fix type annotation issues in Python files"
    )
    parser.add_argument(
        "--directory", "-d", default=".", help="Directory to search for Python files"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Dry run (no changes will be made)"
    )
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.exists() or not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return 1

    print(f"Searching for Python files in {directory}")

    fixed_files = 0
    for file_path in find_python_files(directory):
        if process_file(file_path, args.dry_run):
            fixed_files += 1
            print(f"Fixed: {file_path}")

    print(f"\nFixed {fixed_files} files")
    if args.dry_run:
        print("(Dry run - no changes were made)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
