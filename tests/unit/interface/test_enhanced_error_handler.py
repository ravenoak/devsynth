"""Tests for the enhanced error handler."""

from unittest.mock import MagicMock

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devsynth.interface.enhanced_error_handler import (
    ActionableErrorSuggestion,
    ImprovedErrorHandler,
)


@pytest.fixture
def stub_console():
    """Provide a console stub to avoid real output."""
    return MagicMock(spec=Console)


class TestEnhancedErrorHandler:
    """Tests for actionable suggestions and improved error formatting.

    ReqID: N/A
    """

    @pytest.mark.fast
    def test_actionable_error_suggestion_str_includes_details(self):
        """ActionableErrorSuggestion.__str__ includes steps, links, and examples.

        ReqID: FR-97"""
        suggestion = ActionableErrorSuggestion(
            "Install dependencies",
            documentation_link="http://example.com/docs",
            command_example="pip install example",
            actionable_steps=["Step one", "Step two"],
            code_example="print('hello')",
        )

        result = str(suggestion)

        assert "Actionable steps:" in result
        assert "1. Step one" in result
        assert "Documentation: http://example.com/docs" in result
        assert "Example command: pip install example" in result
        assert "Example code:\nprint('hello')" in result

    @pytest.mark.fast
    def test_format_error_wraps_with_footer(self, stub_console):
        """ImprovedErrorHandler.format_error wraps errors with guidance footer.

        ReqID: FR-97"""
        handler = ImprovedErrorHandler(console=stub_console)
        error = ValueError("boom")

        panel = handler.format_error(error)

        assert isinstance(panel, Panel)
        assert isinstance(panel.subtitle, Text)
        subtitle = panel.subtitle.plain
        assert "devsynth doctor" in subtitle
        assert "troubleshooting.html" in subtitle
