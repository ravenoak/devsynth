"""
AST-based code transformation utilities.

This module provides utilities for transforming Python code using AST (Abstract Syntax Tree)
manipulation. It allows for precise code modifications while preserving syntax correctness.
"""

import ast
import astor
import warnings
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


@contextmanager
def suppress_deprecation_warnings():
    """Context manager to suppress deprecation warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        yield


def to_source_with_suppressed_warnings(node):
    """
    Convert an AST node to source code with suppressed deprecation warnings.

    Args:
        node: The AST node to convert

    Returns:
        The source code as a string
    """
    with suppress_deprecation_warnings():
        return astor.to_source(node)


class AstTransformer:
    """
    Transformer for modifying Python code using AST manipulation.

    This class provides methods for common code transformations such as
    renaming identifiers, extracting functions, and refactoring code.
    """

    def __init__(self):
        """Initialize the transformer."""
        pass

    def rename_identifier(self, code: str, old_name: str, new_name: str) -> str:
        """
        Rename an identifier in the code.

        Args:
            code: The source code to modify
            old_name: The name to replace
            new_name: The new name to use

        Returns:
            The modified code with the identifier renamed

        Raises:
            SyntaxError: If the code cannot be parsed
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Create a transformer to rename the identifier
            transformer = IdentifierRenamer(old_name, new_name)

            # Apply the transformation
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)

            # Generate the new code
            new_code = to_source_with_suppressed_warnings(new_tree)

            logger.info(f"Renamed identifier '{old_name}' to '{new_name}'")
            return new_code
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {str(e)}")
            raise

    def extract_function(self, code: str, start_line: int, end_line: int, 
                        function_name: str, parameters: List[str] = None) -> str:
        """
        Extract a block of code into a new function.

        Args:
            code: The source code to modify
            start_line: The starting line of the code block to extract (1-based)
            end_line: The ending line of the code block to extract (1-based)
            function_name: The name for the new function
            parameters: Optional list of parameter names for the function

        Returns:
            The modified code with the extracted function

        Raises:
            SyntaxError: If the code cannot be parsed
            ValueError: If the line range is invalid
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Adjust line numbers to 0-based indexing
            start_line -= 1
            end_line -= 1

            # Split the code into lines
            lines = code.splitlines()

            # Validate line range
            if start_line < 0 or end_line >= len(lines) or start_line > end_line:
                raise ValueError(f"Invalid line range: {start_line+1} to {end_line+1}")

            # Extract the code block
            block_lines = lines[start_line:end_line+1]
            block_code = "\n".join(block_lines)

            # Determine indentation level
            indentation = len(block_lines[0]) - len(block_lines[0].lstrip())

            # Remove common indentation
            dedented_block = []
            for line in block_lines:
                if line.strip():  # Skip empty lines
                    # Remove only the common indentation
                    dedented_block.append(line[indentation:])
                else:
                    dedented_block.append("")

            # Create the function definition
            params = ", ".join(parameters or [])
            function_def = f"def {function_name}({params}):\n"

            # Add the dedented block with proper indentation
            function_body = "\n".join("    " + line for line in dedented_block)

            # Create the full function code
            function_code = function_def + function_body

            # Replace the original block with a function call
            call_params = ", ".join(parameters or [])
            function_call = " " * indentation + f"{function_name}({call_params})"

            # Create the new code
            new_lines = lines[:start_line] + [function_call] + lines[end_line+1:]

            # Add the function definition at the appropriate location
            # For simplicity, we'll add it at the beginning of the file
            # In a real implementation, we might want to be smarter about where to place it
            new_lines.insert(0, "")
            new_lines.insert(0, function_code)

            new_code = "\n".join(new_lines)

            logger.info(f"Extracted function '{function_name}' from lines {start_line+1}-{end_line+1}")
            return new_code
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {str(e)}")
            raise

    def add_docstring(self, code: str, target: str, docstring: str) -> str:
        """
        Add a docstring to a function, class, or module.

        Args:
            code: The source code to modify
            target: The name of the function or class to add the docstring to,
                   or None for the module docstring
            docstring: The docstring to add

        Returns:
            The modified code with the added docstring

        Raises:
            SyntaxError: If the code cannot be parsed
            ValueError: If the target cannot be found
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Create a transformer to add the docstring
            transformer = DocstringAdder(target, docstring)

            # Apply the transformation
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)

            # Generate the new code
            new_code = to_source_with_suppressed_warnings(new_tree)

            logger.info(f"Added docstring to '{target or 'module'}'")
            return new_code
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {str(e)}")
            raise

    def validate_syntax(self, code: str) -> bool:
        """
        Validate that the code has correct syntax.

        Args:
            code: The source code to validate

        Returns:
            True if the code has valid syntax, False otherwise
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


class IdentifierRenamer(ast.NodeTransformer):
    """AST transformer for renaming identifiers."""

    def __init__(self, old_name: str, new_name: str):
        """
        Initialize the transformer.

        Args:
            old_name: The name to replace
            new_name: The new name to use
        """
        self.old_name = old_name
        self.new_name = new_name

    def visit_Name(self, node):
        """Visit a Name node and rename it if it matches the old name."""
        if node.id == self.old_name:
            return ast.Name(id=self.new_name, ctx=node.ctx)
        return node

    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node and rename it if it matches the old name."""
        # Rename the function name if it matches
        if node.name == self.old_name:
            node.name = self.new_name

        # Rename parameters in the function definition
        for arg in node.args.args:
            if arg.arg == self.old_name:
                arg.arg = self.new_name

        # Visit arguments and body
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        """Visit a ClassDef node and rename it if it matches the old name."""
        # Rename the class name if it matches
        if node.name == self.old_name:
            node.name = self.new_name

        # Visit body
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        """Visit an Attribute node and rename it if it matches the old name."""
        # Rename the attribute name if it matches
        if node.attr == self.old_name:
            node.attr = self.new_name

        # Visit value
        self.generic_visit(node)
        return node


class DocstringAdder(ast.NodeTransformer):
    """AST transformer for adding docstrings."""

    def __init__(self, target: Optional[str], docstring: str):
        """
        Initialize the transformer.

        Args:
            target: The name of the function or class to add the docstring to,
                   or None for the module docstring
            docstring: The docstring to add
        """
        self.target = target
        self.docstring = docstring
        self.target_found = False

    def visit_Module(self, node):
        """Visit a Module node and add a docstring if target is None."""
        if self.target is None:
            # Add a module docstring
            docstring_node = ast.Expr(value=ast.Constant(value=self.docstring))

            # If there's already a docstring, replace it
            if node.body and isinstance(node.body[0], ast.Expr) and (
                isinstance(node.body[0].value, ast.Constant) or 
                # Check for ast.Str for Python < 3.14 compatibility
                (hasattr(ast, 'Str') and isinstance(node.body[0].value, getattr(ast, 'Str', type(None))))
            ):
                node.body[0] = docstring_node
            else:
                # Otherwise, insert at the beginning
                node.body.insert(0, docstring_node)

            self.target_found = True

        # Visit the rest of the module
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node and add a docstring if it matches the target."""
        if self.target == node.name:
            # Add a function docstring
            docstring_node = ast.Expr(value=ast.Constant(value=self.docstring))

            # If there's already a docstring, replace it
            if node.body and isinstance(node.body[0], ast.Expr) and (
                isinstance(node.body[0].value, ast.Constant) or 
                # Check for ast.Str for Python < 3.14 compatibility
                (hasattr(ast, 'Str') and isinstance(node.body[0].value, getattr(ast, 'Str', type(None))))
            ):
                node.body[0] = docstring_node
            else:
                # Otherwise, insert at the beginning
                node.body.insert(0, docstring_node)

            self.target_found = True

        # Visit the rest of the function
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        """Visit a ClassDef node and add a docstring if it matches the target."""
        if self.target == node.name:
            # Add a class docstring
            docstring_node = ast.Expr(value=ast.Constant(value=self.docstring))

            # If there's already a docstring, replace it
            if node.body and isinstance(node.body[0], ast.Expr) and (
                isinstance(node.body[0].value, ast.Constant) or 
                # Check for ast.Str for Python < 3.14 compatibility
                (hasattr(ast, 'Str') and isinstance(node.body[0].value, getattr(ast, 'Str', type(None))))
            ):
                node.body[0] = docstring_node
            else:
                # Otherwise, insert at the beginning
                node.body.insert(0, docstring_node)

            self.target_found = True

        # Visit the rest of the class
        self.generic_visit(node)
        return node
