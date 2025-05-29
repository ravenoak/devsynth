"""
Unit tests for the AST transformer.

This module contains tests for the AstTransformer class, which provides
utilities for transforming Python code using AST manipulation.
"""

import unittest
from devsynth.application.code_analysis.ast_transformer import AstTransformer


class TestAstTransformer(unittest.TestCase):
    """Test the AST transformer."""

    def setUp(self):
        """Set up the test environment."""
        self.transformer = AstTransformer()

        # Sample code for testing
        self.sample_code = """
def calculate_sum(a, b):
    result = a + b
    return result

def main():
    x = 5
    y = 10
    total = calculate_sum(x, y)
    print(f"The sum is {total}")

    # Some additional code
    for i in range(3):
        print(f"Iteration {i}")
"""

    def test_rename_function(self):
        """Test renaming a function."""
        # Create a fresh transformer for this test
        transformer = AstTransformer()

        # Rename a function
        new_code = transformer.rename_identifier(self.sample_code, "calculate_sum", "add_numbers")
        self.assertIn("def add_numbers(a, b):", new_code)
        self.assertIn("total = add_numbers(x, y)", new_code)
        self.assertNotIn("calculate_sum", new_code)

    def test_rename_variable(self):
        """Test renaming a variable."""
        # Create a fresh transformer for this test
        transformer = AstTransformer()

        # Rename a variable
        new_code = transformer.rename_identifier(self.sample_code, "result", "sum_result")

        # Check for the presence of the expected strings
        self.assertIn("sum_result = a + b", new_code)
        self.assertIn("return sum_result", new_code)

        # Check that the variable has been renamed in all occurrences
        # We need to use a regex with word boundaries to check for the exact identifier
        import re
        pattern = r"\bresult\b\s*=\s*a\s*\+\s*b"
        match = re.search(pattern, new_code)
        self.assertIsNone(match, f"Found 'result = a + b' as a standalone identifier in the code: {new_code}")

    def test_rename_parameter(self):
        """Test renaming a parameter."""
        # Create a fresh transformer for this test
        transformer = AstTransformer()

        # Rename a parameter
        new_code = transformer.rename_identifier(self.sample_code, "a", "num1")
        self.assertIn("def calculate_sum(num1, b):", new_code)
        self.assertIn("result = num1 + b", new_code)
        self.assertNotIn("result = a + b", new_code)

    def test_extract_function(self):
        """Test extracting a block of code into a new function."""
        # Extract the print statements in the for loop
        new_code = self.transformer.extract_function(
            self.sample_code,
            13,  # Line with "for i in range(3):"
            14,  # Line with "print(f"Iteration {i}")"
            "print_iterations",
            ["i"]
        )

        # Check that the new function is created
        self.assertIn("def print_iterations(i):", new_code)
        self.assertIn('print(f"Iteration {i}")', new_code)

        # Check that the original code is replaced with a function call
        self.assertIn("print_iterations(i)", new_code)

        # Make sure the code is still valid Python
        self.assertTrue(self.transformer.validate_syntax(new_code))

    def test_add_docstring(self):
        """Test adding a docstring to a function, class, or module."""
        # Add a docstring to a function
        docstring = "Calculate the sum of two numbers."
        new_code = self.transformer.add_docstring(self.sample_code, "calculate_sum", docstring)
        self.assertIn('def calculate_sum(a, b):', new_code)
        self.assertIn('    """Calculate the sum of two numbers."""', new_code)

        # Add a docstring to the module
        module_docstring = "Sample module for testing."
        new_code = self.transformer.add_docstring(self.sample_code, None, module_docstring)
        self.assertIn('"""Sample module for testing."""', new_code)

        # Make sure the code is still valid Python
        self.assertTrue(self.transformer.validate_syntax(new_code))

    def test_validate_syntax(self):
        """Test validating code syntax."""
        # Valid code
        self.assertTrue(self.transformer.validate_syntax(self.sample_code))

        # Invalid code
        invalid_code = """
def broken_function(
    print("Missing closing parenthesis"
"""
        self.assertFalse(self.transformer.validate_syntax(invalid_code))

    def test_complex_transformations(self):
        """Test more complex transformations."""
        # Rename a function and add a docstring
        code = self.sample_code
        code = self.transformer.rename_identifier(code, "calculate_sum", "add_numbers")
        code = self.transformer.add_docstring(code, "add_numbers", "Add two numbers and return the result.")

        # Verify the changes
        self.assertIn("def add_numbers(a, b):", code)
        self.assertIn('    """Add two numbers and return the result."""', code)
        self.assertIn("total = add_numbers(x, y)", code)
        self.assertNotIn("calculate_sum", code)

        # Make sure the code is still valid Python
        self.assertTrue(self.transformer.validate_syntax(code))


if __name__ == "__main__":
    unittest.main()
