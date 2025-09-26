"""Unit tests for the AST transformer.

This module contains tests for the AstTransformer class, which provides
utilities for transforming Python code using AST manipulation.
"""

import unittest

import pytest

from devsynth.application.code_analysis.ast_transformer import (
    AstTransformer,
    DocstringSpec,
    FunctionExtractionRequest,
)


class TestAstTransformer(unittest.TestCase):
    """Test the AST transformer.

    ReqID: N/A"""

    def setUp(self):
        """Set up the test environment."""
        self.transformer = AstTransformer()
        self.sample_code = (
            "\ndef calculate_sum(a, b):\n"
            "    result = a + b\n"
            "    return result\n\n"
            "def main():\n"
            "    x = 5\n"
            "    y = 10\n"
            "    total = calculate_sum(x, y)\n"
            '    print(f"The sum is {total}")\n\n'
            "    # Some additional code\n"
            "    for i in range(3):\n"
            '        print(f"Iteration {i}")\n'
        )

    @pytest.mark.fast
    def test_rename_function_succeeds(self):
        """Test renaming a function.

        ReqID: N/A"""
        transformer = AstTransformer()
        new_code = transformer.rename_identifier(
            self.sample_code, "calculate_sum", "add_numbers"
        )
        self.assertIn("def add_numbers(a, b):", new_code)
        self.assertIn("total = add_numbers(x, y)", new_code)
        self.assertNotIn("calculate_sum", new_code)

    @pytest.mark.fast
    def test_rename_variable_succeeds(self):
        """Test renaming a variable.

        ReqID: N/A"""
        transformer = AstTransformer()
        new_code = transformer.rename_identifier(
            self.sample_code, "result", "sum_result"
        )
        self.assertIn("sum_result = a + b", new_code)
        self.assertIn("return sum_result", new_code)
        import re

        pattern = "\\bresult\\b\\s*=\\s*a\\s*\\+\\s*b"
        match = re.search(pattern, new_code)
        self.assertIsNone(
            match,
            (
                "Found 'result = a + b' as a standalone identifier in the code: "
                f"{new_code}"
            ),
        )

    @pytest.mark.fast
    def test_rename_parameter_succeeds(self):
        """Test renaming a parameter.

        ReqID: N/A"""
        transformer = AstTransformer()
        new_code = transformer.rename_identifier(self.sample_code, "a", "num1")
        self.assertIn("def calculate_sum(num1, b):", new_code)
        self.assertIn("result = num1 + b", new_code)
        self.assertNotIn("result = a + b", new_code)

    @pytest.mark.fast
    def test_rename_identifier_no_change(self):
        """Ensure code is unchanged when identifier is absent.

        ReqID: N/A"""
        code = "def foo():\n    return 1\n"
        transformer = AstTransformer()
        new_code = transformer.rename_identifier(code, "bar", "baz")
        self.assertEqual(code, new_code)

    @pytest.mark.fast
    def test_extract_function_succeeds(self):
        """Test extracting a block of code into a new function.

        ReqID: N/A"""
        request = FunctionExtractionRequest(
            start_line=13,
            end_line=14,
            function_name="print_iterations",
            parameters=["i"],
        )
        new_code = self.transformer.extract_function(self.sample_code, request)
        self.assertIn("def print_iterations(i):", new_code)
        self.assertIn('print(f"Iteration {i}")', new_code)
        self.assertIn("print_iterations(i)", new_code)
        self.assertTrue(self.transformer.validate_syntax(new_code))

    @pytest.mark.fast
    def test_add_docstring_succeeds(self):
        """Test adding a docstring to a function, class, or module.

        ReqID: N/A"""
        docstring = "Calculate the sum of two numbers."
        spec = DocstringSpec(target="calculate_sum", docstring=docstring)
        new_code = self.transformer.add_docstring(self.sample_code, spec)
        self.assertIn("def calculate_sum(a, b):", new_code)
        self.assertIn('    """Calculate the sum of two numbers."""', new_code)
        module_docstring = "Sample module for testing."
        new_code = self.transformer.add_docstring(
            self.sample_code, DocstringSpec(target=None, docstring=module_docstring)
        )
        self.assertIn('"""Sample module for testing."""', new_code)
        self.assertTrue(self.transformer.validate_syntax(new_code))

    @pytest.mark.fast
    def test_validate_syntax_is_valid(self):
        """Test validating code syntax.

        ReqID: N/A"""
        self.assertTrue(self.transformer.validate_syntax(self.sample_code))
        invalid_code = (
            '\ndef broken_function(\n    print("Missing closing parenthesis"\n'
        )
        self.assertFalse(self.transformer.validate_syntax(invalid_code))

    @pytest.mark.fast
    def test_complex_transformations_succeeds(self):
        """Test more complex transformations.

        ReqID: N/A"""
        code = self.sample_code
        code = self.transformer.rename_identifier(code, "calculate_sum", "add_numbers")
        code = self.transformer.add_docstring(
            code,
            DocstringSpec(
                target="add_numbers",
                docstring="Add two numbers and return the result.",
            ),
        )
        self.assertIn("def add_numbers(a, b):", code)
        self.assertIn('    """Add two numbers and return the result."""', code)
        self.assertIn("total = add_numbers(x, y)", code)
        self.assertNotIn("calculate_sum", code)
        self.assertTrue(self.transformer.validate_syntax(code))

    @pytest.mark.fast
    def test_remove_unused_imports_and_variables_succeeds(self):
        """Test removing unused imports and variables.

        ReqID: N/A"""
        code = (
            "\nimport os\nimport sys\n\n"
            "def func():\n"
            "    unused_var = 1\n"
            "    return os.path.basename('x')\n"
        )
        code = self.transformer.remove_unused_imports(code)
        code = self.transformer.remove_unused_variables(code)
        self.assertNotIn("sys", code)
        self.assertNotIn("unused_var", code)

    @pytest.mark.fast
    def test_optimize_string_literals_succeeds(self):
        """Test optimizing string operations.

        ReqID: N/A"""
        code = (
            "\ndef greet(name):\n"
            '    greeting = "Hello, " + name + "!"\n'
            "    return greeting\n"
        )
        optimized = self.transformer.optimize_string_literals(code)
        self.assertIn("Hello, {name}!", optimized)


if __name__ == "__main__":
    unittest.main()
