"""Unit tests for CLI output utilities."""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli.output import (
    OUTPUT_STYLES,
    OutputType,
    colorize,
    print_error,
    print_info,
    print_success,
)


class TestOutputType:
    """Test OutputType enum."""

    @pytest.mark.fast
    def test_output_type_values(self):
        """Test that OutputType has expected values."""
        assert OutputType.INFO == "info"
        assert OutputType.SUCCESS == "success"
        assert OutputType.WARNING == "warning"
        assert OutputType.ERROR == "error"
        assert OutputType.DEBUG == "debug"
        assert OutputType.CODE == "code"
        assert OutputType.COMMAND == "command"
        assert OutputType.RESULT == "result"
        assert OutputType.HEADER == "header"
        assert OutputType.SUBHEADER == "subheader"


class TestOutputStyles:
    """Test OUTPUT_STYLES configuration."""

    @pytest.mark.fast
    def test_output_styles_contains_all_types(self):
        """Test that OUTPUT_STYLES has entries for all OutputType values."""
        for output_type in OutputType:
            assert output_type in OUTPUT_STYLES
            assert isinstance(OUTPUT_STYLES[output_type], str)

    @pytest.mark.fast
    def test_output_styles_values(self):
        """Test specific OUTPUT_STYLES values."""
        assert OUTPUT_STYLES[OutputType.INFO] == "blue"
        assert OUTPUT_STYLES[OutputType.SUCCESS] == "green"
        assert OUTPUT_STYLES[OutputType.ERROR] == "red"


class TestOutputFunctions:
    """Test output utility functions."""

    @pytest.mark.fast
    def test_colorize_info(self):
        """Test colorize function for info type."""
        result = colorize("Test message", OutputType.INFO)
        assert isinstance(result, str)
        assert "Test message" in result

    @pytest.mark.fast
    def test_colorize_success(self):
        """Test colorize function for success type."""
        result = colorize("Success message", OutputType.SUCCESS)
        assert isinstance(result, str)
        assert "Success message" in result

    @pytest.mark.fast
    def test_colorize_error(self):
        """Test colorize function for error type."""
        result = colorize("Error message", OutputType.ERROR)
        assert isinstance(result, str)
        assert "Error message" in result

    @pytest.mark.fast
    @patch("devsynth.application.cli.output.Console")
    def test_print_info(self, mock_console_class):
        """Test print_info function."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        print_info("Info message")

        mock_console.print.assert_called_once()

    @pytest.mark.fast
    @patch("devsynth.application.cli.output.Console")
    def test_print_success(self, mock_console_class):
        """Test print_success function."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        print_success("Success message")

        mock_console.print.assert_called_once()

    @pytest.mark.fast
    @patch("devsynth.application.cli.output.Console")
    def test_print_error(self, mock_console_class):
        """Test print_error function."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        print_error("Error message")

        mock_console.print.assert_called_once()
