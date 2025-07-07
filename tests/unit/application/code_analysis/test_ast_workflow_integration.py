import unittest
from unittest.mock import patch, MagicMock
import ast
from devsynth.application.code_analysis.ast_workflow_integration import AstWorkflowIntegration
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.domain.models.memory import MemoryItem, MemoryType


class MockMemoryStore:
    def __init__(self):
        self.items = {}
        self.counter = 0

    def store(self, item: MemoryItem) -> str:
        self.counter += 1
        item_id = str(self.counter)
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str):
        return self.items.get(item_id)

    def search(self, query, limit=10):
        return list(self.items.values())[:limit]


class TestAstWorkflowIntegration(unittest.TestCase):
    def setUp(self):
        self.memory_manager = MemoryManager({'default': MockMemoryStore()})
        self.integration = AstWorkflowIntegration(self.memory_manager)
        self.analyzer = CodeAnalyzer()

        # Sample code for testing
        self.sample_code = """\
\"\"\"Example module\"\"\"

def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

class Calculator:
    \"\"\"Performs calculations.\"\"\"
    def multiply(self, a, b):
        \"\"\"Multiply two numbers.\"\"\"
        return a * b
"""

    def test_complexity_and_readability_metrics(self):
        analysis = self.analyzer.analyze_code(self.sample_code)
        complexity = self.integration._calculate_complexity(analysis)
        readability = self.integration._calculate_readability(analysis)
        maintainability = self.integration._calculate_maintainability(analysis)

        self.assertAlmostEqual(complexity, 0.65, places=2)
        self.assertAlmostEqual(readability, 1.0, places=2)
        self.assertAlmostEqual(maintainability, 0.86, places=2)

    def test_differentiate_selects_best_option(self):
        code_no_docs = """\

def add(a, b):
    return a + b

class Calculator:
    def multiply(self, a, b):
        return a * b
"""
        code_with_docs = self.sample_code
        options = [
            {"name": "no_docs", "description": "", "code": code_no_docs},
            {"name": "with_docs", "description": "", "code": code_with_docs},
        ]
        selected = self.integration.differentiate_implementation_quality(options, "task")
        self.assertEqual(selected["name"], "with_docs")
        metrics = selected["metrics"]
        for key in ["complexity", "readability", "maintainability"]:
            self.assertGreaterEqual(metrics[key], 0.0)
            self.assertLessEqual(metrics[key], 1.0)

    def test_expand_implementation_options(self):
        """Test expanding implementation options for a given code."""
        # Mock the memory manager's store method
        with patch.object(self.memory_manager, 'store') as mock_store:
            mock_store.return_value = "test_memory_id"

            # Call the method under test
            result = self.integration.expand_implementation_options(self.sample_code, "test_task")

            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertIn("original", result)
            self.assertIn("alternatives", result)
            self.assertEqual(result["original"], self.sample_code)

            # Verify that memory was stored
            mock_store.assert_called()

    def test_refine_implementation(self):
        """Test refining an implementation."""
        # Create code with some issues to refine
        code_with_issues = """\
def calculate(a, b):
    # Redundant variable
    result = a + b
    return result
"""

        # Mock the memory manager's store method
        with patch.object(self.memory_manager, 'store') as mock_store:
            mock_store.return_value = "test_memory_id"

            # Call the method under test
            result = self.integration.refine_implementation(code_with_issues, "test_task")

            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertIn("original_code", result)
            self.assertIn("refined_code", result)
            self.assertIn("improvements", result)
            self.assertEqual(result["original_code"], code_with_issues)

            # Verify that memory was stored
            mock_store.assert_called()

    def test_retrospect_code_quality(self):
        """Test retrospecting on code quality."""
        # Create code with varying quality
        low_quality_code = """\
def f(x, y):
    z = x + y
    return z
"""

        # Mock the memory manager's store and search methods
        with patch.object(self.memory_manager, 'store') as mock_store:
            with patch.object(self.memory_manager, 'search') as mock_search:
                mock_store.return_value = "test_memory_id"
                mock_search.return_value = []  # No previous memories

                # Call the method under test
                result = self.integration.retrospect_code_quality(low_quality_code, "test_task")

                # Verify the result
                self.assertIsInstance(result, dict)
                self.assertIn("code", result)
                self.assertIn("quality_metrics", result)
                self.assertIn("improvement_suggestions", result)
                self.assertEqual(result["code"], low_quality_code)

                # Verify quality metrics
                metrics = result["quality_metrics"]
                self.assertIn("complexity", metrics)
                self.assertIn("readability", metrics)
                self.assertIn("maintainability", metrics)

                # Verify that memory was stored
                mock_store.assert_called()


if __name__ == "__main__":
    unittest.main()
