import unittest
from unittest.mock import MagicMock, patch

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.documentation.documentation_manager import DocumentationManager

class TestDocumentationManagerUtils(unittest.TestCase):
    """Test case for the utility functions in the DocumentationManager class."""

    def setUp(self):
        """Set up the test case."""
        # Mock the memory manager
        self.memory_manager = MagicMock(spec=MemoryManager)
        
        # Create the documentation manager with the mock memory manager
        self.documentation_manager = DocumentationManager(self.memory_manager)
        
        # Mock the query_documentation method to return test data
        self.documentation_manager.query_documentation = MagicMock()

    def test_get_function_documentation(self):
        """Test the get_function_documentation method."""
        # Set up the mock to return test data
        mock_results = [
            {
                "content": "Documentation for function pandas.DataFrame.groupby",
                "type": "function",
                "library": "pandas",
                "version": "1.4.2",
                "relevance": 0.95
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        
        # Call the method
        function_name = "pandas.DataFrame.groupby"
        results = self.documentation_manager.get_function_documentation(function_name)
        
        # Verify the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "function")
        self.assertEqual(results[0]["content"], "Documentation for function pandas.DataFrame.groupby")
        
        # Verify that query_documentation was called with the correct parameters
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["pandas"])

    def test_get_class_documentation(self):
        """Test the get_class_documentation method."""
        # Set up the mock to return test data
        mock_results = [
            {
                "content": "Documentation for class sklearn.ensemble.RandomForestClassifier",
                "type": "class",
                "library": "sklearn",
                "version": "1.1.2",
                "relevance": 0.95
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        
        # Call the method
        class_name = "sklearn.ensemble.RandomForestClassifier"
        results = self.documentation_manager.get_class_documentation(class_name)
        
        # Verify the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "class")
        self.assertEqual(results[0]["content"], "Documentation for class sklearn.ensemble.RandomForestClassifier")
        
        # Verify that query_documentation was called with the correct parameters
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"class:{class_name}")
        self.assertEqual(kwargs.get("libraries"), ["sklearn"])

    def test_get_usage_examples(self):
        """Test the get_usage_examples method."""
        # Set up the mock to return test data
        mock_results = [
            {
                "content": "Example 1 for numpy.array",
                "type": "example",
                "library": "numpy",
                "version": "1.22.4",
                "relevance": 0.95
            },
            {
                "content": "Example 2 for numpy.array",
                "type": "example",
                "library": "numpy",
                "version": "1.22.4",
                "relevance": 0.85
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        
        # Call the method
        item_name = "numpy.array"
        results = self.documentation_manager.get_usage_examples(item_name)
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["type"], "example")
        self.assertEqual(results[0]["content"], "Example 1 for numpy.array")
        self.assertEqual(results[1]["type"], "example")
        self.assertEqual(results[1]["content"], "Example 2 for numpy.array")
        
        # Verify that query_documentation was called with the correct parameters
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"example:{item_name}")
        self.assertEqual(kwargs.get("libraries"), ["numpy"])

    def test_get_api_compatibility(self):
        """Test the get_api_compatibility method."""
        # Mock the repository.get_documentation method to return test data
        self.documentation_manager.repository.get_documentation = MagicMock()
        self.documentation_manager.repository.get_documentation.side_effect = lambda lib, ver: {
            "pandas": {
                "1.3.0": {"parameters": ["param1", "param2"]},
                "1.4.0": {"parameters": ["param1", "param2", "param3"], "changes": ["Added param3"]},
                "1.4.2": {"parameters": ["param1", "param2", "param3"], "deprecated": ["param2 will be deprecated in 1.5.0"]}
            }
        }.get(lib, {}).get(ver, {})
        
        # Call the method
        function_name = "pandas.read_csv"
        versions = ["1.3.0", "1.4.0", "1.4.2"]
        results = self.documentation_manager.get_api_compatibility(function_name, versions)
        
        # Verify the results
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["versions"]), 3)
        self.assertEqual(results["versions"][0]["version"], "1.3.0")
        self.assertEqual(results["versions"][1]["version"], "1.4.0")
        self.assertEqual(results["versions"][2]["version"], "1.4.2")
        self.assertIn("changes", results["versions"][1])
        self.assertIn("deprecated", results["versions"][2])
        
        # Verify that get_documentation was called for each version
        self.assertEqual(self.documentation_manager.repository.get_documentation.call_count, 3)

    def test_get_related_functions(self):
        """Test the get_related_functions method."""
        # Set up the mock to return test data
        mock_results = [
            {
                "content": "Documentation for function scipy.stats.ttest_ind",
                "type": "function",
                "library": "scipy",
                "version": "1.8.1",
                "relevance": 0.95,
                "related": ["scipy.stats.ttest_rel", "scipy.stats.ttest_1samp"]
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        
        # Mock the repository.get_documentation method to return test data for related functions
        self.documentation_manager.repository.get_documentation = MagicMock()
        self.documentation_manager.repository.get_documentation.side_effect = lambda lib, ver, func=None: {
            "scipy.stats.ttest_rel": {"description": "Calculates the T-test for the means of two related samples of scores"},
            "scipy.stats.ttest_1samp": {"description": "Calculates the T-test for the mean of ONE group of scores"}
        }.get(func, {}) if func else {}
        
        # Call the method
        function_name = "scipy.stats.ttest_ind"
        results = self.documentation_manager.get_related_functions(function_name)
        
        # Verify the results
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["related_functions"]), 2)
        self.assertEqual(results["related_functions"][0]["name"], "scipy.stats.ttest_rel")
        self.assertEqual(results["related_functions"][1]["name"], "scipy.stats.ttest_1samp")
        
        # Verify that query_documentation was called with the correct parameters
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["scipy"])

    def test_get_usage_patterns(self):
        """Test the get_usage_patterns method."""
        # Set up the mock to return test data
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
                        "code": "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)"
                    },
                    {
                        "pattern": "With stratification",
                        "code": "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)"
                    }
                ],
                "best_practices": [
                    "Always set random_state for reproducibility",
                    "Use stratify for imbalanced datasets"
                ],
                "common_params": {
                    "test_size": "0.2 or 0.25 are common values",
                    "random_state": "Any integer for reproducibility",
                    "stratify": "Usually set to target variable y for classification"
                }
            }
        ]
        self.documentation_manager.query_documentation.return_value = mock_results
        
        # Call the method
        function_name = "sklearn.model_selection.train_test_split"
        results = self.documentation_manager.get_usage_patterns(function_name)
        
        # Verify the results
        self.assertEqual(results["function"], function_name)
        self.assertEqual(len(results["usage_patterns"]), 2)
        self.assertEqual(results["usage_patterns"][0]["pattern"], "Basic usage")
        self.assertEqual(results["usage_patterns"][1]["pattern"], "With stratification")
        self.assertEqual(len(results["best_practices"]), 2)
        self.assertEqual(len(results["common_params"]), 3)
        
        # Verify that query_documentation was called with the correct parameters
        self.documentation_manager.query_documentation.assert_called_once()
        args, kwargs = self.documentation_manager.query_documentation.call_args
        self.assertEqual(args[0], f"function:{function_name}")
        self.assertEqual(kwargs.get("libraries"), ["sklearn"])

if __name__ == '__main__':
    unittest.main()
