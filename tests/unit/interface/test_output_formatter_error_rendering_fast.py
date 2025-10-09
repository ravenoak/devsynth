"""Targeted fast tests for OutputFormatter error and sanitization paths."""

from __future__ import annotations

import pytest
from rich.table import Table
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormat, OutputFormatter

pytestmark = pytest.mark.fast


def test_format_message_error_styles_and_escapes_markup() -> None:
    """Errors render with bold red styling and escaped HTML content."""

    formatter = OutputFormatter()
    result = formatter.format_message(
        "ERROR: Something <b>bad</b>", message_type="error"
    )

    assert isinstance(result, Text)
    assert result.style == "bold red"
    assert result.plain == "ERROR: Something &lt;b&gt;bad&lt;/b&gt;"


def test_markdown_branch_sanitizes_hyperlinks() -> None:
    """Markdown conversion should escape hyperlink markup and retain safe URLs."""

    formatter = OutputFormatter()
    data = {
        "References": [
            '<a href="javascript:alert(1)">Alert</a>',
            "https://example.com/docs",
        ]
    }

    markdown = formatter.format_structured(data, OutputFormat.MARKDOWN, title="Links")

    assert isinstance(markdown, str)
    assert markdown.splitlines()[0] == "# Links"
    assert "&lt;a href=&quot;javascript:alert(1)&quot;&gt;Alert&lt;/a&gt;" in markdown
    assert "https://example.com/docs" in markdown
    assert "<a href" not in markdown


def test_table_branch_sanitizes_script_links() -> None:
    """Table formatting escapes script tags and preserves safe hyperlinks."""

    formatter = OutputFormatter()
    rows = [
        {"name": "alpha", "link": "https://example.com"},
        {"name": "beta", "link": "<script>alert('x')</script>"},
    ]

    table = formatter.format_structured(rows, OutputFormat.TABLE, title="Endpoints")

    assert isinstance(table, Table)
    assert table.title == "Endpoints"
    headers = [column.header for column in table.columns]
    assert headers == sorted(headers)
    link_column = table.columns[headers.index("link")]
    assert link_column._cells[0] == "https://example.com"
    assert link_column._cells[1] == ""
    assert all(
        "<script>" not in cell for column in table.columns for cell in column._cells
    )
