"""Tests for the OutputFormatter class."""

import pytest
from unittest.mock import MagicMock, patch
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormatter, formatter


class TestOutputFormatter:
    """Tests for the OutputFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create an OutputFormatter for testing."""
        return OutputFormatter()

    @pytest.fixture
    def console(self):
        """Create a mock console for testing."""
        return MagicMock(spec=Console)

    def test_sanitize_output(self, formatter):
        """Test sanitizing output text."""
        # Test with normal text
        assert formatter.sanitize_output("Hello, world!") == "Hello, world!"

        # Test with HTML tags (script tags are removed by sanitize_input)
        assert formatter.sanitize_output("<script>alert('XSS')</script>") == ""
        assert formatter.sanitize_output("<div>Some content</div>") == "&lt;div&gt;Some content&lt;/div&gt;"

        # Test with empty string
        assert formatter.sanitize_output("") == ""

        # Test with None
        with pytest.raises(AttributeError):
            formatter.sanitize_output(None)

    def test_detect_message_type(self, formatter):
        """Test detecting message types."""
        # Test error messages
        assert formatter.detect_message_type("ERROR: Something went wrong") == "error"
        assert formatter.detect_message_type("FAILED: Task failed") == "error"
        assert formatter.detect_message_type("CRITICAL: System failure") == "error"

        # Test warning messages
        assert formatter.detect_message_type("WARNING: Be careful") == "warning"

        # Test success messages
        assert formatter.detect_message_type("SUCCESS: Task completed") == "success"
        assert formatter.detect_message_type("COMPLETED: All done") == "success"
        assert formatter.detect_message_type("Task completed successfully") == "success"

        # Test info messages
        assert formatter.detect_message_type("INFO: Just FYI") == "info"
        assert formatter.detect_message_type("NOTE: Take note of this") == "info"

        # Test heading messages
        assert formatter.detect_message_type("# Heading 1") == "heading"
        assert formatter.detect_message_type("## Heading 2") == "heading"

        # Test normal messages
        assert formatter.detect_message_type("Just a normal message") == "normal"
        assert formatter.detect_message_type("") == "normal"

    def test_format_message(self, formatter):
        """Test formatting messages."""
        # Test with highlight
        result = formatter.format_message("Hello, world!", highlight=True)
        assert isinstance(result, Panel)
        assert result.renderable == "Hello, world!"

        # Test error message
        result = formatter.format_message("ERROR: Something went wrong")
        assert isinstance(result, Text)
        assert str(result) == "ERROR: Something went wrong"
        assert result.style == "bold red"

        # Test warning message
        result = formatter.format_message("WARNING: Be careful")
        assert isinstance(result, Text)
        assert str(result) == "WARNING: Be careful"
        assert result.style == "yellow"

        # Test success message
        result = formatter.format_message("SUCCESS: Task completed")
        assert isinstance(result, Text)
        assert str(result) == "SUCCESS: Task completed"
        assert result.style == "green"

        # Test info message
        result = formatter.format_message("INFO: Just FYI")
        assert isinstance(result, Text)
        assert str(result) == "INFO: Just FYI"
        assert result.style == "cyan"

        # Test heading message
        result = formatter.format_message("# Heading 1")
        assert isinstance(result, Text)
        assert str(result) == "Heading 1"
        assert result.style == "bold blue"

        result = formatter.format_message("## Heading 2")
        assert isinstance(result, Text)
        assert str(result) == "Heading 2"
        assert result.style == "bold cyan"

        # Test normal message
        result = formatter.format_message("Just a normal message")
        assert isinstance(result, Text)
        assert str(result) == "Just a normal message"
        assert result.style is None

        # Test with Rich markup
        result = formatter.format_message("[bold]Bold text[/bold]")
        assert result == "[bold]Bold text[/bold]"

        # Test with HTML tags
        result = formatter.format_message("<div>Some content</div>")
        assert isinstance(result, Text)
        assert str(result) == "&lt;div&gt;Some content&lt;/div&gt;"

        # Test with script tags (which are removed by sanitize_input)
        result = formatter.format_message("<script>alert('XSS')</script>")
        assert isinstance(result, Text)
        assert str(result) == ""

        # Test with explicit message type
        result = formatter.format_message("Hello, world!", message_type="error")
        assert isinstance(result, Text)
        assert str(result) == "Hello, world!"
        assert result.style == "bold red"

    def test_display(self, formatter, console):
        """Test displaying formatted messages."""
        formatter.set_console(console)

        # Test with normal message
        formatter.display("Hello, world!")
        console.print.assert_called_once()
        assert isinstance(console.print.call_args[0][0], Text)
        assert str(console.print.call_args[0][0]) == "Hello, world!"
        console.print.reset_mock()

        # Test with highlight
        formatter.display("Hello, world!", highlight=True)
        console.print.assert_called_once()
        assert isinstance(console.print.call_args[0][0], Panel)
        assert console.print.call_args[0][0].renderable == "Hello, world!"
        assert console.print.call_args[1]["style"] == "bold white on blue"
        console.print.reset_mock()

        # Test with error message
        formatter.display("ERROR: Something went wrong")
        console.print.assert_called_once()
        assert isinstance(console.print.call_args[0][0], Text)
        assert str(console.print.call_args[0][0]) == "ERROR: Something went wrong"
        assert console.print.call_args[0][0].style == "bold red"
        console.print.reset_mock()

        # Test without console
        formatter.console = None
        with pytest.raises(ValueError):
            formatter.display("Hello, world!")

    def test_set_console(self, formatter, console):
        """Test setting the console."""
        formatter.set_console(console)
        assert formatter.console == console

    def test_format_table(self, formatter):
        """Test formatting a dictionary as a table."""
        data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
        }

        # Test without title
        result = formatter.format_table(data)
        assert "name  : John Doe" in result
        assert "age   : 30" in result
        assert "email : john@example.com" in result

        # Test with title
        result = formatter.format_table(data, title="User Information")
        assert result.startswith("# User Information")
        assert "name  : John Doe" in result
        assert "age   : 30" in result
        assert "email : john@example.com" in result

        # Test with empty data
        result = formatter.format_table({})
        assert result == ""

        # Test with HTML in data
        data = {
            "name": "<div>Some content</div>",
            "age": 30,
        }
        result = formatter.format_table(data)
        assert "&lt;div&gt;Some content&lt;/div&gt;" in result
        assert "30" in result

    def test_format_list(self, formatter):
        """Test formatting a list of items."""
        items = ["Item 1", "Item 2", "Item 3"]

        # Test without title
        result = formatter.format_list(items)
        assert "• Item 1" in result
        assert "• Item 2" in result
        assert "• Item 3" in result

        # Test with title
        result = formatter.format_list(items, title="My List")
        assert result.startswith("# My List")
        assert "• Item 1" in result
        assert "• Item 2" in result
        assert "• Item 3" in result

        # Test with custom bullet
        result = formatter.format_list(items, bullet="-")
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

        # Test with empty list
        result = formatter.format_list([])
        assert result == ""

        # Test with HTML in items
        items = ["<div>Some content</div>", "Item 2"]
        result = formatter.format_list(items)
        assert "• &lt;div&gt;Some content&lt;/div&gt;" in result
        assert "• Item 2" in result


def test_formatter_singleton():
    """Test that the formatter singleton is an instance of OutputFormatter."""
    assert isinstance(formatter, OutputFormatter)
