"""
Tests for the quality report generator script.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from scripts.generate_quality_report import (
    calculate_overall_quality_score,
    generate_quality_recommendations,
    get_coverage_metrics,
    get_property_test_metrics,
)


@pytest.mark.fast
class TestQualityReportGenerator:
    """Test the quality report generator functionality."""

    def test_get_coverage_metrics_with_file(self):
        """Test coverage metrics extraction from coverage.json."""
        mock_coverage_data = {
            "totals": {
                "percent_covered": 85.5,
                "percent_covered_display": "85.5",
                "num_statements": 1000,
                "missing_lines": 145,
                "covered_lines": 855,
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "builtins.open", mock_open(read_data=json.dumps(mock_coverage_data))
            ):
                metrics = get_coverage_metrics()

        assert metrics["line_coverage"] == 85.5
        assert metrics["num_statements"] == 1000
        assert metrics["covered_lines"] == 855

    def test_get_coverage_metrics_without_file(self):
        """Test coverage metrics when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            metrics = get_coverage_metrics()

        assert metrics["line_coverage"] == 0
        assert metrics["num_statements"] == 0
        assert metrics["covered_lines"] == 0

    def test_get_property_test_metrics(self):
        """Test property test metrics collection."""
        mock_files = [Path("test_prop1.py"), Path("test_prop2.py")]
        mock_content = """
        @given(st.integers())
        def test_something(x):
            pass
            
        @given(st.text())
        def test_another(s):
            pass
        """

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.glob", return_value=mock_files):
                with patch("builtins.open", mock_open(read_data=mock_content)):
                    metrics = get_property_test_metrics()

        assert metrics["total_property_tests"] == 4  # 2 files * 2 @given each
        assert metrics["property_test_files"] == 2
        assert metrics["enabled"] is False  # Default env var

    def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation."""
        metrics = {
            "coverage": {"line_coverage": 85.0},
            "mutation": {"mutation_score": 75.0},
            "property": {"total_property_tests": 10, "enabled": True},
            "organization": {"marker_compliance": 95.0},
            "performance": {"parallel_speedup": 4.0},
        }

        score = calculate_overall_quality_score(metrics)

        # Should be weighted average of all components
        assert 70 <= score <= 90  # Reasonable range
        assert isinstance(score, float)

    def test_generate_quality_recommendations(self):
        """Test quality improvement recommendations generation."""
        metrics = {
            "coverage": {"line_coverage": 70.0},  # Below 80%
            "mutation": {"skipped": True},
            "property": {"total_property_tests": 0},
            "organization": {"marker_compliance": 85.0},  # Below 95%
            "performance": {"parallel_speedup": 2.0},  # Below 3x
        }

        recommendations = generate_quality_recommendations(metrics)

        # Should have recommendations for each area
        assert len(recommendations) >= 4
        assert any("coverage" in rec.lower() for rec in recommendations)
        assert any("mutation" in rec.lower() for rec in recommendations)
        assert any("property" in rec.lower() for rec in recommendations)

    def test_quality_score_with_missing_mutation(self):
        """Test quality score calculation when mutation testing is skipped."""
        metrics = {
            "coverage": {"line_coverage": 90.0},
            "mutation": {"mutation_score": None},  # Skipped
            "property": {"total_property_tests": 5, "enabled": False},
            "organization": {"marker_compliance": 100.0},
            "performance": {"parallel_speedup": 3.5},
        }

        score = calculate_overall_quality_score(metrics)

        # Should handle None mutation score gracefully
        assert 60 <= score <= 85
        assert isinstance(score, float)

    def test_recommendations_for_good_metrics(self):
        """Test recommendations when metrics are already good."""
        metrics = {
            "coverage": {"line_coverage": 95.0},
            "mutation": {"skipped": False, "mutation_score": 85.0},
            "property": {"total_property_tests": 20, "enabled": True},
            "organization": {"marker_compliance": 98.0},
            "performance": {"parallel_speedup": 5.0},
        }

        recommendations = generate_quality_recommendations(metrics)

        # Should have fewer recommendations for good metrics
        assert len(recommendations) <= 2
        # Should have positive reinforcement
        assert any("excellent" in rec.lower() for rec in recommendations)


@pytest.mark.fast
def test_html_generation():
    """Test HTML dashboard generation."""
    from scripts.generate_quality_report import generate_html_dashboard

    metrics = {
        "overall_score": 82.5,
        "coverage": {
            "line_coverage": 85.0,
            "covered_lines": 850,
            "num_statements": 1000,
        },
        "mutation": {
            "skipped": False,
            "mutation_score": 75.0,
            "killed_mutations": 18,
            "total_mutations": 24,
        },
        "property": {
            "total_property_tests": 12,
            "property_test_files": 4,
            "enabled": True,
        },
        "organization": {"marker_compliance": 95.0, "total_tests": 500},
        "performance": {
            "parallel_speedup": 4.2,
            "worker_count": 8,
            "efficiency": 0.525,
        },
        "recommendations": ["Test recommendation 1", "Test recommendation 2"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        output_file = f.name

    try:
        generate_html_dashboard(metrics, output_file)

        # Verify HTML was generated
        with open(output_file) as f:
            html_content = f.read()

        assert "DevSynth Quality Dashboard" in html_content
        assert "82.5/100" in html_content
        assert "85.0%" in html_content
        assert "Test recommendation 1" in html_content

    finally:
        Path(output_file).unlink()
