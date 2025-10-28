"""Utilities for grouping functions into generated classes."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from collections.abc import Sequence

from .types import ClassDefNode, FunctionDefNode, StatementList


@dataclass(frozen=True)
class ClassExtractionRequest:
    """Parameters describing how to consolidate functions into a class."""

    functions: Sequence[str]
    class_name: str
    base_classes: Sequence[str] = field(default_factory=tuple)
    docstring: str | None = None


@dataclass(frozen=True)
class GeneratedClass:
    """Representation of a generated class and the methods it wraps."""

    node: ClassDefNode
    methods: tuple[FunctionDefNode, ...]


def build_class_from_functions(
    request: ClassExtractionRequest, functions: Sequence[FunctionDefNode]
) -> GeneratedClass:
    """Construct a class definition from the extracted function nodes."""

    class_body: StatementList = []
    if request.docstring is not None:
        class_body.append(ast.Expr(value=ast.Constant(value=request.docstring)))

    methods: list[FunctionDefNode] = []
    for function in functions:
        args = [ast.arg(arg="self")]
        args.extend(function.args.args)
        function.args.args = args
        methods.append(function)
        class_body.append(function)

    class_def = ast.ClassDef(
        name=request.class_name,
        bases=[ast.Name(id=base, ctx=ast.Load()) for base in request.base_classes],
        keywords=[],
        body=class_body,
        decorator_list=[],
        type_params=[],
    )
    return GeneratedClass(node=class_def, methods=tuple(methods))


class FunctionToClassExtractor(ast.NodeTransformer):
    """Collect selected functions and wrap them into a generated class."""

    def __init__(self, request: ClassExtractionRequest) -> None:
        self.request = request
        self.extracted_functions: list[FunctionDefNode] = []
        self.missing_functions: list[str] = []

    def visit_Module(self, node: ast.Module) -> ast.AST:  # noqa: N802
        new_body: StatementList = []
        requested = {name for name in self.request.functions}
        for statement in node.body:
            if isinstance(statement, ast.FunctionDef) and statement.name in requested:
                requested.remove(statement.name)
                self.extracted_functions.append(statement)
                continue
            new_body.append(self.visit(statement))
        self.missing_functions = sorted(requested)
        if self.extracted_functions:
            generated_class = build_class_from_functions(
                self.request, self.extracted_functions
            )
            new_body.append(generated_class.node)
        node.body = new_body
        return node
