"""Fast parameterized tests for OutputFormatter structured branches."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import pytest
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormat, OutputFormatter

pytestmark = pytest.mark.fast


CaseVerifier = Callable[[Any, OutputFormatter], None]


@dataclass(frozen=True)
class StructuredScenario:
    """Describe a format_structured scenario to exercise a code path."""

    id: str
    output_format: OutputFormat
    data: Any
    title: str | None
    with_console: bool
    verifier: CaseVerifier


class FalsyList(list):
    """List that reports False to drive specific Rich fallbacks."""

    def __bool__(self) -> bool:  # pragma: no cover - trivial override
        return False


def _verify_json(expected: dict[str, Any]) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:
        assert isinstance(result, Syntax)
        expected_text = json.dumps(expected, indent=formatter.indent, sort_keys=True)
        assert result.code == expected_text

    return _inner


def _verify_yaml(expected: dict[str, Any]) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:
        assert isinstance(result, Syntax)
        expected_text = yaml.dump(
            expected,
            indent=formatter.indent,
            sort_keys=True,
            default_flow_style=False,
        )
        assert result.code == expected_text
        assert yaml.safe_load(result.code) == expected

    return _inner


def _verify_markdown_lines(expected_lines: list[str]) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, str)
        assert result.splitlines() == expected_lines

    return _inner


def _verify_empty_table(expected_title: str) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, Table)
        assert result.title == expected_title
        assert len(result.columns) == 0
        assert len(result.rows) == 0

    return _inner


def _verify_table_rows(expected_cells: dict[str, list[str]]) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, Table)
        headers = [column.header for column in result.columns]
        assert headers == list(expected_cells.keys())
        for column in result.columns:
            assert column._cells == expected_cells[column.header]

    return _inner


def _verify_panel_with_table(
    expected_title: str, expected_columns: list[str], expected_rows: list[list[str]]
) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, Panel)
        assert result.title == expected_title
        assert isinstance(result.renderable, Table)
        table = result.renderable
        assert [column.header for column in table.columns] == expected_columns
        for column, column_values in zip(table.columns, zip(*expected_rows), strict=True):
            assert list(column._cells) == list(column_values)

    return _inner


def _verify_panel_with_text(expected_title: str, expected_plain: str) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, Panel)
        assert result.title == expected_title
        assert isinstance(result.renderable, Text)
        assert result.renderable.plain == expected_plain

    return _inner


def _verify_rich_table(expected_columns: list[str]) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, Table)
        assert [column.header for column in result.columns] == expected_columns

    return _inner


def _verify_text(expected_text: str) -> CaseVerifier:
    def _inner(result: Any, formatter: OutputFormatter) -> None:  # noqa: ARG001
        assert isinstance(result, str)
        assert result == expected_text

    return _inner


STRUCTURED_SCENARIOS = (
    StructuredScenario(
        id="json-syntax",
        output_format=OutputFormat.JSON,
        data={"b": 2, "a": 1},
        title=None,
        with_console=True,
        verifier=_verify_json({"b": 2, "a": 1}),
    ),
    StructuredScenario(
        id="yaml-syntax",
        output_format=OutputFormat.YAML,
        data={"nest": {"key": "value"}},
        title=None,
        with_console=True,
        verifier=_verify_yaml({"nest": {"key": "value"}}),
    ),
    StructuredScenario(
        id="markdown-dict",
        output_format=OutputFormat.MARKDOWN,
        data={
            "metadata": {"status": "ready", "owner": "qa"},
            "notes": ["first", "second"],
        },
        title="Report",
        with_console=False,
        verifier=_verify_markdown_lines(
            [
                "# Report",
                "",
                "## metadata",
                "",
                "- **status**: ready",
                "- **owner**: qa",
                "",
                "## notes",
                "",
                "- first",
                "- second",
            ]
        ),
    ),
    StructuredScenario(
        id="markdown-list",
        output_format=OutputFormat.MARKDOWN,
        data=[{"name": "alpha", "count": 1}, "orphan"],
        title="Items",
        with_console=False,
        verifier=_verify_markdown_lines(
            [
                "# Items",
                "",
                "- **name**: alpha",
                "- **count**: 1",
                "- orphan",
            ]
        ),
    ),
    StructuredScenario(
        id="table-empty-list",
        output_format=OutputFormat.TABLE,
        data=[],
        title="Empty Title",
        with_console=False,
        verifier=_verify_empty_table("Empty Title"),
    ),
    StructuredScenario(
        id="table-heterogeneous",
        output_format=OutputFormat.TABLE,
        data=[
            {"name": "alpha", "details": {"level": 1}},
            {"name": "beta", "count": [1, 2]},
        ],
        title="Records",
        with_console=False,
        verifier=_verify_table_rows(
            {
                "count": ["", "[\n  1,\n  2\n]"],
                "details": ["{\n  \"level\": 1\n}", ""],
                "name": ["alpha", "beta"],
            }
        ),
    ),
    StructuredScenario(
        id="rich-dict",
        output_format=OutputFormat.RICH,
        data={"name": "DevSynth", "status": "ready"},
        title="Metadata",
        with_console=False,
        verifier=_verify_panel_with_table(
            "Metadata", ["Key", "Value"], [["name", "DevSynth"], ["status", "ready"]]
        ),
    ),
    StructuredScenario(
        id="rich-list-of-dicts",
        output_format=OutputFormat.RICH,
        data=[{"name": "alpha", "value": 1}, {"name": "beta", "value": 2}],
        title="Records",
        with_console=False,
        verifier=_verify_rich_table(["name", "value"]),
    ),
    StructuredScenario(
        id="rich-bullet-panel",
        output_format=OutputFormat.RICH,
        data=["alpha", "beta"],
        title="List",
        with_console=False,
        verifier=_verify_panel_with_text("List", "• alpha\n• beta\n"),
    ),
    StructuredScenario(
        id="rich-falsy-list",
        output_format=OutputFormat.RICH,
        data=FalsyList(["ignored"]),
        title="Maybe Empty",
        with_console=False,
        verifier=_verify_panel_with_text("Maybe Empty", "(empty list)"),
    ),
    StructuredScenario(
        id="text-scalar",
        output_format=OutputFormat.TEXT,
        data="event complete",
        title="Scalar",
        with_console=False,
        verifier=_verify_text("# Scalar\n\nevent complete"),
    ),
)


@pytest.mark.parametrize(
    "scenario",
    STRUCTURED_SCENARIOS,
    ids=[scenario.id for scenario in STRUCTURED_SCENARIOS],
)
def test_format_structured_exercises_all_branches(
    scenario: StructuredScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise every branch of format_structured with deterministic sanitization."""

    monkeypatch.setattr(OutputFormatter, "sanitize_output", lambda self, text: str(text))
    formatter = OutputFormatter()

    if scenario.with_console:
        formatter.set_console(Console(width=80, record=True))

    result = formatter.format_structured(
        scenario.data,
        scenario.output_format,
        title=scenario.title,
    )

    scenario.verifier(result, formatter)


def test_format_table_and_list_preserve_sanitized_complex_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """format_table/list should respect sanitizer output and updated formatting options."""

    formatter = OutputFormatter()
    sanitized_inputs: list[str] = []

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        sanitized_inputs.append(text)
        return f"SAN:{text}:"

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    formatter.set_format_options(indent=4, spacing=3, line_width=72)

    assert formatter.indent == 4
    assert formatter.spacing == 3
    assert formatter.line_width == 72

    table_output = formatter.format_table(
        {
            "<key>": "<div>payload</div>",
            "nested": {"items": ["<a>"]},
        },
        title="Details",
    )

    assert table_output.startswith("# Details")
    assert "SAN:<key>:" in table_output
    assert "SAN:<div>payload</div>:" in table_output
    assert "SAN:{'items': ['<a>']}:" in table_output

    list_output = formatter.format_list(
        ["<script>alert(1)</script>", {"inner": "<tag>"}],
        title="Entries",
        bullet="-",
    )

    assert list_output.startswith("# Entries")
    assert "- SAN:<script>alert(1)</script>:" in list_output
    assert "- SAN:{'inner': '<tag>'}:" in list_output

    expected_inputs = [
        "<key>",
        "<div>payload</div>",
        "nested",
        "{'items': ['<a>']}",
        "<script>alert(1)</script>",
        "{'inner': '<tag>'}",
    ]
    assert sanitized_inputs == expected_inputs

    json_text = formatter.format_structured({"a": 1}, OutputFormat.JSON)
    assert json_text == json.dumps({"a": 1}, indent=4, sort_keys=True)


def test_command_output_unknown_extension_and_highlight_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown command extensions fall back to defaults and highlights route through print."""

    formatter = OutputFormatter(default_format=OutputFormat.JSON)

    fallback = formatter.format_command_output({"value": 5}, format_name="custom.bin")
    assert isinstance(fallback, str)
    assert json.loads(fallback) == {"value": 5}

    printed: list[tuple[Any, str | None]] = []

    class SpyConsole:
        def print(self, renderable: Any, style: str | None = None) -> None:
            printed.append((renderable, style))

    formatter.set_console(SpyConsole())

    def fake_sanitize(self: OutputFormatter, text: str) -> str:
        return f"SAN:{text}"

    monkeypatch.setattr(OutputFormatter, "sanitize_output", fake_sanitize)

    formatter.display("attention", highlight=True)

    assert printed, "display should route highlight panels through the console"
    renderable, style = printed[0]
    assert isinstance(renderable, Panel)
    assert renderable.renderable == "SAN:attention"
    assert style == "bold white on blue"
