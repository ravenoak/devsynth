"""
Tests for the test dependency analyzer script.

This module tests the functionality of scripts/analyze_test_dependencies.py
to ensure it correctly identifies test dependencies and isolation markers.
"""

import ast
import json

# Import the analyzer classes
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts"))

from analyze_test_dependencies import (
    TestDependencyAnalyzer,
    TestFileAnalyzer,
    generate_recommendations,
)


@pytest.mark.fast
class TestTestDependencyAnalyzer:
    """Test the TestDependencyAnalyzer AST visitor."""

    def test_detects_file_operations(self):
        """Test detection of file system operations."""
        code = """
import os
from pathlib import Path

def test_file_ops():
    with open('test.txt', 'w') as f:
        f.write('test')
    Path('test').mkdir()
    os.makedirs('dir')
"""
        tree = ast.parse(code)
        analyzer = TestDependencyAnalyzer()
        analyzer.visit(tree)

        assert "open" in analyzer.file_operations
        assert "Path" in analyzer.imports
        assert "os" in analyzer.imports

    def test_detects_network_calls(self):
        """Test detection of network operations."""
        code = """
import requests
import socket

def test_network():
    response = requests.get('http://example.com')
    sock = socket.socket()
"""
        tree = ast.parse(code)
        analyzer = TestDependencyAnalyzer()
        analyzer.visit(tree)

        assert any("requests" in call for call in analyzer.network_calls)
        assert "requests" in analyzer.imports
        assert "socket" in analyzer.imports

    def test_detects_global_state(self):
        """Test detection of global state modifications."""
        code = """
import os
from unittest.mock import patch

def test_global_state():
    os.environ['TEST'] = 'value'
    with patch('sys.modules'):
        pass
"""
        tree = ast.parse(code)
        analyzer = TestDependencyAnalyzer()
        analyzer.visit(tree)

        assert "os" in analyzer.imports
        assert "unittest.mock.patch" in analyzer.imports

    def test_detects_fixture_usage(self):
        """Test detection of pytest fixtures."""
        code = """
def test_with_fixtures(tmp_path, tmpdir_factory, monkeypatch):
    tmp_path.mkdir('test')
    tmpdir_factory.mktemp('temp')
    monkeypatch.setenv('TEST', 'value')
"""
        tree = ast.parse(code)
        analyzer = TestDependencyAnalyzer()
        analyzer.visit(tree)

        assert "tmp_path" in analyzer.fixture_usage
        assert "fixture:tmp_path" in analyzer.file_operations


@pytest.mark.fast
class TestTestFileAnalyzer:
    """Test the TestFileAnalyzer class."""

    def test_analyzes_simple_test_file(self, tmp_path):
        """Test analysis of a simple test file."""
        test_file = tmp_path / "test_simple.py"
        test_file.write_text(
            """
import pytest

@pytest.mark.fast
def test_simple():
    assert True

def test_another():
    assert 1 + 1 == 2
"""
        )

        analyzer = TestFileAnalyzer()
        result = analyzer.analyze_file(test_file)

        assert result["test_count"] == 2
        assert "test_simple" in result["test_functions"]
        assert "test_another" in result["test_functions"]
        assert not result["has_isolation_marker"]
        assert result["safe_for_parallel"]

    def test_analyzes_file_with_isolation_marker(self, tmp_path):
        """Test analysis of file with isolation marker."""
        test_file = tmp_path / "test_isolated.py"
        test_file.write_text(
            """
import pytest
import os

@pytest.mark.isolation
@pytest.mark.fast
def test_with_file_ops():
    with open('test.txt', 'w') as f:
        f.write('test')
    os.makedirs('test_dir')
"""
        )

        analyzer = TestFileAnalyzer()
        result = analyzer.analyze_file(test_file)

        assert result["has_isolation_marker"]
        assert not result["safe_for_parallel"]
        assert result["risk_score"] > 0
        assert "open" in result["dependencies"]["file_operations"]

    def test_handles_syntax_errors(self, tmp_path):
        """Test handling of files with syntax errors."""
        test_file = tmp_path / "test_broken.py"
        test_file.write_text(
            """
def test_broken(
    # Missing closing parenthesis
    assert True
"""
        )

        analyzer = TestFileAnalyzer()
        result = analyzer.analyze_file(test_file)

        assert "error" in result
        assert result.get("analyzable", True) == False


@pytest.mark.fast
class TestRecommendationGeneration:
    """Test the recommendation generation logic."""

    def test_generates_recommendations(self):
        """Test generation of removal recommendations."""
        analysis_results = [
            {
                "relative_path": "tests/test_safe.py",
                "has_isolation_marker": True,
                "safe_for_parallel": True,
                "risk_score": 0,
            },
            {
                "relative_path": "tests/test_risky.py",
                "has_isolation_marker": True,
                "safe_for_parallel": False,
                "risk_score": 10,
            },
            {
                "relative_path": "tests/test_no_marker.py",
                "has_isolation_marker": False,
                "safe_for_parallel": True,
                "risk_score": 0,
            },
        ]

        recommendations = generate_recommendations(analysis_results)

        assert recommendations["summary"]["total_test_files"] == 3
        assert recommendations["summary"]["files_with_isolation_markers"] == 2
        assert recommendations["summary"]["safe_for_removal"] == 1

        assert (
            "tests/test_safe.py"
            in recommendations["recommendations"]["immediate_removal"]
        )
        assert (
            "tests/test_risky.py"
            in recommendations["recommendations"]["keep_isolation"]
        )

    def test_calculates_percentages(self):
        """Test percentage calculations in recommendations."""
        analysis_results = [
            {"has_isolation_marker": True, "safe_for_parallel": True, "risk_score": 0},
            {"has_isolation_marker": True, "safe_for_parallel": True, "risk_score": 1},
            {
                "has_isolation_marker": True,
                "safe_for_parallel": False,
                "risk_score": 10,
            },
            {
                "has_isolation_marker": True,
                "safe_for_parallel": False,
                "risk_score": 15,
            },
        ]

        recommendations = generate_recommendations(analysis_results)

        assert recommendations["summary"]["removal_percentage"] == 50.0


@pytest.mark.fast
class TestIntegration:
    """Integration tests for the analyzer."""

    def test_end_to_end_analysis(self, tmp_path):
        """Test complete analysis workflow."""
        # Create test directory structure
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Create sample test files
        (test_dir / "test_safe.py").write_text(
            """
import pytest

@pytest.mark.fast
def test_safe():
    assert True
"""
        )

        (test_dir / "test_with_isolation.py").write_text(
            """
import pytest
import os

@pytest.mark.isolation
@pytest.mark.fast
def test_file_ops():
    os.makedirs('test', exist_ok=True)
"""
        )

        # Run analysis
        from analyze_test_dependencies import (
            TestFileAnalyzer,
            find_test_files,
            generate_recommendations,
        )

        test_files = find_test_files(test_dir)
        assert len(test_files) == 2

        analyzer = TestFileAnalyzer()
        results = []
        for test_file in test_files:
            results.append(analyzer.analyze_file(test_file))

        recommendations = generate_recommendations(results)

        assert recommendations["summary"]["total_test_files"] == 2
        assert recommendations["summary"]["files_with_isolation_markers"] == 1


@pytest.mark.fast
def test_main_function_help():
    """Test that main function provides help."""
    from analyze_test_dependencies import main

    with patch("sys.argv", ["analyze_test_dependencies.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        # Help should exit with code 0
        assert exc_info.value.code == 0


@pytest.mark.fast
def test_main_function_missing_test_dir():
    """Test main function with missing test directory."""
    from analyze_test_dependencies import main

    with patch(
        "sys.argv", ["analyze_test_dependencies.py", "--test-dir", "nonexistent"]
    ):
        result = main()
        assert result == 1  # Should return error code
