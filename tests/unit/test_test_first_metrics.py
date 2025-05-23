import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Import the module we'll be testing
# This will be implemented later
import sys
sys.path.append('scripts')
from test_first_metrics import (
    get_commit_history,
    analyze_commit,
    calculate_metrics,
    generate_metrics_report,
    main
)

class TestTestFirstMetrics(unittest.TestCase):
    """Test the test_first_metrics.py script."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metrics_file = os.path.join(self.temp_dir.name, "test_first_metrics.json")

        # Sample commit data
        self.sample_commits = [
            {
                "hash": "abc123",
                "author": "Test Author",
                "date": "2025-05-25",
                "message": "Add new feature",
                "files": [
                    {"path": "src/devsynth/feature.py", "status": "A"},
                    {"path": "tests/unit/test_feature.py", "status": "A"}
                ]
            },
            {
                "hash": "def456",
                "author": "Test Author",
                "date": "2025-05-26",
                "message": "Fix bug",
                "files": [
                    {"path": "src/devsynth/module.py", "status": "M"},
                    {"path": "tests/unit/test_module.py", "status": "M"}
                ]
            },
            {
                "hash": "ghi789",
                "author": "Test Author",
                "date": "2025-05-27",
                "message": "Implement without test",
                "files": [
                    {"path": "src/devsynth/no_test.py", "status": "A"}
                ]
            }
        ]

        # Expected metrics
        self.expected_metrics = {
            "total_commits": 3,
            "test_first_commits": 2,
            "implementation_first_commits": 1,
            "test_first_percentage": 66.67,
            "by_author": {
                "Test Author": {
                    "total_commits": 3,
                    "test_first_commits": 2,
                    "implementation_first_commits": 1,
                    "test_first_percentage": 66.67
                }
            },
            "by_date": {
                "2025-05-25": {
                    "total_commits": 1,
                    "test_first_commits": 1,
                    "implementation_first_commits": 0,
                    "test_first_percentage": 100.0
                },
                "2025-05-26": {
                    "total_commits": 1,
                    "test_first_commits": 1,
                    "implementation_first_commits": 0,
                    "test_first_percentage": 100.0
                },
                "2025-05-27": {
                    "total_commits": 1,
                    "test_first_commits": 0,
                    "implementation_first_commits": 1,
                    "test_first_percentage": 0.0
                }
            }
        }

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    @patch('test_first_metrics.subprocess.run')
    def test_get_commit_history(self, mock_run):
        """Test getting commit history from git."""
        # Mock the subprocess.run function to return sample data
        mock_process = MagicMock()
        mock_process.stdout = "abc123|Test Author|2025-05-25|Add new feature"
        mock_run.return_value = mock_process

        # Call the function
        commits = get_commit_history(days=7)

        # Verify the result
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["hash"], "abc123")
        self.assertEqual(commits[0]["author"], "Test Author")

        # Verify that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("git", args)
        self.assertIn("log", args)
        self.assertIn("--pretty=format:%H|%an|%ad|%s", args)
        self.assertIn("--date=short", args)
        self.assertIn(f"--since={7} days ago", args)

    @patch('test_first_metrics.subprocess.run')
    def test_analyze_commit(self, mock_run):
        """Test analyzing a commit to determine if it follows test-first development."""
        # Mock the subprocess.run function to return sample data
        mock_process = MagicMock()
        mock_process.stdout = "\n".join([
            "M\tsrc/devsynth/feature.py",
            "A\ttests/unit/test_feature.py"
        ])
        mock_run.return_value = mock_process

        # Call the function
        commit = {
            "hash": "abc123",
            "author": "Test Author",
            "date": "2025-05-25",
            "message": "Add new feature"
        }
        result = analyze_commit(commit)

        # Verify the result
        self.assertEqual(result["hash"], "abc123")
        self.assertEqual(len(result["files"]), 2)
        self.assertEqual(result["files"][0]["path"], "src/devsynth/feature.py")
        self.assertEqual(result["files"][0]["status"], "M")
        self.assertEqual(result["files"][1]["path"], "tests/unit/test_feature.py")
        self.assertEqual(result["files"][1]["status"], "A")

        # Verify that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("git", args)
        self.assertIn("show", args)
        self.assertIn("--name-status", args)
        self.assertIn("--format=", args)
        self.assertIn("abc123", args)

    def test_calculate_metrics(self):
        """Test calculating metrics from commit data."""
        # Call the function
        metrics = calculate_metrics(self.sample_commits)

        # Verify the result
        self.assertEqual(metrics["total_commits"], 3)
        self.assertEqual(metrics["test_first_commits"], 2)
        self.assertEqual(metrics["implementation_first_commits"], 1)
        self.assertAlmostEqual(metrics["test_first_percentage"], 66.67, places=2)

        # Check author metrics
        self.assertEqual(metrics["by_author"]["Test Author"]["total_commits"], 3)
        self.assertEqual(metrics["by_author"]["Test Author"]["test_first_commits"], 2)
        self.assertEqual(metrics["by_author"]["Test Author"]["implementation_first_commits"], 1)
        self.assertAlmostEqual(metrics["by_author"]["Test Author"]["test_first_percentage"], 66.67, places=2)

        # Check date metrics
        self.assertEqual(metrics["by_date"]["2025-05-25"]["total_commits"], 1)
        self.assertEqual(metrics["by_date"]["2025-05-25"]["test_first_commits"], 1)
        self.assertEqual(metrics["by_date"]["2025-05-25"]["implementation_first_commits"], 0)
        self.assertEqual(metrics["by_date"]["2025-05-25"]["test_first_percentage"], 100.0)

    def test_generate_metrics_report(self):
        """Test generating a metrics report."""
        # Call the function
        report = generate_metrics_report(self.expected_metrics)

        # Verify the result
        self.assertIn("Test-First Development Metrics", report)
        self.assertIn("Total commits: 3", report)
        self.assertIn("Test-first commits: 2", report)
        self.assertIn("Implementation-first commits: 1", report)
        self.assertIn("Test-first percentage: 66.67%", report)
        self.assertIn("Metrics by Author", report)
        self.assertIn("Test Author", report)
        self.assertIn("Metrics by Date", report)
        self.assertIn("2025-05-25", report)

    @patch('test_first_metrics.get_commit_history')
    @patch('test_first_metrics.analyze_commit')
    @patch('test_first_metrics.calculate_metrics')
    @patch('test_first_metrics.generate_metrics_report')
    @patch('builtins.print')
    def test_main(self, mock_print, mock_generate_report, mock_calculate_metrics, 
                 mock_analyze_commit, mock_get_history):
        """Test the main function."""
        # Mock the functions
        mock_get_history.return_value = self.sample_commits
        mock_analyze_commit.side_effect = lambda commit: commit
        mock_calculate_metrics.return_value = self.expected_metrics
        mock_generate_report.return_value = "Test report"

        # Call the function
        main(days=7, output_file=self.metrics_file)

        # Verify that the functions were called with the correct arguments
        mock_get_history.assert_called_once_with(days=7)
        self.assertEqual(mock_analyze_commit.call_count, 3)
        mock_calculate_metrics.assert_called_once()
        mock_generate_report.assert_called_once_with(self.expected_metrics)
        mock_print.assert_any_call("Test report")

        # Verify that the metrics were saved to the file
        self.assertTrue(os.path.exists(self.metrics_file))
        with open(self.metrics_file, 'r') as f:
            saved_metrics = json.load(f)
        self.assertEqual(saved_metrics, self.expected_metrics)

if __name__ == '__main__':
    unittest.main()
