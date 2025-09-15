import pytest

"""Deterministic tests for CodeTransformer."""

from devsynth.application.code_analysis.transformer import CodeTransformer


@pytest.mark.fast
def test_optimize_string_literals_simple():
    """Optimize extra whitespace in string literals.

    ReqID: N/A"""
    code = "def greet():\n" '    message = "Hello,    world!"\n' "    return message\n"
    transformer = CodeTransformer()
    result = transformer.transform_code(code, ["optimize_string_literals"])
    transformed = result.get_transformed_code()
    assert "Hello, world!" in transformed
    assert any(
        "Optimized string literal" in c["description"] for c in result.get_changes()
    )
