"""Unit tests for specialised AST transformer helper modules."""

from __future__ import annotations

import ast
from textwrap import dedent

import pytest

from devsynth.application.code_analysis.transformers import (
    ClassExtractionRequest,
    DocstringSpec,
    MethodConversionPlan,
    apply_docstring_spec,
    build_class_from_functions,
    build_method_from_function,
)


@pytest.mark.fast
def test_apply_docstring_spec_inserts_function_docstring() -> None:
    """Docstring helpers inject the configured docstring into target functions."""

    module = ast.parse(
        dedent(
            """
            def greet(name):
                return f"Hello, {name}!"
            """
        )
    )
    function = module.body[0]
    assert isinstance(function, ast.FunctionDef)

    spec = DocstringSpec(target="greet", docstring="Say hello.")
    result = apply_docstring_spec(module, spec)

    assert result.target_found is True
    docstring_expr = result.tree.body[0].body[0]
    assert isinstance(docstring_expr, ast.Expr)
    assert isinstance(docstring_expr.value, ast.Constant)
    assert docstring_expr.value.value == "Say hello."


@pytest.mark.fast
def test_build_method_from_function_respects_method_type() -> None:
    """Function to method conversion adds appropriate receivers and decorators."""

    function_module = ast.parse(
        dedent(
            """
            def helper(value):
                return value * 2
            """
        )
    )
    helper_function = function_module.body[0]
    assert isinstance(helper_function, ast.FunctionDef)

    class_plan = MethodConversionPlan(
        function_name="helper", class_name="Worker", method_type="class"
    )
    class_method = build_method_from_function(helper_function, class_plan).node
    assert class_method.args.args[0].arg == "cls"
    assert any(
        isinstance(decorator, ast.Name) and decorator.id == "classmethod"
        for decorator in class_method.decorator_list
    )

    static_plan = MethodConversionPlan(
        function_name="helper", class_name="Worker", method_type="static"
    )
    static_method = build_method_from_function(helper_function, static_plan).node
    assert not static_method.args.args or static_method.args.args[0].arg != "self"
    assert any(
        isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
        for decorator in static_method.decorator_list
    )


@pytest.mark.fast
def test_build_class_from_functions_wraps_functions() -> None:
    """Class extraction wraps selected functions and prefixes `self` arguments."""

    module = ast.parse(
        dedent(
            """
            def load_config(path):
                return path

            def save_config(path, value):
                return value
            """
        )
    )
    load_config = module.body[0]
    save_config = module.body[1]
    assert isinstance(load_config, ast.FunctionDef)
    assert isinstance(save_config, ast.FunctionDef)

    request = ClassExtractionRequest(
        functions=("load_config", "save_config"),
        class_name="ConfigService",
        base_classes=("BaseService",),
        docstring="Manage configuration persistence.",
    )
    generated = build_class_from_functions(request, (load_config, save_config))

    assert generated.node.name == "ConfigService"
    assert [base.id for base in generated.node.bases] == ["BaseService"]
    first_stmt = generated.node.body[0]
    assert isinstance(first_stmt, ast.Expr)
    assert isinstance(first_stmt.value, ast.Constant)
    assert first_stmt.value.value == "Manage configuration persistence."

    methods = generated.methods
    assert methods[0].args.args[0].arg == "self"
    assert methods[1].args.args[0].arg == "self"
