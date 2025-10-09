"""
Tests for the testing script audit tool.

This module tests the functionality of scripts/audit_testing_scripts.py
to ensure it correctly identifies and categorizes testing scripts.
"""

import json

# Import the auditor classes
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts"))

from audit_testing_scripts import (
    ScriptAnalyzer,
    ScriptAuditor,
    generate_markdown_report,
)


@pytest.mark.fast
class TestScriptAnalyzer:
    """Test the ScriptAnalyzer class."""

    def test_categorizes_test_execution_script(self, tmp_path):
        """Test categorization of test execution scripts."""
        script_file = tmp_path / "run_tests.py"
        script_file.write_text(
            """
#!/usr/bin/env python3
'''Script to run pytest tests.'''

import pytest
import subprocess

def run_tests():
    subprocess.run(['pytest', '--cov=src'])

if __name__ == '__main__':
    run_tests()
"""
        )

        analyzer = ScriptAnalyzer()
        result = analyzer.analyze_script(script_file)

        assert "test_execution" in result["categories"]
        assert "pytest" in result["imports"]
        assert "run_tests" in result["functions"]
        assert result["executable"] == False  # Not executable in test
        assert "Script to run pytest tests." in result["description"]

    def test_categorizes_coverage_script(self, tmp_path):
        """Test categorization of coverage scripts."""
        script_file = tmp_path / "coverage_report.py"
        script_file.write_text(
            """
# Coverage analysis script
import coverage

def generate_coverage_report():
    cov = coverage.Coverage()
    cov.html_report()
"""
        )

        analyzer = ScriptAnalyzer()
        result = analyzer.analyze_script(script_file)

        assert "coverage" in result["categories"]
        assert "coverage" in result["imports"]
        assert "generate_coverage_report" in result["functions"]

    def test_categorizes_validation_script(self, tmp_path):
        """Test categorization of validation scripts."""
        script_file = tmp_path / "verify_test_markers.py"
        script_file.write_text(
            """
#!/usr/bin/env python3
'''Verify that all tests have speed markers.'''

def verify_markers():
    # Check test markers
    pass

def validate_test_structure():
    # Validate structure
    pass
"""
        )

        analyzer = ScriptAnalyzer()
        result = analyzer.analyze_script(script_file)

        assert "validation" in result["categories"]
        assert "verify_markers" in result["functions"]
        assert "validate_test_structure" in result["functions"]

    def test_handles_shell_script(self, tmp_path):
        """Test handling of shell scripts."""
        script_file = tmp_path / "run_tests.sh"
        script_file.write_text(
            """#!/bin/bash
# Test execution script
pytest --cov=src --cov-report=html
"""
        )

        analyzer = ScriptAnalyzer()
        result = analyzer.analyze_script(script_file)

        assert "test_execution" in result["categories"]
        assert result["functions"] == []  # No Python functions in shell script
        assert "pytest" in result["dependencies"]

    def test_handles_syntax_errors(self, tmp_path):
        """Test handling of files with syntax errors."""
        script_file = tmp_path / "broken_script.py"
        script_file.write_text(
            """
def broken_function(
    # Missing closing parenthesis and colon
    pass
"""
        )

        analyzer = ScriptAnalyzer()
        result = analyzer.analyze_script(script_file)

        # Should still analyze what it can
        assert result["name"] == "broken_script.py"
        assert result["size"] > 0


@pytest.mark.fast
class TestScriptAuditor:
    """Test the ScriptAuditor class."""

    def test_finds_testing_scripts(self, tmp_path):
        """Test finding testing scripts by pattern and content."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create various script types
        (scripts_dir / "run_tests.py").write_text(
            "import pytest\ndef run_tests(): pass"
        )
        (scripts_dir / "coverage_report.py").write_text(
            "import coverage\ndef report(): pass"
        )
        (scripts_dir / "verify_markers.py").write_text("def verify(): pass")
        (scripts_dir / "unrelated.py").write_text(
            "print('hello')"
        )  # Should not be found
        (scripts_dir / "test_something.py").write_text(
            "def test_func(): pass"
        )  # Should be found

        auditor = ScriptAuditor(scripts_dir)
        found_scripts = auditor.find_testing_scripts()

        script_names = [s.name for s in found_scripts]
        assert "run_tests.py" in script_names
        assert "coverage_report.py" in script_names
        assert "verify_markers.py" in script_names
        assert "test_something.py" in script_names
        assert "unrelated.py" not in script_names

    def test_analyzes_overlaps(self, tmp_path):
        """Test overlap analysis."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create scripts with overlapping functionality
        (scripts_dir / "run_tests1.py").write_text(
            """
import pytest
def run_tests(): pass
def common_function(): pass
"""
        )

        (scripts_dir / "run_tests2.py").write_text(
            """
import pytest
def execute_tests(): pass
def common_function(): pass
"""
        )

        auditor = ScriptAuditor(scripts_dir)
        auditor.scripts = [
            {
                "name": "run_tests1.py",
                "path": "run_tests1.py",
                "categories": ["test_execution"],
                "functions": ["run_tests", "common_function"],
            },
            {
                "name": "run_tests2.py",
                "path": "run_tests2.py",
                "categories": ["test_execution"],
                "functions": ["execute_tests", "common_function"],
            },
        ]

        overlaps = auditor.analyze_overlaps()

        assert "test_execution" in overlaps["category_overlaps"]
        assert len(overlaps["category_overlaps"]["test_execution"]) == 2
        assert "common_function" in overlaps["duplicate_functions"]
        assert overlaps["overlap_summary"]["categories_with_overlaps"] == 1

    @patch("subprocess.run")
    def test_git_usage_frequency(self, mock_run, tmp_path):
        """Test git usage frequency analysis."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "test_script.py"
        script_file.write_text("print('test')")

        # Mock git commands
        mock_run.side_effect = [
            MagicMock(
                stdout="commit1\ncommit2\ncommit3", returncode=0
            ),  # log --oneline
            MagicMock(
                stdout="2023-01-15 10:30:00 +0000", returncode=0
            ),  # last modified
            MagicMock(
                stdout="2023-01-01 09:00:00 +0000", returncode=0
            ),  # creation date
        ]

        auditor = ScriptAuditor(scripts_dir)
        git_stats = auditor.get_git_usage_frequency(script_file)

        assert git_stats["commit_count"] == 3
        assert git_stats["last_modified"] == "2023-01-15 10:30:00 +0000"
        assert git_stats["created_date"] == "2023-01-01 09:00:00 +0000"
        assert git_stats["frequency_score"] == 3

    def test_generates_consolidation_recommendations(self, tmp_path):
        """Test consolidation recommendations generation."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        auditor = ScriptAuditor(scripts_dir)
        auditor.scripts = [
            {
                "name": "run_tests1.py",
                "path": "run_tests1.py",
                "categories": ["test_execution"],
                "functions": ["run_tests"],
                "size": 100,
                "lines": 50,
                "git_stats": {"frequency_score": 1},
            },
            {
                "name": "run_tests2.py",
                "path": "run_tests2.py",
                "categories": ["test_execution"],
                "functions": ["execute_tests"],
                "size": 150,
                "lines": 75,
                "git_stats": {"frequency_score": 2},
            },
            {
                "name": "run_tests3.py",
                "path": "run_tests3.py",
                "categories": ["test_execution"],
                "functions": ["test_runner"],
                "size": 80,
                "lines": 40,
                "git_stats": {"frequency_score": 1},
            },
        ]

        recommendations = auditor.generate_consolidation_recommendations()

        # Should identify test_execution group for consolidation
        assert len(recommendations["consolidation_groups"]) >= 1
        test_exec_group = next(
            (
                g
                for g in recommendations["consolidation_groups"]
                if g["category"] == "test_execution"
            ),
            None,
        )
        assert test_exec_group is not None
        assert len(test_exec_group["scripts"]) == 3

        # Should have CLI migration mappings
        assert "run_tests1.py" in recommendations["cli_migration_mapping"]
        assert (
            recommendations["cli_migration_mapping"]["run_tests1.py"]
            == "devsynth test run"
        )


@pytest.mark.fast
class TestMarkdownGeneration:
    """Test markdown report generation."""

    def test_generates_markdown_report(self):
        """Test markdown report generation."""
        audit_data = {
            "metadata": {
                "generated_at": "2023-01-01T12:00:00",
                "scripts_directory": "/test/scripts",
            },
            "summary": {
                "total_scripts": 5,
                "total_lines_of_code": 500,
                "categories_in_use": 3,
                "average_script_size": 100,
            },
            "scripts": [
                {"categories": ["test_execution"], "name": "test1.py"},
                {"categories": ["coverage"], "name": "test2.py"},
                {"categories": ["test_execution", "validation"], "name": "test3.py"},
            ],
            "overlaps": {
                "category_overlaps": {
                    "test_execution": [
                        {"name": "test1.py", "description": "First test script"},
                        {"name": "test3.py", "description": "Third test script"},
                    ]
                },
                "overlap_summary": {
                    "categories_with_overlaps": 1,
                    "duplicate_function_count": 0,
                },
            },
            "recommendations": {
                "consolidation_groups": [
                    {
                        "category": "test_execution",
                        "description": "Test execution scripts",
                        "consolidation_benefit": "high",
                        "scripts": [{"name": "test1.py", "size": 100, "functions": 2}],
                    }
                ],
                "cli_migration_mapping": {"test1.py": "devsynth test run"},
                "deprecation_candidates": [
                    {"name": "old_test.py", "reason": "Low usage"}
                ],
            },
            "category_definitions": {
                "test_execution": {"description": "Scripts that execute tests"},
                "coverage": {"description": "Coverage analysis scripts"},
            },
        }

        markdown = generate_markdown_report(audit_data)

        assert "# Testing Scripts Audit Report" in markdown
        assert "Total scripts analyzed**: 5" in markdown
        assert "test_execution** (2 scripts)" in markdown  # test1.py and test3.py
        assert "coverage** (1 scripts)" in markdown  # test2.py
        assert "## Overlapping Functionality" in markdown
        assert "## Consolidation Recommendations" in markdown
        assert "## CLI Migration Mapping" in markdown
        assert "`test1.py` | `devsynth test run`" in markdown
        assert "## Deprecation Candidates" in markdown
        assert "`old_test.py`: Low usage" in markdown


@pytest.mark.fast
def test_main_function_help():
    """Test that main function provides help."""
    from audit_testing_scripts import main

    with patch("sys.argv", ["audit_testing_scripts.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


@pytest.mark.fast
def test_main_function_missing_scripts_dir():
    """Test main function with missing scripts directory."""
    from audit_testing_scripts import main

    with patch(
        "sys.argv", ["audit_testing_scripts.py", "--scripts-dir", "nonexistent"]
    ):
        result = main()
        assert result == 1


@pytest.mark.fast
def test_integration_audit_workflow(tmp_path):
    """Test complete audit workflow."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    # Create sample scripts
    (scripts_dir / "run_tests.py").write_text(
        """
#!/usr/bin/env python3
'''Main test runner script.'''

import pytest
import subprocess

def run_all_tests():
    subprocess.run(['pytest', '--cov=src'])

def run_fast_tests():
    subprocess.run(['pytest', '-m', 'fast'])
"""
    )

    (scripts_dir / "verify_markers.py").write_text(
        """
#!/usr/bin/env python3
'''Verify test markers.'''

def verify_speed_markers():
    # Check for speed markers
    pass
"""
    )

    auditor = ScriptAuditor(scripts_dir)
    audit_data = auditor.audit(include_git_history=False)

    assert audit_data["summary"]["total_scripts"] == 2
    assert audit_data["summary"]["categories_in_use"] >= 1

    # Check that scripts were categorized
    script_names = [s["name"] for s in audit_data["scripts"]]
    assert "run_tests.py" in script_names
    assert "verify_markers.py" in script_names

    # Check for test execution category
    test_exec_scripts = [
        s for s in audit_data["scripts"] if "test_execution" in s.get("categories", [])
    ]
    assert len(test_exec_scripts) >= 1
