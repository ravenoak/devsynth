"""
Integration test for the SelfAnalyzer class.

This test verifies that the SelfAnalyzer can analyze the DevSynth codebase
and generate insights that can be used for self-improvement.
"""

import os
import pytest
from pathlib import Path

from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer

# Mark tests as requiring the codebase resource
codebase_available = pytest.mark.requires_resource("codebase")


class TestSelfAnalyzer:
    """Test the SelfAnalyzer class."""

    @codebase_available
    def test_analyze_devsynth_codebase(self):
        """Test that the SelfAnalyzer can analyze the DevSynth codebase."""
        # Get the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        # Create a SelfAnalyzer instance
        analyzer = SelfAnalyzer(project_root)

        # Analyze the codebase
        result = analyzer.analyze()

        # Verify that the result contains the expected keys
        assert "code_analysis" in result
        assert "insights" in result

        # Verify that the insights contain the expected sections
        insights = result["insights"]
        assert "metrics_summary" in insights
        assert "architecture" in insights
        assert "code_quality" in insights
        assert "test_coverage" in insights
        assert "improvement_opportunities" in insights

        # Verify that the architecture analysis identified the layers
        architecture = insights["architecture"]
        assert "layers" in architecture
        layers = architecture["layers"]
        assert "domain" in layers
        assert "application" in layers
        assert "adapters" in layers
        assert "ports" in layers

        # Verify that the code quality analysis includes docstring coverage
        code_quality = insights["code_quality"]
        assert "docstring_coverage" in code_quality
        assert "total_files" in code_quality
        assert "total_classes" in code_quality
        assert "total_functions" in code_quality

        # Verify that the test coverage analysis includes coverage percentage
        test_coverage = insights["test_coverage"]
        assert "total_symbols" in test_coverage
        assert "tested_symbols" in test_coverage
        assert "coverage_percentage" in test_coverage

        # Print some key metrics for debugging
        print(f"\nCode Analysis Results:")
        print(f"Total files: {code_quality['total_files']}")
        print(f"Total classes: {code_quality['total_classes']}")
        print(f"Total functions: {code_quality['total_functions']}")
        print(f"Docstring coverage (files): {code_quality['docstring_coverage']['files'] * 100:.1f}%")
        print(f"Docstring coverage (classes): {code_quality['docstring_coverage']['classes'] * 100:.1f}%")
        print(f"Docstring coverage (functions): {code_quality['docstring_coverage']['functions'] * 100:.1f}%")
        print(f"Test coverage: {test_coverage['coverage_percentage'] * 100:.1f}%")

        # Print improvement opportunities
        print(f"\nImprovement Opportunities:")
        for opportunity in insights["improvement_opportunities"]:
            print(f"- [{opportunity['priority']}] {opportunity['description']}")

    @codebase_available
    def test_architecture_violations(self):
        """Test that the SelfAnalyzer can detect architecture violations."""
        # Get the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        # Create a SelfAnalyzer instance
        analyzer = SelfAnalyzer(project_root)

        # Analyze the codebase
        result = analyzer.analyze()

        # Get the architecture violations
        architecture = result["insights"]["architecture"]
        violations = architecture["architecture_violations"]

        # Print the violations for debugging
        print(f"\nArchitecture Violations:")
        for violation in violations:
            print(f"- {violation['description']}")

        # Verify that the violations are properly structured
        for violation in violations:
            assert "source_layer" in violation
            assert "target_layer" in violation
            assert "description" in violation

    @codebase_available
    def test_improvement_opportunities(self):
        """Test that the SelfAnalyzer can identify improvement opportunities."""
        # Get the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        # Create a SelfAnalyzer instance
        analyzer = SelfAnalyzer(project_root)

        # Analyze the codebase
        result = analyzer.analyze()

        # Get the improvement opportunities
        opportunities = result["insights"]["improvement_opportunities"]

        # Verify that the opportunities are properly structured
        for opportunity in opportunities:
            assert "type" in opportunity
            assert "description" in opportunity
            assert "priority" in opportunity
            assert opportunity["priority"] in ["high", "medium", "low"]


if __name__ == "__main__":
    pytest.main(["-v", "test_self_analyzer.py"])
