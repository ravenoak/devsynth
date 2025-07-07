"""
Unit tests for the code transformation functionality.

This module contains tests for the various transformer classes in the
transformer.py module, including the CodeTransformer class and its methods
for transforming code, files, and directories.
"""

import os
import tempfile
import pytest
import ast
from pathlib import Path
from unittest.mock import patch, MagicMock

from devsynth.application.code_analysis.transformer import (
    AstTransformer,
    UnusedImportRemover,
    RedundantAssignmentRemover,
    UnusedVariableRemover,
    StringLiteralOptimizer,
    CodeStyleTransformer,
    CodeTransformer,
    SymbolUsageCounter
)


@pytest.fixture
def sample_code():
    """Return sample Python code for testing transformations."""
    return """
import os
import sys
import re  # This import is unused

def calculate_sum(a, b):
    # Redundant assignment
    result = a + b
    return result

def main():
    x = 5
    y = 10
    z = 15  # This variable is unused

    # String concatenation that could be optimized
    greeting = "Hello, " + "world!"

    total = calculate_sum(x, y)
    print(f"The sum is {total}")
"""


@pytest.fixture
def test_file_path():
    """Create a temporary file with sample code for testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_file.write("""
import os
import sys
import re  # This import is unused

def calculate_sum(a, b):
    # Redundant assignment
    result = a + b
    return result

def main():
    x = 5
    y = 10
    z = 15  # This variable is unused

    # String concatenation that could be optimized
    greeting = "Hello, " + "world!"

    total = calculate_sum(x, y)
    print(f"The sum is {total}")
""".encode('utf-8'))
        temp_path = temp_file.name

    yield temp_path

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def test_directory():
    """Create a temporary directory with Python files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a basic directory structure
        dir_path = Path(temp_dir)

        # Create a Python file with unused imports
        (dir_path / "unused_imports.py").write_text("""
import os
import sys
import re  # This import is unused

def main():
    print(os.path.join("a", "b"))
""")

        # Create a Python file with unused variables
        (dir_path / "unused_variables.py").write_text("""
def process_data(data):
    result = []
    count = 0  # This variable is unused

    for item in data:
        result.append(item * 2)

    return result
""")

        # Create a subdirectory with a Python file
        subdir = dir_path / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.py").write_text("""
def nested_function():
    x = 10
    y = 20  # This variable is unused
    return x
""")

        yield str(dir_path)


class TestAstTransformer:
    """Test the base AstTransformer class."""

    def test_record_change(self):
        """Test that changes are recorded correctly."""
        transformer = AstTransformer()
        node = MagicMock()
        node.lineno = 10
        node.col_offset = 5
        transformer.record_change(node, "Test change")

        assert len(transformer.changes) == 1
        assert transformer.changes[0]["description"] == "Test change"
        assert transformer.changes[0]["line"] == 10
        assert transformer.changes[0]["col"] == 5


class TestUnusedImportRemover:
    """Test the UnusedImportRemover class."""

    def test_remove_unused_imports(self, sample_code):
        """Test that unused imports are removed."""
        # Create a symbol usage dictionary where 're' is not used
        symbol_usage = {"os": 1, "sys": 1, "re": 0}

        # Create a transformer and parse the code
        transformer = CodeTransformer()
        result = transformer.transform_code(sample_code, ["remove_unused_imports"])

        # Check that the unused import was removed
        assert "import re" not in result.get_transformed_code()
        assert "import os" in result.get_transformed_code()
        assert "import sys" in result.get_transformed_code()

        # Check that the changes were recorded
        assert any("Removed unused import" in change["description"] for change in result.get_changes())


class TestRedundantAssignmentRemover:
    """Test the RedundantAssignmentRemover class."""

    def test_remove_redundant_assignments(self, sample_code):
        """Test that redundant assignments are removed."""
        transformer = CodeTransformer()
        result = transformer.transform_code(sample_code, ["remove_redundant_assignments"])

        # Check that the redundant assignment was simplified
        assert "return a + b" in result.get_transformed_code()
        assert "result = a + b" not in result.get_transformed_code()

        # Check that the changes were recorded
        assert any("Simplified redundant assignment" in change["description"] for change in result.get_changes())


class TestUnusedVariableRemover:
    """Test the UnusedVariableRemover class."""

    def test_remove_unused_variables(self, sample_code):
        """Test that unused variables are removed."""
        transformer = CodeTransformer()
        result = transformer.transform_code(sample_code, ["remove_unused_variables"])

        # Check that the unused variable was removed
        assert "z = 15" not in result.get_transformed_code()
        assert "x = 5" in result.get_transformed_code()
        assert "y = 10" in result.get_transformed_code()

        # Check that the changes were recorded
        assert any("Removed unused variable" in change["description"] for change in result.get_changes())


class TestStringLiteralOptimizer:
    """Test the StringLiteralOptimizer class."""

    def test_optimize_string_literals(self, sample_code):
        """Test that string literals are optimized."""
        transformer = CodeTransformer()
        result = transformer.transform_code(sample_code, ["optimize_string_literals"])

        # Check that the string concatenation was optimized
        assert '"Hello, world!"' in result.get_transformed_code()
        assert '"Hello, " + "world!"' not in result.get_transformed_code()

        # Check that the changes were recorded
        assert any("Optimized string literal" in change["description"] for change in result.get_changes())


class TestCodeStyleTransformer:
    """Test the CodeStyleTransformer class."""

    def test_improve_code_style(self):
        """Test that code style is improved."""
        code = """
def function_without_docstring(a, b):
    return a + b

class ClassWithoutDocstring:
    def method_without_docstring(self):
        pass
"""

        transformer = CodeTransformer()
        result = transformer.transform_code(code, ["improve_code_style"])

        # Check that docstrings were added
        assert '"""' in result.get_transformed_code()

        # Check that the changes were recorded
        assert any("Added docstring" in change["description"] for change in result.get_changes())


class TestCodeTransformer:
    """Test the CodeTransformer class."""

    def test_transform_code(self, sample_code):
        """Test transforming code with multiple transformations."""
        transformer = CodeTransformer()
        result = transformer.transform_code(
            sample_code, 
            ["remove_unused_imports", "remove_unused_variables", "optimize_string_literals"]
        )

        # Check that all transformations were applied
        assert "import re" not in result.get_transformed_code()
        assert "z = 15" not in result.get_transformed_code()
        assert '"Hello, world!"' in result.get_transformed_code()

        # Check that the result has the expected methods
        assert hasattr(result, "get_original_code")
        assert hasattr(result, "get_transformed_code")
        assert hasattr(result, "get_changes")

    def test_transform_file(self, test_file_path):
        """Test transforming a file."""
        transformer = CodeTransformer()
        result = transformer.transform_file(
            test_file_path, 
            ["remove_unused_imports", "remove_unused_variables"]
        )

        # Check that the result has the expected methods
        assert hasattr(result, "get_original_code")
        assert hasattr(result, "get_transformed_code")
        assert hasattr(result, "get_changes")

        # Check that transformations were applied
        assert "import re" not in result.get_transformed_code()
        assert "z = 15" not in result.get_transformed_code()

    def test_transform_directory(self, test_directory):
        """Test transforming a directory."""
        transformer = CodeTransformer()
        results = transformer.transform_directory(
            test_directory, 
            recursive=True,
            transformations=["remove_unused_imports", "remove_unused_variables"]
        )

        # Check that we got results for all Python files
        assert len(results) == 3

        # Check that each result has the expected methods
        for file_path, result in results.items():
            assert hasattr(result, "get_original_code")
            assert hasattr(result, "get_transformed_code")
            assert hasattr(result, "get_changes")

        # Check that transformations were applied to each file
        unused_imports_path = next(path for path in results.keys() if "unused_imports.py" in path)
        unused_imports_result = results[unused_imports_path]
        assert "import re" not in unused_imports_result.get_transformed_code()

        unused_variables_path = next(path for path in results.keys() if "unused_variables.py" in path)
        unused_variables_result = results[unused_variables_path]
        assert "count = 0" not in unused_variables_result.get_transformed_code()

        nested_file_path = next(path for path in results.keys() if "nested_file.py" in path)
        nested_file_result = results[nested_file_path]
        assert "y = 20" not in nested_file_result.get_transformed_code()

    def test_find_python_files(self, test_directory):
        """Test finding Python files in a directory."""
        transformer = CodeTransformer()
        files = transformer._find_python_files(test_directory, recursive=True)

        # Check that all Python files were found
        assert len(files) == 3
        assert any("unused_imports.py" in f for f in files)
        assert any("unused_variables.py" in f for f in files)
        assert any("nested_file.py" in f for f in files)

        # Test non-recursive mode
        files = transformer._find_python_files(test_directory, recursive=False)

        # Check that only top-level Python files were found
        assert len(files) == 2
        assert any("unused_imports.py" in f for f in files)
        assert any("unused_variables.py" in f for f in files)
        assert not any("nested_file.py" in f for f in files)


class TestSymbolUsageCounter:
    """Test the SymbolUsageCounter class."""

    def test_count_symbol_usage(self):
        """Test counting symbol usage in code."""
        code = """
import os
import sys

def main():
    path = os.path.join("a", "b")
    print(path)
"""

        # Parse the code into an AST
        tree = ast.parse(code)

        # Create a symbol usage dictionary
        symbol_usage = {}

        # Count symbol usage
        counter = SymbolUsageCounter(symbol_usage)
        counter.visit(tree)

        # Check that symbols were counted correctly
        assert "os" in symbol_usage
        assert symbol_usage["os"] > 0
        assert "path" in symbol_usage
        assert symbol_usage["path"] > 0
        assert "sys" in symbol_usage
        assert symbol_usage["sys"] == 0  # Unused import
