"""Utilities for converting free functions into class methods."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Literal, cast

from .types import ClassDefNode, FunctionDefNode

MethodType = Literal["instance", "class", "static"]


@dataclass(frozen=True)
class MethodConversionPlan:
    """Parameters for converting a top-level function into a class method."""

    function_name: str
    class_name: str
    method_type: MethodType = "instance"


@dataclass(frozen=True)
class MethodDefinition:
    """A generated method ready to be inserted into a class body."""

    node: FunctionDefNode


def build_method_from_function(
    function: FunctionDefNode, plan: MethodConversionPlan
) -> MethodDefinition:
    """Create a method definition from a top-level function and conversion plan."""

    method_node = ast.FunctionDef(
        name=function.name,
        args=ast.arguments(
            posonlyargs=list(function.args.posonlyargs),
            args=list(function.args.args),
            vararg=function.args.vararg,
            kwonlyargs=list(function.args.kwonlyargs),
            kw_defaults=list(function.args.kw_defaults),
            kwarg=function.args.kwarg,
            defaults=list(function.args.defaults),
        ),
        body=[
            ast.fix_missing_locations(ast.copy_location(stmt, stmt))
            for stmt in function.body
        ],
        decorator_list=[],
        returns=function.returns,
        type_comment=function.type_comment,
        type_params=list(getattr(function, "type_params", [])),
    )

    if plan.method_type == "instance":
        method_node.args.args.insert(0, ast.arg(arg="self"))
    elif plan.method_type == "class":
        method_node.args.args.insert(0, ast.arg(arg="cls"))
        method_node.decorator_list.append(ast.Name(id="classmethod", ctx=ast.Load()))
    else:
        method_node.decorator_list.append(ast.Name(id="staticmethod", ctx=ast.Load()))

    return MethodDefinition(node=method_node)


class FunctionToMethodConverter(ast.NodeTransformer):
    """Convert a top-level function into a method on a class."""

    def __init__(self, plan: MethodConversionPlan) -> None:
        self.plan = plan
        self.function_found: bool = False
        self.class_found: bool = False
        self._function_node: FunctionDefNode | None = None

    def visit_FunctionDef(self, node: FunctionDefNode) -> ast.AST | None:  # noqa: N802
        if node.name == self.plan.function_name:
            self.function_found = True
            self._function_node = node
            return None
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ClassDefNode) -> ClassDefNode:  # noqa: N802
        node = cast(ClassDefNode, self.generic_visit(node))
        if node.name != self.plan.class_name:
            return node
        self.class_found = True
        if self._function_node is None:
            return node

        method_definition = build_method_from_function(self._function_node, self.plan)
        node.body.append(method_definition.node)
        return node
