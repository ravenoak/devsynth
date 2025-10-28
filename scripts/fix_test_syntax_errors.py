#!/usr/bin/env python
"""
Script to fix common syntax errors in test files.

This script identifies and fixes common syntax errors in test files, such as:
1. Missing or incorrect imports
2. Indentation issues
3. Incorrect function signatures
4. Docstring formatting issues
"""

import ast
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


def find_test_files(base_dir: str) -> list[str]:
    """Find all Python test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def check_file_syntax(file_path: str) -> tuple[bool, str | None]:
    """Check if a file has syntax errors."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def fix_common_syntax_errors(file_path: str) -> bool:
    """Fix common syntax errors in a file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Fix 1: Add missing imports
    if "pytest.mark" in content and "import pytest" not in content:
        import_match = re.search(r"^(import\s+.*?)$", content, re.MULTILINE)
        if import_match:
            # Add after the last import
            last_import = import_match.group(1)
            last_import_pos = content.rfind(last_import) + len(last_import)
            content = (
                content[:last_import_pos]
                + "\nimport pytest"
                + content[last_import_pos:]
            )
        else:
            # Add at the beginning of the file after any docstrings
            docstring_end = (
                content.find('"""', content.find('"""') + 3) + 3
                if '"""' in content
                else 0
            )
            content = (
                content[:docstring_end] + "\nimport pytest\n" + content[docstring_end:]
            )

    # Fix 2: Fix indentation issues in docstrings
    content = re.sub(
        r'"""(.*?)import\s+pytest(.*?)"""', r'"""\1\2"""', content, flags=re.DOTALL
    )

    # Fix 3: Fix incorrect function signatures in BDD step files
    if "/behavior/steps/" in file_path:
        # Make sure step definitions have proper imports
        if "from pytest_bdd import" not in content:
            if "import pytest" in content:
                pytest_import_pos = content.find("import pytest") + len("import pytest")
                content = (
                    content[:pytest_import_pos]
                    + "\nfrom pytest_bdd import given, when, then, parsers, scenarios"
                    + content[pytest_import_pos:]
                )
            else:
                docstring_end = (
                    content.find('"""', content.find('"""') + 3) + 3
                    if '"""' in content
                    else 0
                )
                content = (
                    content[:docstring_end]
                    + "\nimport pytest\nfrom pytest_bdd import given, when, then, parsers, scenarios\n"
                    + content[docstring_end:]
                )

    # Fix 4: Fix missing parentheses in function calls
    content = re.sub(r"(\w+\.\w+)\s+(\w+\()", r"\1(\2", content)

    # Fix 5: Fix missing commas in function arguments
    content = re.sub(r"(\w+\(.*?)\s+(\w+\s*=)", r"\1, \2", content)

    # Check if we made any changes
    if content != original_content:
        try:
            # Verify the fixed content is valid Python
            ast.parse(content)

            # Write the fixed content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Fixed syntax errors in {file_path}")
            return True
        except SyntaxError as e:
            print(f"Failed to fix syntax errors in {file_path}: {e}")
            return False

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
    error_count = 0

    for file_path in test_files:
        syntax_valid, error = check_file_syntax(file_path)
        if not syntax_valid:
            print(f"Syntax error in {file_path}: {error}")
            if fix_common_syntax_errors(file_path):
                fixed_count += 1
            else:
                error_count += 1

    print(f"Fixed {fixed_count} files with syntax errors")
    print(f"Failed to fix {error_count} files with syntax errors")


if __name__ == "__main__":
    main()
