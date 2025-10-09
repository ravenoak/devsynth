"""
Tests for the test execution benchmark script.

This module tests the functionality of scripts/benchmark_test_execution.py
to ensure it correctly measures test performance.
"""

import json

# Import the benchmark classes
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts"))

from benchmark_test_execution import TestExecutionBenchmark


@pytest.mark.fast
class TestTestExecutionBenchmark:
    """Test the TestExecutionBenchmark class."""

    def test_initialization(self):
        """Test benchmark initialization."""
        benchmark = TestExecutionBenchmark()

        assert "metadata" in benchmark.results
        assert "benchmarks" in benchmark.results
        assert "analysis" in benchmark.results
        assert benchmark.results["metadata"]["tool_version"] == "1.0.0"

    @patch("subprocess.run")
    def test_run_benchmark_success(self, mock_run):
        """Test successful benchmark execution."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===== 5 passed, 0 failed, 2 skipped in 1.23s ====="
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        benchmark = TestExecutionBenchmark()

        with patch("time.time", side_effect=[1000.0, 1001.23]):  # 1.23 second duration
            result = benchmark.run_benchmark("unit-tests", "fast", 2)

        assert result["target"] == "unit-tests"
        assert result["speed"] == "fast"
        assert result["workers"] == 2
        assert result["duration"] == 1.23
        assert result["success"] == True
        assert result["passed"] == 5
        assert result["skipped"] == 2
        assert result["test_count"] == 7
        assert result["tests_per_second"] > 0

    @patch("subprocess.run")
    def test_run_benchmark_timeout(self, mock_run):
        """Test benchmark timeout handling."""
        # Mock timeout
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired(["pytest"], 300)

        benchmark = TestExecutionBenchmark()
        result = benchmark.run_benchmark("unit-tests", "fast", 2, timeout=300)

        assert result["success"] == False
        assert result["error"] == "timeout"
        assert result["duration"] == 300
        assert result["test_count"] == 0

    @patch("subprocess.run")
    def test_run_benchmark_failure(self, mock_run):
        """Test benchmark failure handling."""
        # Mock subprocess failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "===== 2 passed, 3 failed in 2.45s ====="
        mock_result.stderr = "Some error"
        mock_run.return_value = mock_result

        benchmark = TestExecutionBenchmark()

        with patch("time.time", side_effect=[1000.0, 1002.45]):
            result = benchmark.run_benchmark("unit-tests", None, 1)

        assert result["success"] == False
        assert result["passed"] == 2
        assert result["failed"] == 3
        assert result["test_count"] == 5
        assert result["duration"] == 2.45

    def test_analyze_results_empty(self):
        """Test analysis with no results."""
        benchmark = TestExecutionBenchmark()
        benchmark.analyze_results()

        # Should not crash and should have empty analysis
        assert "analysis" in benchmark.results

    def test_analyze_results_with_data(self):
        """Test analysis with benchmark data."""
        benchmark = TestExecutionBenchmark()

        # Add sample benchmark data
        benchmark.results["benchmarks"] = [
            {
                "target": "unit-tests",
                "speed": None,
                "workers": 1,
                "duration": 10.0,
                "success": True,
                "test_count": 100,
                "tests_per_second": 10.0,
            },
            {
                "target": "unit-tests",
                "speed": None,
                "workers": 2,
                "duration": 6.0,
                "success": True,
                "test_count": 100,
                "tests_per_second": 16.67,
            },
            {
                "target": "unit-tests",
                "speed": None,
                "workers": 4,
                "duration": 35.0,  # Bottleneck
                "success": True,
                "test_count": 100,
                "tests_per_second": 2.86,
            },
        ]

        benchmark.analyze_results()

        analysis = benchmark.results["analysis"]

        # Check speedup analysis
        assert "speedup_analysis" in analysis
        assert "unit-tests" in analysis["speedup_analysis"]

        speedups = analysis["speedup_analysis"]["unit-tests"]["speedups"]
        assert 2 in speedups
        assert speedups[2]["speedup"] == pytest.approx(10.0 / 6.0, rel=0.1)

        # Check bottlenecks
        assert "bottlenecks" in analysis
        assert len(analysis["bottlenecks"]) == 1
        assert analysis["bottlenecks"][0]["duration"] == 35.0

        # Check statistics
        stats = analysis["statistics"]
        assert stats["total_benchmarks"] == 3
        assert stats["successful_benchmarks"] == 3
        assert stats["average_duration"] == pytest.approx(
            (10.0 + 6.0 + 35.0) / 3, rel=0.1
        )

    def test_generates_recommendations(self):
        """Test recommendation generation."""
        benchmark = TestExecutionBenchmark()

        # Test data with poor parallelization
        speedup_analysis = {
            "unit-tests": {
                "speedups": {
                    2: {"speedup": 1.1, "efficiency": 0.55},
                    4: {"speedup": 1.2, "efficiency": 0.30},
                }
            }
        }

        bottlenecks = [
            {"target": "integration-tests", "speed": "slow", "duration": 45.0}
        ]

        recommendations = benchmark._generate_recommendations(
            speedup_analysis, bottlenecks
        )

        assert len(recommendations) >= 2
        assert any("Poor parallelization" in rec for rec in recommendations)
        assert any("Found 1 slow test executions" in rec for rec in recommendations)


@pytest.mark.fast
def test_main_function_help():
    """Test that main function provides help."""
    from benchmark_test_execution import main

    with patch("sys.argv", ["benchmark_test_execution.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


@pytest.mark.fast
def test_main_function_invalid_workers():
    """Test main function with invalid worker specification."""
    from benchmark_test_execution import main

    with patch("sys.argv", ["benchmark_test_execution.py", "--workers", "invalid"]):
        result = main()
        assert result == 1


@pytest.mark.fast
def test_integration_benchmark_workflow(tmp_path):
    """Test complete benchmark workflow."""
    # This test verifies the overall flow without running actual pytest
    benchmark = TestExecutionBenchmark()

    # Mock the run_benchmark method to avoid actual test execution
    with patch.object(benchmark, "run_benchmark") as mock_run:
        mock_run.return_value = {
            "target": "unit-tests",
            "speed": None,
            "workers": 2,
            "duration": 5.0,
            "success": True,
            "test_count": 50,
            "tests_per_second": 10.0,
        }

        benchmark.run_comprehensive_benchmark(["unit-tests"], [1, 2])

        # Should have called run_benchmark for each combination
        assert mock_run.call_count >= 2
        assert len(benchmark.results["benchmarks"]) >= 2

    # Test analysis
    benchmark.analyze_results()
    assert "analysis" in benchmark.results
    assert "statistics" in benchmark.results["analysis"]
