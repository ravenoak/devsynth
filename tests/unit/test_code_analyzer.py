"""
Tests for the CodeAnalyzer application logic.
"""

import os
import tempfile
import unittest
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock

from devsynth.domain.interfaces.code_analysis import CodeAnalysisProvider, FileAnalysisResult, CodeAnalysisResult
from devsynth.domain.models.code_analysis import FileAnalysis, CodeAnalysis
from devsynth.application.code_analysis.analyzer import CodeAnalyzer


class TestCodeAnalyzer(unittest.TestCase):
    """Test the CodeAnalyzer application logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer()

        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

        # Create a test Python file
        self.test_file_path = os.path.join(self.test_dir, "test_file.py")
        with open(self.test_file_path, "w") as f:
            f.write("""\"\"\"Test module docstring.\"\"\"
import os
import sys

class TestClass:
    \"\"\"Test class docstring.\"\"\"

    def __init__(self, value):
        \"\"\"Initialize with a value.\"\"\"
        self.value = value

    def test_method(self):
        \"\"\"Test method docstring.\"\"\"
        return self.value

def test_function(param1, param2=None):
    \"\"\"Test function docstring.\"\"\"
    return param1

TEST_VARIABLE = "test"
""")

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_analyze_file(self):
        """Test analyzing a single file."""
        result = self.analyzer.analyze_file(self.test_file_path)

        # Verify the result is a FileAnalysisResult
        self.assertIsInstance(result, FileAnalysisResult)

        # Check imports
        imports = result.get_imports()
        self.assertEqual(len(imports), 2)
        self.assertEqual(imports[0]["name"], "os")
        self.assertEqual(imports[1]["name"], "sys")

        # Check classes
        classes = result.get_classes()
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["name"], "TestClass")
        self.assertIn("test_method", classes[0]["methods"])

        # Check functions
        functions = result.get_functions()
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["name"], "test_function")
        self.assertIn("param1", functions[0]["params"])

        # Check variables
        variables = result.get_variables()
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0]["name"], "TEST_VARIABLE")

        # Check docstring
        self.assertEqual(result.get_docstring(), "Test module docstring.")

        # Check metrics
        metrics = result.get_metrics()
        self.assertIn("lines_of_code", metrics)
        self.assertGreater(metrics["lines_of_code"], 0)

    def test_analyze_directory(self):
        """Test analyzing a directory of files."""
        # Create another test file
        another_file_path = os.path.join(self.test_dir, "another_file.py")
        with open(another_file_path, "w") as f:
            f.write("""
from test_file import TestClass

\"\"\"Another test module.\"\"\"

def another_function():
    \"\"\"Another function.\"\"\"
    return TestClass(42).test_method()
""")

        result = self.analyzer.analyze_directory(self.test_dir)

        # Verify the result is a CodeAnalysisResult
        self.assertIsInstance(result, CodeAnalysisResult)

        # Check that both files were analyzed
        self.assertIsNotNone(result.get_file_analysis(self.test_file_path))
        self.assertIsNotNone(result.get_file_analysis(another_file_path))

        # Check symbol references
        test_class_refs = result.get_symbol_references("TestClass")
        self.assertGreaterEqual(len(test_class_refs), 1)

        # Check dependencies
        dependencies = result.get_dependencies("another_file")
        self.assertIn("test_file", dependencies)

        # Check metrics
        metrics = result.get_metrics()
        self.assertIn("total_files", metrics)
        self.assertEqual(metrics["total_files"], 2)

    def test_analyze_code(self):
        """Test analyzing a string of code."""
        code = """
import math

def calculate_area(radius):
    \"\"\"Calculate the area of a circle.\"\"\"
    return math.pi * radius ** 2

RADIUS = 5
"""

        result = self.analyzer.analyze_code(code)

        # Verify the result is a FileAnalysisResult
        self.assertIsInstance(result, FileAnalysisResult)

        # Check imports
        imports = result.get_imports()
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0]["name"], "math")

        # Check functions
        functions = result.get_functions()
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]["name"], "calculate_area")

        # Check variables
        variables = result.get_variables()
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0]["name"], "RADIUS")

    def test_project_structure_metrics(self):
        """Test analyzing project structure metrics."""
        with patch.object(self.analyzer, "_find_python_files") as mock_find:
            mock_find.return_value = [self.test_file_path]
            metrics = self.analyzer.analyze_project_structure()
        self.assertEqual(metrics["files"], 1)
        self.assertEqual(metrics["functions"], 1)


if __name__ == "__main__":
    unittest.main()
