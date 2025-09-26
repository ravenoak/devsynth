import ast
import unittest
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_workflow_integration import (
    AstWorkflowIntegration,
    EvaluatedImplementation,
    EvaluationMetrics,
    ImplementationAlternative,
    ImplementationOptions,
    RefinementResult,
    RetrospectiveResult,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.methodology.base import Phase


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
    """Tests for the AstWorkflowIntegration component.

    ReqID: N/A"""

    def setUp(self):
        self.memory_manager = MemoryManager({"default": MockMemoryStore()})
        self.memory_manager.search = lambda query, limit=10: []
        self.integration = AstWorkflowIntegration(self.memory_manager)
        self.analyzer = CodeAnalyzer()
        self.sample_code = '"""Example module"""\n\ndef add(a, b):\n    """Add two numbers."""\n    return a + b\n\nclass Calculator:\n    """Performs calculations."""\n    def multiply(self, a, b):\n        """Multiply two numbers."""\n        return a * b\n'

    def test_complexity_and_readability_metrics_succeeds(self):
        """Test that complexity and readability metrics succeeds.

        ReqID: N/A"""
        analysis = self.analyzer.analyze_code(self.sample_code)
        complexity = self.integration._calculate_complexity(analysis)
        readability = self.integration._calculate_readability(analysis)
        maintainability = self.integration._calculate_maintainability(analysis)
        self.assertAlmostEqual(complexity, 0.65, places=2)
        self.assertAlmostEqual(readability, 1.0, places=2)
        self.assertAlmostEqual(maintainability, 0.86, places=2)

    def test_differentiate_selects_best_option_succeeds(self):
        """Test that differentiate selects best option succeeds.

        ReqID: N/A"""
        code_no_docs = "\ndef add(a, b):\n    return a + b\n\nclass Calculator:\n    def multiply(self, a, b):\n        return a * b\n"
        code_with_docs = self.sample_code
        options = [
            ImplementationAlternative(
                name="no_docs",
                description="",
                code=code_no_docs,
                analysis_id="analysis-no-docs",
            ),
            ImplementationAlternative(
                name="with_docs",
                description="",
                code=code_with_docs,
                analysis_id="analysis-with-docs",
            ),
        ]
        with patch.object(self.memory_manager, "store_with_edrr_phase") as store:
            store.return_value = "id1"
            selected = self.integration.differentiate_implementation_quality(
                options, "task"
            )
            store.assert_called()
            kwargs = store.call_args.kwargs
            assert kwargs["memory_type"] == MemoryType.CODE_ANALYSIS
            assert kwargs["edrr_phase"] == Phase.DIFFERENTIATE.value
        assert isinstance(selected, EvaluatedImplementation)
        self.assertEqual(selected.name, "with_docs")
        metrics = selected.metrics
        assert isinstance(metrics, EvaluationMetrics)
        for value in [metrics.complexity, metrics.readability, metrics.maintainability]:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_expand_implementation_options_succeeds(self):
        """Test expanding implementation options for a given code.

        ReqID: N/A"""
        with patch.object(self.memory_manager, "store") as mock_store:
            mock_store.return_value = "test_memory_id"
            result = self.integration.expand_implementation_options(
                self.sample_code, "test_task"
            )
            assert isinstance(result, ImplementationOptions)
            self.assertEqual(result.original, self.sample_code)
            self.assertGreaterEqual(len(result.alternatives), 1)
            mock_store.assert_called()

    def test_refine_implementation_succeeds(self):
        """Test refining an implementation.

        ReqID: N/A"""
        code_with_issues = "def calculate(a, b):\n    # Redundant variable\n    result = a + b\n    return result\n"
        with patch.object(self.memory_manager, "store") as mock_store:
            mock_store.return_value = "test_memory_id"
            result = self.integration.refine_implementation(
                code_with_issues, "test_task"
            )
            assert isinstance(result, RefinementResult)
            self.assertEqual(result.original_code, code_with_issues)
            self.assertIsInstance(result.improvements, list)
            mock_store.assert_called()

    def test_retrospect_code_quality_succeeds(self):
        """Test retrospecting on code quality.

        ReqID: N/A"""
        low_quality_code = "def f(x, y):\n    z = x + y\n    return z\n"
        with patch.object(self.memory_manager, "store") as mock_store:
            with patch.object(self.memory_manager, "search") as mock_search:
                mock_store.return_value = "test_memory_id"
                mock_search.return_value = []
                result = self.integration.retrospect_code_quality(
                    low_quality_code, "test_task"
                )
                assert isinstance(result, RetrospectiveResult)
                self.assertEqual(result.code, low_quality_code)
                self.assertIsInstance(result.quality_metrics, EvaluationMetrics)
                self.assertIsInstance(result.improvement_suggestions, list)
                mock_store.assert_called()


if __name__ == "__main__":
    unittest.main()
