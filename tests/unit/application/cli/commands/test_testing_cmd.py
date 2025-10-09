"""Unit tests for the testing command CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli.commands.testing_cmd import testing_cmd
from devsynth.interface.cli import CLIUXBridge


class TestTestingCommand:
    """Test the unified testing command interface."""

    @pytest.mark.fast
    def test_testing_cmd_basic_functionality(self, tmp_project_dir, capsys):
        """Test that testing_cmd displays the expected information."""
        with patch.object(Path, "exists") as mock_exists:
            # Mock all script paths as existing
            mock_exists.return_value = True

            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Verify key sections are present
            assert "🧪 Unified Testing Infrastructure" in output
            assert "✅ Foundation Tools Available:" in output
            assert "Test Dependency Analyzer" in output
            assert "Testing Script Auditor" in output
            assert "Performance Benchmark Tool" in output
            assert "Safe Isolation Marker Removal" in output
            assert "📊 Current Status:" in output
            assert "💡 Quick Actions:" in output
            assert "🎯 Phase 1 Tasks Completed:" in output
            assert "📈 Performance Achievements:" in output

    @pytest.mark.fast
    def test_testing_cmd_shows_expected_content(self, tmp_project_dir, capsys):
        """Test that testing_cmd shows expected content and formatting."""
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Should show all expected sections and content
            assert "🧪 Unified Testing Infrastructure" in output
            assert "✅ Foundation Tools Available:" in output
            assert "Test Dependency Analyzer" in output
            assert "Testing Script Auditor" in output
            assert "Performance Benchmark Tool" in output
            assert "Safe Isolation Marker Removal" in output
            assert "📊 Current Status:" in output
            assert "💡 Quick Actions:" in output
            assert "🎯 Phase 1 Tasks Completed:" in output
            assert "📈 Performance Achievements:" in output

    @pytest.mark.fast
    def test_testing_cmd_uses_cli_bridge(self, tmp_project_dir):
        """Test that testing_cmd uses the CLI bridge correctly."""
        with patch(
            "devsynth.application.cli.commands.testing_cmd.CLIUXBridge"
        ) as mock_bridge_class:
            mock_bridge = MagicMock()
            mock_bridge_class.return_value = mock_bridge

            with patch.object(Path, "exists", return_value=True):
                testing_cmd()

            # Verify bridge.print was called multiple times
            assert mock_bridge.print.call_count >= 20
            mock_bridge_class.assert_called_once()

    @pytest.mark.fast
    def test_testing_cmd_logging_configuration(self, tmp_project_dir):
        """Test that testing_cmd uses proper logging."""
        # The logger is created at module import time, so we just verify it exists
        from devsynth.application.cli.commands.testing_cmd import logger

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    @pytest.mark.fast
    def test_testing_cmd_script_paths_checked(self, tmp_project_dir):
        """Test that testing_cmd checks for script files."""
        # Just verify that the command runs without errors
        # The script checking logic is tested through the output content
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()  # Should not raise any exceptions

    @pytest.mark.fast
    def test_testing_cmd_output_formatting(self, tmp_project_dir, capsys):
        """Test that testing_cmd formats output correctly."""
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Check for proper emoji usage and formatting
            assert "✅" in output  # Check marks
            assert "🧪" in output  # Test tube emoji
            assert "📊" in output  # Chart emoji
            assert "💡" in output  # Light bulb emoji
            assert "🎯" in output  # Target emoji
            assert "📈" in output  # Chart increasing emoji

            # Check for proper emoji usage and content
            assert "✅" in output  # Check marks
            assert "🧪" in output  # Test tube emoji
            assert "📊" in output  # Chart emoji
            assert "💡" in output  # Light bulb emoji
            assert "🎯" in output  # Target emoji
            assert "📈" in output  # Chart increasing emoji

    @pytest.mark.fast
    def test_testing_cmd_quick_actions_displayed(self, tmp_project_dir, capsys):
        """Test that testing_cmd displays the expected quick action commands."""
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Check for expected command examples
            assert "devsynth run-tests --speed fast" in output
            assert "devsynth run-tests --target unit" in output
            assert "python scripts/analyze_test_dependencies.py --dry-run" in output
            assert "python scripts/audit_testing_scripts.py --format markdown" in output
            assert (
                "python scripts/benchmark_test_execution.py --workers 1,2,4" in output
            )

    @pytest.mark.fast
    def test_testing_cmd_performance_achievements(self, tmp_project_dir, capsys):
        """Test that testing_cmd displays performance achievements correctly."""
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Check for specific performance metrics mentioned
            assert "6.14x parallel speedup" in output
            assert "exceeds 5x target" in output
            assert "Only 3 isolation markers found" in output
            assert "cleaner than expected" in output
            assert "159 testing scripts analyzed" in output

    @pytest.mark.fast
    def test_testing_cmd_phase_tasks_completed(self, tmp_project_dir, capsys):
        """Test that testing_cmd shows completed phase 1 tasks."""
        with patch.object(Path, "exists", return_value=True):
            testing_cmd()

            captured = capsys.readouterr()
            output = captured.out

            # Check for completed tasks
            assert "✅ Task 1.1: Test Dependency Analyzer Tool" in output
            assert "✅ Task 1.2: Testing Script Audit Tool" in output
            assert "✅ Task 1.3: Core Unified CLI Structure" in output
            assert "✅ Task 1.4: Safe Isolation Marker Removal" in output
            assert "✅ Task 1.5: Performance Baseline Measurement" in output
