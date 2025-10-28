#!/usr/bin/env python
"""
Script to fix method signature issues in test files.

This script identifies and fixes inconsistent use of 'self' parameter in test class methods.
"""

import ast
import os
import re
import sys
from typing import Dict, List, Set, Tuple


class TestMethodVisitor(ast.NodeVisitor):
    """AST visitor to find test methods with inconsistent self parameter usage."""

    def __init__(self):
        self.test_classes = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self.current_class = node.name
        self.test_classes[node.name] = {
            "methods": [],
            "methods_without_self": [],
            "node": node,
        }
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        if self.current_class and node.name.startswith("test_"):
            self.test_classes[self.current_class]["methods"].append(node.name)

            # Check if the method has 'self' as first argument
            has_self = False
            if node.args.args and node.args.args[0].arg == "self":
                has_self = True
            else:
                self.test_classes[self.current_class]["methods_without_self"].append(
                    node
                )

        self.generic_visit(node)


def find_test_files(base_dir):
    """Find all Python test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def fix_method_signatures(file_path):
    """Fix inconsistent method signatures in a test file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Syntax error in {file_path}, skipping")
        return False

    visitor = TestMethodVisitor()
    visitor.visit(tree)

    # Check if we need to fix anything
    needs_fixing = False
    for class_name, class_info in visitor.test_classes.items():
        if class_info["methods"] and class_info["methods_without_self"]:
            # If a class has both methods with and without self, it needs fixing
            if len(class_info["methods"]) > len(class_info["methods_without_self"]):
                # Most methods use self, so add self to methods without it
                needs_fixing = True
                break

    if not needs_fixing:
        return False

    # Fix the file
    lines = content.split("\n")
    modified_lines = lines.copy()

    for class_name, class_info in visitor.test_classes.items():
        if class_info["methods"] and class_info["methods_without_self"]:
            # If most methods use self, add self to methods without it
            if len(class_info["methods"]) > len(class_info["methods_without_self"]):
                for method_node in class_info["methods_without_self"]:
                    line_num = method_node.lineno - 1  # 0-indexed
                    line = lines[line_num]

                    # Find the method definition pattern
                    method_pattern = rf"def\s+{method_node.name}\s*\("
                    match = re.search(method_pattern, line)

                    if match:
                        # Add 'self' as the first parameter
                        start, end = match.span()
                        new_line = (
                            line[:end]
                            + "self"
                            + (", " if method_node.args.args else "")
                            + line[end:]
                        )
                        modified_lines[line_num] = new_line

    # Write the modified content back to the file if changes were made
    if modified_lines != lines:
        print(f"Fixing method signatures in {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(modified_lines))
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
        if fix_method_signatures(file_path):
            fixed_count += 1

    print(f"Fixed method signatures in {fixed_count} files")


if __name__ == "__main__":
    main()
