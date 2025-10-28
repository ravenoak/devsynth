"""
AST-based code transformation module.

This module provides components for transforming Python code using AST (Abstract Syntax Tree)
manipulations, enabling automated refactoring, optimization, and other code transformations.
"""

import ast
import os
import re
from typing import (
    Any,
    Dict,
    List,
    NotRequired,
    Optional,
    Set,
    Type,
    TypedDict,
    Union,
    cast,
)
from collections.abc import Callable

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.domain.interfaces.code_analysis import (
    CodeTransformationProvider,
    FileAnalysisResult,
    TransformationResult,
)
from devsynth.domain.models.code_analysis import CodeTransformation
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

# ---------------------------------------------------------------------------
# ``ast.unparse`` became available in Python 3.9.  When running on 3.9+ we
# prefer it over ``astor`` so that environments without the extra dependency do
# not fail.  ``astor`` is imported lazily only when required.
# ---------------------------------------------------------------------------
if hasattr(ast, "unparse"):

    def _to_source(tree: ast.AST) -> str:
        """Convert an AST back to source code using ``ast.unparse``."""

        return ast.unparse(tree)

else:  # pragma: no cover - exercised on older Python versions
    import astor  # type: ignore[import]

    def _to_source(tree: ast.AST) -> str:
        """Fallback to ``astor`` when ``ast.unparse`` is unavailable."""

        return astor.to_source(tree)


class ChangeRecord(TypedDict, total=False):
    """Structured description of a transformation change."""

    description: str
    line: NotRequired[int]
    col: NotRequired[int]


class AstTransformer(ast.NodeTransformer):
    """Base AST transformer for modifying Python code."""

    def __init__(self):
        """Initialize the transformer."""
        super().__init__()
        self.changes: list[ChangeRecord] = []

    def record_change(self, node: ast.AST, description: str) -> None:
        """Record a change made to the AST."""
        if hasattr(node, "lineno"):
            self.changes.append(
                {
                    "line": node.lineno,
                    "col": getattr(node, "col_offset", 0),
                    "description": description,
                }
            )
        else:
            self.changes.append({"description": description})


class UnusedImportRemover(AstTransformer):
    """Transformer that removes unused imports."""

    def __init__(self, symbol_usage: dict[str, int]):
        """
        Initialize the transformer.

        Args:
            symbol_usage: Dictionary mapping symbol names to their usage count
        """
        super().__init__()
        self.symbol_usage: dict[str, int] = symbol_usage

    def visit_Import(self, node: ast.Import) -> ast.AST | None:
        """Visit an Import node and remove unused imports."""
        new_names: list[ast.alias] = []
        for name in node.names:
            if name.name in self.symbol_usage and self.symbol_usage[name.name] > 0:
                new_names.append(name)
            else:
                self.record_change(node, f"Removed unused import: {name.name}")

        if not new_names:
            # All imports in this statement are unused, remove the entire statement
            return None

        # Some imports are used, keep them
        node.names = new_names
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | None:
        """Visit an ImportFrom node and remove unused imports."""
        new_names: list[ast.alias] = []
        for name in node.names:
            # Check if the imported name is used
            import_name = f"{node.module}.{name.name}" if node.module else name.name
            if (
                name.name in self.symbol_usage and self.symbol_usage[name.name] > 0
            ) or (
                import_name in self.symbol_usage and self.symbol_usage[import_name] > 0
            ):
                new_names.append(name)
            else:
                self.record_change(node, f"Removed unused import: {import_name}")

        if not new_names:
            # All imports in this statement are unused, remove the entire statement
            return None

        # Some imports are used, keep them
        node.names = new_names
        return node


class RedundantAssignmentRemover(AstTransformer):
    """Transformer that removes redundant variable assignments."""

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        """Visit an Assign node and remove redundant assignments."""
        # Check if this is a self-assignment (x = x)
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Name)
            and node.targets[0].id == node.value.id
        ):
            self.record_change(
                node,
                f"Removed redundant self-assignment: {node.targets[0].id} = {node.value.id}",
            )
            return None

        # Check if this is a redundant assignment in a function (result = a + b followed by return result)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            # Get the parent node (function body)
            parent = getattr(node, "parent", None)
            if parent and isinstance(parent, list):
                # Find this node's index in the parent list
                try:
                    idx = parent.index(node)
                    # Check if the next node is a return statement returning the assigned variable
                    if (
                        idx < len(parent) - 1
                        and isinstance(parent[idx + 1], ast.Return)
                        and isinstance(parent[idx + 1].value, ast.Name)
                        and parent[idx + 1].value.id == node.targets[0].id
                    ):
                        # Replace the return statement with a return of the original expression
                        parent[idx + 1].value = node.value
                        self.record_change(
                            node,
                            f"Simplified redundant assignment: {node.targets[0].id} = <expr> followed by return {node.targets[0].id}",
                        )
                        # Remove this assignment
                        return None
                except ValueError:
                    pass

        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Visit a FunctionDef node and set parent references."""
        # Set parent reference for all nodes in the function body
        for child in node.body:
            setattr(child, "parent", node.body)
        return self.generic_visit(node)


class UnusedVariableRemover(AstTransformer):
    """Transformer that removes unused variable assignments."""

    def __init__(self, symbol_usage: dict[str, int]):
        """
        Initialize the transformer.

        Args:
            symbol_usage: Dictionary mapping symbol names to their usage count
        """
        super().__init__()
        self.symbol_usage: dict[str, int] = symbol_usage

    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        """Visit an Assign node and remove unused variable assignments."""
        # Only handle simple assignments to a single target
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            # Debug: Print the symbol usage for this variable
            logger.debug(
                f"Variable: {var_name}, Usage count: {self.symbol_usage.get(var_name, 'Not in dictionary')}"
            )
            logger.debug(f"Symbol usage dictionary: {self.symbol_usage}")

            # Check if the variable is truly unused (usage count is 0)
            if var_name in self.symbol_usage and self.symbol_usage[var_name] == 0:
                # Check if the value has side effects (calls, etc.)
                if not self._has_side_effects(node.value):
                    self.record_change(
                        node, f"Removed unused variable assignment: {var_name}"
                    )
                    return None

        return self.generic_visit(node)

    def _has_side_effects(self, node: ast.AST) -> bool:
        """Check if a node has potential side effects."""
        # Calls might have side effects
        if isinstance(node, ast.Call):
            return True

        # Recursively check for side effects in child nodes
        for child in ast.iter_child_nodes(node):
            if self._has_side_effects(child):
                return True

        return False


class StringLiteralOptimizer(AstTransformer):
    """Transformer that optimizes string literals."""

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Visit a Constant node and optimize string literals."""
        if isinstance(node.value, str):
            # Convert multiple spaces to a single space
            if "  " in node.value:
                old_value = node.value
                new_value = re.sub(r"\s+", " ", node.value)
                if old_value != new_value:
                    self.record_change(
                        node, f"Optimized string literal: removed extra whitespace"
                    )
                    node.value = new_value

        return node

    # For Python < 3.8 compatibility
    def visit_Str(self, node: ast.AST) -> ast.AST:
        """Visit a Str node and optimize string literals (Python < 3.8)."""
        if hasattr(ast, "Str") and isinstance(node, getattr(ast, "Str")):
            # Convert multiple spaces to a single space
            if "  " in node.s:
                old_value = node.s
                new_value = re.sub(r"\s+", " ", node.s)
                if old_value != new_value:
                    self.record_change(
                        node, f"Optimized string literal: removed extra whitespace"
                    )
                    node.s = new_value

        return node


class CodeStyleTransformer(AstTransformer):
    """Transformer that improves code style."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Visit a FunctionDef node and improve its style."""
        # Add docstring if missing
        if not ast.get_docstring(node):
            docstring = f'"""{node.name} function."""'
            docstring_expr = ast.Expr(value=ast.Constant(value=docstring))
            node.body.insert(0, docstring_expr)
            self.record_change(
                node, f"Added missing docstring to function: {node.name}"
            )

        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        """Visit a ClassDef node and improve its style."""
        # Add docstring if missing
        if not ast.get_docstring(node):
            docstring = f'"""{node.name} class."""'
            docstring_expr = ast.Expr(value=ast.Constant(value=docstring))
            node.body.insert(0, docstring_expr)
            self.record_change(node, f"Added missing docstring to class: {node.name}")

        return self.generic_visit(node)


class CodeTransformer(CodeTransformationProvider):
    """Implementation of CodeTransformationProvider for transforming Python code."""

    def __init__(self):
        """Initialize the code transformer."""
        self.analyzer = CodeAnalyzer()
        self.transformers: dict[str, type[AstTransformer]] = {
            # Original names
            "unused_imports": UnusedImportRemover,
            "redundant_assignments": RedundantAssignmentRemover,
            "unused_variables": UnusedVariableRemover,
            "string_optimization": StringLiteralOptimizer,
            "code_style": CodeStyleTransformer,
            # Aliases used in tests
            "remove_unused_imports": UnusedImportRemover,
            "remove_redundant_assignments": RedundantAssignmentRemover,
            "remove_unused_variables": UnusedVariableRemover,
            "optimize_string_literals": StringLiteralOptimizer,
            "improve_code_style": CodeStyleTransformer,
        }

    def transform_code(
        self, code: str, transformations: list[str] | None = None
    ) -> TransformationResult:
        """
        Transform the given code using the specified transformations.

        Args:
            code: The code to transform
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A TransformationResult object containing the transformed code and changes made
        """
        try:
            # Parse the code into an AST
            tree = ast.parse(code)

            # Analyze the code to get symbol usage information
            analysis: FileAnalysisResult = self.analyzer.analyze_code(code)

            # Create symbol usage dictionary
            symbol_usage: dict[str, int] = {}
            for var in analysis.get_variables():
                symbol_usage[var["name"]] = 0

            for class_info in analysis.get_classes():
                symbol_usage[class_info["name"]] = 0

            for func in analysis.get_functions():
                symbol_usage[func["name"]] = 0

            for imp in analysis.get_imports():
                symbol_usage[imp["name"]] = 0

            # Count symbol usage by walking the AST
            symbol_counter = SymbolUsageCounter(symbol_usage)
            symbol_counter.visit(tree)

            # Apply transformations
            changes: list[ChangeRecord] = []
            if transformations is None:
                transformations = list(self.transformers.keys())

            for transform_name in transformations:
                if transform_name in self.transformers:
                    transformer_class = self.transformers[transform_name]

                    # Initialize the transformer with symbol usage if needed
                    if transform_name in ["unused_imports", "unused_variables"]:
                        transformer = cast(
                            Callable[[dict[str, int]], AstTransformer],
                            transformer_class,
                        )(symbol_counter.symbol_usage)
                    else:
                        transformer = transformer_class()

                    # Apply the transformation
                    tree = cast(ast.AST, transformer.visit(tree))

                    # Collect changes
                    changes.extend(transformer.changes)

            # Generate the transformed code
            transformed_code = _to_source(tree)

            return CodeTransformation(
                original_code=code, transformed_code=transformed_code, changes=changes
            )
        except Exception as e:
            logger.error(f"Error transforming code: {str(e)}")
            return CodeTransformation(
                original_code=code,
                transformed_code=code,
                changes=[{"description": f"Error: {str(e)}"}],
            )

    def transform_file(
        self, file_path: str, transformations: list[str] | None = None
    ) -> TransformationResult:
        """
        Transform the code in the given file using the specified transformations.

        Args:
            file_path: The path to the file to transform
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A TransformationResult object containing the transformed code and changes made
        """
        try:
            file_path = os.fspath(file_path)
            # Read the file content
            with open(file_path, encoding="utf-8") as f:
                code = f.read()

            # Transform the code
            result = self.transform_code(code, transformations)

            return result
        except Exception as e:
            logger.error(f"Error transforming file {file_path}: {str(e)}")
            return CodeTransformation(
                original_code="",
                transformed_code="",
                changes=[{"description": f"Error: {str(e)}"}],
            )

    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = True,
        transformations: list[str] | None = None,
    ) -> dict[str, TransformationResult]:
        """
        Transform all Python files in the given directory using the specified transformations.

        Args:
            dir_path: The path to the directory to transform
            recursive: Whether to recursively transform files in subdirectories
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A dictionary mapping file paths to TransformationResult objects
        """
        dir_path = os.fspath(dir_path)
        results: dict[str, TransformationResult] = {}

        # Find all Python files in the directory
        python_files: list[str] = self._find_python_files(dir_path, recursive)

        # Transform each file
        for file_path in python_files:
            try:
                result = self.transform_file(file_path, transformations)
                results[file_path] = result
            except Exception as e:
                logger.error(f"Error transforming file {file_path}: {str(e)}")
                results[file_path] = CodeTransformation(
                    original_code="",
                    transformed_code="",
                    changes=[{"description": f"Error: {str(e)}"}],
                )

        return results

    def _find_python_files(self, dir_path: str, recursive: bool) -> list[str]:
        """Find all Python files in a directory."""
        python_files: list[str] = []
        dir_path = os.fspath(dir_path)

        if recursive:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(dir_path):
                if file.endswith(".py"):
                    python_files.append(os.path.join(dir_path, file))

        return python_files


class SymbolUsageCounter(ast.NodeVisitor):
    """AST visitor for counting symbol usage."""

    def __init__(self, symbol_usage: dict[str, int]):
        """
        Initialize the counter.

        Args:
            symbol_usage: Dictionary mapping symbol names to their usage count
        """
        self.symbol_usage: dict[str, int] = symbol_usage
        # Keep track of variables being assigned to avoid counting them as used
        self.being_assigned: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit an Assign node and handle variable assignments."""
        # Mark targets as being assigned
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.being_assigned.add(target.id)

        # Visit the value first (right side of assignment)
        self.visit(node.value)

        # Then visit the targets (left side of assignment)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.being_assigned.remove(target.id)
                # Don't count the assignment itself as a usage
                # The variable will be counted as used only if it appears elsewhere

    def visit_Name(self, node: ast.Name) -> None:
        """Visit a Name node and count its usage."""
        # Only count as usage if not being assigned
        if node.id in self.symbol_usage and node.id not in self.being_assigned:
            self.symbol_usage[node.id] += 1
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit an Attribute node and count its usage."""
        # Handle module.attribute usage
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            attr_name = node.attr
            full_name = f"{module_name}.{attr_name}"

            if full_name in self.symbol_usage:
                self.symbol_usage[full_name] += 1
            if (
                module_name in self.symbol_usage
                and module_name not in self.being_assigned
            ):
                self.symbol_usage[module_name] += 1

        self.generic_visit(node)
