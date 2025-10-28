"""Docstring transformation helpers with precise typing."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Optional, cast

from .types import ModuleNode, StatementList


@dataclass(frozen=True)
class DocstringSpec:
    """Description of a docstring insertion target."""

    target: str | None
    docstring: str


@dataclass(frozen=True)
class DocstringMutationResult:
    """Result of applying a docstring mutation to a module."""

    tree: ModuleNode
    target_found: bool


class DocstringAdder(ast.NodeTransformer):
    """Insert docstrings according to a :class:`DocstringSpec`."""

    def __init__(self, spec: DocstringSpec) -> None:
        self.spec = spec
        self.target_found: bool = False

    def _ensure_docstring(self, body: StatementList) -> None:
        docstring_node = ast.Expr(value=ast.Constant(value=self.spec.docstring))
        if body and isinstance(body[0], ast.Expr) and _is_docstring_expr(body[0]):
            body[0] = docstring_node
        else:
            body.insert(0, docstring_node)

    def visit_Module(self, node: ModuleNode) -> ModuleNode:  # noqa: N802
        if self.spec.target is None:
            self._ensure_docstring(node.body)
            self.target_found = True
        return cast(ModuleNode, self.generic_visit(node))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
        if self.spec.target == node.name:
            self._ensure_docstring(node.body)
            self.target_found = True
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:  # noqa: N802
        if self.spec.target == node.name:
            self._ensure_docstring(node.body)
            self.target_found = True
        return self.generic_visit(node)


def apply_docstring_spec(
    tree: ModuleNode, spec: DocstringSpec
) -> DocstringMutationResult:
    """Apply a docstring insertion specification to a module."""

    transformer = DocstringAdder(spec)
    mutated = transformer.visit(tree)
    return DocstringMutationResult(
        tree=cast(ModuleNode, mutated), target_found=transformer.target_found
    )


def _is_docstring_expr(node: ast.Expr) -> bool:
    return isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
