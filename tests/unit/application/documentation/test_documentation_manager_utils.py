import unittest
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.memory.memory_manager import MemoryManager


class TestDocumentationManagerUtils(unittest.TestCase):
    """Test case for the utility functions in the DocumentationManager class.

    ReqID: N/A"""

    def setUp(self):
        """Set up the test case."""
        self.memory_manager = MagicMock(spec=MemoryManager)
        self.documentation_manager = DocumentationManager(self.memory_manager)
        self.documentation_manager.query_documentation = MagicMock()

    @pytest.mark.medium
    def test_get_function_documentation_succeeds(self):
        """Test the get_function_documentation method.

        ReqID: N/A"""
        mock_results = [
            {
                "content": "Documentation for function pandas.DataFrame.groupby",
                "type": "function",
                "library": "pandas",
                "version": "1.4.2",
                "relevance": 0.95,
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        function_name = "pandas.DataFrame.groupby"
        results = self.documentation_manager.get_function_documentation(function_name)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "function")
        self.assertEqual(
            results[0]["content"], "Documentation for function pandas.DataFrame.groupby"
        )
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["pandas"])

    @pytest.mark.medium
    def test_get_class_documentation_succeeds(self):
        """Test the get_class_documentation method.

        ReqID: N/A"""
        mock_results = [
            {
                "content": "Documentation for class sklearn.ensemble.RandomForestClassifier",
                "type": "class",
                "library": "sklearn",
                "version": "1.1.2",
                "relevance": 0.95,
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        class_name = "sklearn.ensemble.RandomForestClassifier"
        results = self.documentation_manager.get_class_documentation(class_name)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "class")
        self.assertEqual(
            results[0]["content"],
            "Documentation for class sklearn.ensemble.RandomForestClassifier",
        )
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"class:{class_name}")
        self.assertEqual(kwargs.get("libraries"), ["sklearn"])

    @pytest.mark.medium
    def test_get_usage_examples_succeeds(self):
        """Test the get_usage_examples method.

        ReqID: N/A"""
        mock_results = [
            {
                "content": "Example 1 for numpy.array",
                "type": "example",
                "library": "numpy",
                "version": "1.22.4",
                "relevance": 0.95,
            },
            {
                "content": "Example 2 for numpy.array",
                "type": "example",
                "library": "numpy",
                "version": "1.22.4",
                "relevance": 0.85,
            },
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        item_name = "numpy.array"
        results = self.documentation_manager.get_usage_examples(item_name)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["type"], "example")
        self.assertEqual(results[0]["content"], "Example 1 for numpy.array")
        self.assertEqual(results[1]["type"], "example")
        self.assertEqual(results[1]["content"], "Example 2 for numpy.array")
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"example:{item_name}")
        self.assertEqual(kwargs.get("libraries"), ["numpy"])

    @pytest.mark.medium
    def test_get_api_compatibility_succeeds(self):
        """Test the get_api_compatibility method.

        ReqID: N/A"""
        self.documentation_manager.repository.get_documentation = MagicMock()
        self.documentation_manager.repository.get_documentation.side_effect = (
            lambda lib, ver: {
                "pandas": {
                    "1.3.0": {"parameters": ["param1", "param2"]},
                    "1.4.0": {
                        "parameters": ["param1", "param2", "param3"],
                        "changes": ["Added param3"],
                    },
                    "1.4.2": {
                        "parameters": ["param1", "param2", "param3"],
                        "deprecated": ["param2 will be deprecated in 1.5.0"],
                    },
                }
            }
            .get(lib, {})
            .get(ver, {})
        )
        function_name = "pandas.read_csv"
        versions = ["1.3.0", "1.4.0", "1.4.2"]
        results = self.documentation_manager.get_api_compatibility(
            function_name, versions
        )
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["versions"]), 3)
        self.assertEqual(results["versions"][0]["version"], "1.3.0")
        self.assertEqual(results["versions"][1]["version"], "1.4.0")
        self.assertEqual(results["versions"][2]["version"], "1.4.2")
        self.assertIn("changes", results["versions"][1])
        self.assertIn("deprecated", results["versions"][2])
        self.assertEqual(
            self.documentation_manager.repository.get_documentation.call_count, 3
        )

    @pytest.mark.medium
    def test_get_related_functions_succeeds(self):
        """Test the get_related_functions method.

        ReqID: N/A"""
        mock_results = [
            {
                "content": "Documentation for function scipy.stats.ttest_ind",
                "type": "function",
                "library": "scipy",
                "version": "1.8.1",
                "relevance": 0.95,
                "related": ["scipy.stats.ttest_rel", "scipy.stats.ttest_1samp"],
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        self.documentation_manager.repository.get_documentation = MagicMock()
        self.documentation_manager.repository.get_documentation.side_effect = lambda lib, ver, func=None: (
            {
                "scipy.stats.ttest_rel": {
                    "description": "Calculates the T-test for the means of two related samples of scores"
                },
                "scipy.stats.ttest_1samp": {
                    "description": "Calculates the T-test for the mean of ONE group of scores"
                },
            }.get(func, {})
            if func
            else {}
        )
        function_name = "scipy.stats.ttest_ind"
        results = self.documentation_manager.get_related_functions(function_name)
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["related_functions"]), 2)
        self.assertEqual(
            results["related_functions"][0]["name"], "scipy.stats.ttest_rel"
        )
        self.assertEqual(
            results["related_functions"][1]["name"], "scipy.stats.ttest_1samp"
        )
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["scipy"])

    @pytest.mark.medium
    def test_get_usage_patterns_succeeds(self):
        """Test the get_usage_patterns method.

        ReqID: N/A"""
        mock_results = [
            {
                "content": "Documentation for function sklearn.model_selection.train_test_split",
                "type": "function",
                "library": "sklearn",
                "version": "1.1.2",
                "relevance": 0.95,
                "usage_patterns": [
                    {
                        "pattern": "Basic usage",
                        "code": "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)",
                    },
                    {
                        "pattern": "With stratification",
                        "code": "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)",
                    },
                ],
                "best_practices": [
                    "Always set random_state for reproducibility",
                    "Use stratify for imbalanced datasets",
                ],
                "common_params": {
                    "test_size": "0.2 or 0.25 are common values",
                    "random_state": "Any integer for reproducibility",
                    "stratify": "Usually set to target variable y for classification",
                },
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        function_name = "sklearn.model_selection.train_test_split"
        results = self.documentation_manager.get_usage_patterns(function_name)
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["usage_patterns"]), 2)
        self.assertEqual(results["usage_patterns"][0]["pattern"], "Basic usage")
        self.assertEqual(results["usage_patterns"][1]["pattern"], "With stratification")
        self.assertEqual(len(results["best_practices"]), 2)
        self.assertEqual(len(results["common_params"]), 3)
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["sklearn"])

    @pytest.mark.medium
    def test_offline_fetch_uses_cache_returns_expected_result(self):
        """Ensure offline fetch returns cached documentation.

        ReqID: N/A"""
        self.documentation_manager.repository.has_documentation = MagicMock(
            return_value=True
        )
        self.documentation_manager.repository.get_documentation = MagicMock(
            return_value={"stored_at": "now"}
        )
        self.documentation_manager.fetcher.fetch_documentation = MagicMock()
        result = self.documentation_manager.fetch_documentation(
            "foo", "1.0", offline=True
        )
        self.assertEqual(result["source"], "cache")
        self.documentation_manager.fetcher.fetch_documentation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
