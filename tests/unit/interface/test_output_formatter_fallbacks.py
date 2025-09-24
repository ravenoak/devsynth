"""Targeted fast tests for OutputFormatter fallback behaviors."""

from __future__ import annotations

import json
from typing import Any

import pytest
import yaml
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormat, OutputFormatter

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def _patch_sanitize(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure output sanitization is deterministic for assertions."""

    def identity(self: OutputFormatter, text: str) -> str:
        return str(text)

    monkeypatch.setattr(OutputFormatter, "sanitize_output", identity)


def test_table_format_falls_back_to_text_for_nontabular_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """format_structured(table) should fall back to text when rows cannot be built.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    calls: list[tuple[Any, OutputFormat | None, str | None]] = []
    original = OutputFormatter.format_structured

    def spy(
        self: OutputFormatter,
        data: Any,
        output_format: OutputFormat | None = None,
        title: str | None = None,
    ) -> Any:
        calls.append((data, output_format, title))
        return original(self, data, output_format, title)

    monkeypatch.setattr(OutputFormatter, "format_structured", spy)

    scalar_result = formatter.format_structured(
        "diagnostic", OutputFormat.TABLE, title="Scalar"
    )
    assert isinstance(scalar_result, str)
    assert scalar_result == "# Scalar\n\ndiagnostic"
    assert [call[1] for call in calls] == [OutputFormat.TABLE, OutputFormat.TEXT]
    assert calls[1][0] == "diagnostic"

    calls.clear()

    heterogeneous = formatter.format_structured(
        ["alpha", 123], OutputFormat.TABLE, title="Mixed"
    )
    assert isinstance(heterogeneous, str)
    assert heterogeneous == "# Mixed\n\n• alpha\n• 123"
    assert [call[1] for call in calls] == [OutputFormat.TABLE, OutputFormat.TEXT]
    assert calls[1][0] == ["alpha", 123]


def test_rich_format_selects_renderables_for_data_shapes() -> None:
    """format_structured(rich) should choose Panel/Table/Text per input type.

    ReqID: N/A
    """

    formatter = OutputFormatter()

    dict_panel = formatter.format_structured(
        {"name": "DevSynth", "status": "ready"}, OutputFormat.RICH, title="Metadata"
    )
    assert isinstance(dict_panel, Panel)
    assert dict_panel.title == "Metadata"
    assert isinstance(dict_panel.renderable, Table)

    list_table = formatter.format_structured(
        [
            {"column": "alpha", "value": 1},
            {"column": "beta", "details": ["nested", "values"]},
        ],
        OutputFormat.RICH,
    )
    assert isinstance(list_table, Table)
    assert [column.header for column in list_table.columns] == [
        "column",
        "details",
        "value",
    ]

    bullet_panel = formatter.format_structured(
        ["first", "second"], OutputFormat.RICH, title="Items"
    )
    assert isinstance(bullet_panel, Panel)
    bullet_text = bullet_panel.renderable
    assert isinstance(bullet_text, Text)
    assert bullet_text.plain == "• first\n• second\n"

    class FalsyList(list):
        def __bool__(self) -> bool:  # pragma: no cover - simple override
            return False

    empty_panel = formatter.format_structured(
        FalsyList(["ignored entry"]), OutputFormat.RICH, title="Maybe Empty"
    )
    assert isinstance(empty_panel, Panel)
    empty_text = empty_panel.renderable
    assert isinstance(empty_text, Text)
    assert empty_text.plain == "(empty list)"

    scalar_text = formatter.format_structured("plain", OutputFormat.RICH)
    assert isinstance(scalar_text, Text)
    assert scalar_text.plain == "plain"


def test_list_of_dicts_table_renders_missing_and_complex_values() -> None:
    """Ensure list-of-dicts tables keep order, blanks, and JSON serialization.

    ReqID: N/A
    """

    formatter = OutputFormatter()

    records = [
        {"name": "alpha", "value": 1},
        {"name": "beta", "metadata": {"nested": ["x", "y"]}},
    ]

    table = formatter.format_structured(records, OutputFormat.TABLE, title="Records")
    assert isinstance(table, Table)
    assert [column.header for column in table.columns] == ["metadata", "name", "value"]

    metadata_column = next(
        column for column in table.columns if column.header == "metadata"
    )
    value_column = next(column for column in table.columns if column.header == "value")

    assert metadata_column._cells[0] == ""
    assert metadata_column._cells[1] == json.dumps(
        records[1]["metadata"], indent=formatter.indent
    )
    assert value_column._cells[0] == "1"
    assert value_column._cells[1] == ""


def test_set_format_options_and_command_output_overrides() -> None:
    """set_format_options updates formatter state and drives command overrides.

    ReqID: N/A
    """

    formatter = OutputFormatter()
    formatter.set_format_options(indent=4, spacing=2, line_width=88)

    assert formatter.indent == 4
    assert formatter.spacing == 2
    assert formatter.line_width == 88

    yaml_output = formatter.format_command_output(
        {"outer": {"inner": [1, 2]}}, format_name="yaml", title="Tree"
    )
    assert isinstance(yaml_output, str)
    assert yaml.safe_load(yaml_output) == {"outer": {"inner": [1, 2]}}

    default_renderable = formatter.format_command_output(
        "plain report", format_name="unknown.ext"
    )
    assert isinstance(default_renderable, Text)
    assert default_renderable.plain == "plain report"
