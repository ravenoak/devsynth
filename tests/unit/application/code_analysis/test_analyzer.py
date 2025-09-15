import pytest

"""Tests for the CodeAnalyzer class with simple code samples."""

from devsynth.application.code_analysis.analyzer import CodeAnalyzer


@pytest.mark.fast
def test_analyze_code_simple():
    """Analyze minimal code and ensure deterministic output.

    ReqID: N/A"""
    code = "import os\n\nx = 1\n\ndef add(y):\n    return x + y\n"
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_code(code, "sample.py")
    assert any(imp["name"] == "os" for imp in result.get_imports())
    assert any(var["name"] == "x" for var in result.get_variables())
    assert any(func["name"] == "add" for func in result.get_functions())
    assert result.get_classes() == []
    assert result.get_docstring() == ""
