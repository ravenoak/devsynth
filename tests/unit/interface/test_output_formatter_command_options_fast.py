"""Focused fast tests for OutputFormatter command overrides and helpers."""

from __future__ import annotations

import json

import pytest
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormatter

pytestmark = pytest.mark.fast


def test_format_command_output_json_yaml_with_and_without_console() -> None:
    """Command overrides should honor console availability and pretty-printing."""

    payload = {"alpha": 1, "nested": {"beta": ["x", "y"]}}

    plain_formatter = OutputFormatter()
    plain_formatter.set_format_options(indent=6, spacing=3, line_width=44)

    json_plain = plain_formatter.format_command_output(payload, format_name="json")
    assert isinstance(json_plain, str)
    assert json_plain == json.dumps(payload, indent=6, sort_keys=True)
    assert json.loads(json_plain) == payload

    yaml_plain = plain_formatter.format_command_output(payload, format_name="yaml")
    assert isinstance(yaml_plain, str)
    assert yaml_plain == yaml.dump(
        payload,
        indent=plain_formatter.indent,
        sort_keys=True,
        default_flow_style=False,
    )
    assert yaml.safe_load(yaml_plain) == payload

    assert plain_formatter.spacing == 3
    assert plain_formatter.line_width == 44

    console_formatter = OutputFormatter(console=Console(width=120, record=True))

    json_renderable = console_formatter.format_command_output(
        payload, format_name="json"
    )
    assert isinstance(json_renderable, Syntax)
    assert json_renderable.code == json.dumps(
        payload, indent=console_formatter.indent, sort_keys=True
    )

    yaml_renderable = console_formatter.format_command_output(
        payload, format_name="yaml"
    )
    assert isinstance(yaml_renderable, Syntax)
    assert yaml.safe_load(yaml_renderable.code) == payload


def test_format_command_output_table_fallback_and_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Table overrides should sanitize heterogenous lists and return empty tables."""

    formatter = OutputFormatter()
    sanitized: list[str] = []

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        sanitized.append(text)
        return f"safe:{text}"

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    mixed_items = ["plain", {"nested": [1, 2]}]
    fallback_text = formatter.format_command_output(
        mixed_items,
        format_name="table",
        title="Mixed",
    )

    assert isinstance(fallback_text, str)
    assert fallback_text.splitlines() == [
        "# Mixed",
        "",
        "• safe:plain",
        "• safe:{'nested': [1, 2]}",
    ]
    assert sanitized == ["plain", "{'nested': [1, 2]}"]

    sanitized.clear()
    empty_table = formatter.format_command_output(
        [], format_name="table", title="No Rows"
    )
    assert isinstance(empty_table, Table)
    assert empty_table.title == "No Rows"
    assert len(empty_table.columns) == 0
    assert len(empty_table.rows) == 0
    assert sanitized == []


def test_format_command_output_rich_renderables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rich overrides should wrap dictionaries, list rows, and bullets with sanitization."""

    formatter = OutputFormatter()
    sanitized: list[str] = []

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        sanitized.append(text)
        return f"san:{text}"

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    dict_panel = formatter.format_command_output(
        {"name": "delta", "count": 3},
        format_name="rich",
        title="Metadata",
    )
    assert isinstance(dict_panel, Panel)
    assert dict_panel.title == "Metadata"
    assert isinstance(dict_panel.renderable, Table)
    table = dict_panel.renderable
    assert [column.header for column in table.columns] == ["Key", "Value"]
    assert list(table.columns[0]._cells) == ["san:name", "san:count"]
    assert list(table.columns[1]._cells) == ["san:delta", "san:3"]
    assert sanitized == ["name", "delta", "count", "3"]

    sanitized.clear()
    records_table = formatter.format_command_output(
        [{"col": "alpha"}, {"col": "beta", "extra": {"z": 1}}],
        format_name="rich",
        title="Rows",
    )
    assert isinstance(records_table, Table)
    assert [column.header for column in records_table.columns] == ["col", "extra"]
    col_column = next(
        column for column in records_table.columns if column.header == "col"
    )
    extra_column = next(
        column for column in records_table.columns if column.header == "extra"
    )
    assert list(col_column._cells) == ["san:alpha", "san:beta"]
    assert extra_column._cells[0] == "san:"
    assert extra_column._cells[1] == json.dumps({"z": 1}, indent=formatter.indent)
    assert sanitized == ["alpha", "", "beta"]

    sanitized.clear()
    bullet_panel = formatter.format_command_output(
        ["first", "second"], format_name="rich", title="List"
    )
    assert isinstance(bullet_panel, Panel)
    assert isinstance(bullet_panel.renderable, Text)
    assert bullet_panel.renderable.plain == "• san:first\n• san:second\n"
    assert sanitized == ["first", "second"]

    sanitized.clear()
    empty_renderable = formatter.format_command_output(
        [], format_name="rich", title="Empty"
    )
    assert isinstance(empty_renderable, Table)
    assert empty_renderable.title == "Empty"
    assert len(empty_renderable.columns) == 0
    assert len(empty_renderable.rows) == 0
    assert sanitized == []
