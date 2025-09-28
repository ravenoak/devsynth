import json

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devsynth.application.cli.command_output_formatter import (
    CommandOutputStyle,
    CommandOutputType,
    StandardizedOutputFormatter,
)
from devsynth.application.cli.models import CommandDisplay


@pytest.fixture()
def formatter():
    # Use a Console with a null file to avoid writing to stdout during tests
    return StandardizedOutputFormatter(console=Console(file=None))


@pytest.mark.fast
def test_format_message_minimal_returns_text(formatter):
    out = formatter.format_message("hello", output_style=CommandOutputStyle.MINIMAL)
    assert isinstance(out, CommandDisplay)
    assert isinstance(out.renderable, Text)
    assert "hello" in out.renderable.plain


@pytest.mark.fast
def test_format_message_simple_highlight_false_returns_str(formatter):
    out = formatter.format_message(
        "hello", output_style=CommandOutputStyle.SIMPLE, highlight=False
    )
    assert isinstance(out, CommandDisplay)
    assert isinstance(out.renderable, str)
    assert out.renderable == "hello"


@pytest.mark.fast
def test_format_message_standard_with_markup_returns_panel_passthrough(formatter):
    # Contains Rich markup [bold]
    out = formatter.format_message(
        "[bold]hi[/bold]", output_style=CommandOutputStyle.STANDARD
    )
    assert isinstance(out, CommandDisplay)
    assert isinstance(out.renderable, Panel)


@pytest.mark.fast
def test_format_table_with_dict_and_list(formatter):
    tbl1 = formatter.format_table({"a": 1, "b": {"x": 2}})
    tbl2 = formatter.format_table([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    assert isinstance(tbl1, CommandDisplay)
    assert isinstance(tbl2, CommandDisplay)
    assert hasattr(tbl1.renderable, "add_row") and hasattr(tbl2.renderable, "add_row")


@pytest.mark.fast
def test_format_table_with_unsupported_type_falls_back(formatter):
    tbl = formatter.format_table(42)
    assert isinstance(tbl, CommandDisplay)
    assert any(col.header == "Data" for col in tbl.renderable.columns)


@pytest.mark.fast
def test_format_list_variants(formatter):
    items = ["one", "two"]
    minimal = formatter.format_list(items, output_style=CommandOutputStyle.MINIMAL)
    simple = formatter.format_list(items, output_style=CommandOutputStyle.SIMPLE)
    standard = formatter.format_list(items, output_style=CommandOutputStyle.STANDARD)
    assert isinstance(minimal, CommandDisplay)
    assert isinstance(simple, CommandDisplay)
    assert isinstance(standard, CommandDisplay)
    assert isinstance(minimal.renderable, str)
    assert isinstance(simple.renderable, Text)
    assert isinstance(standard.renderable, Panel)


@pytest.mark.fast
def test_format_code_variants(formatter):
    code = "print('hi')"
    minimal = formatter.format_code(code, output_style=CommandOutputStyle.MINIMAL)
    simple = formatter.format_code(code, output_style=CommandOutputStyle.SIMPLE)
    standard = formatter.format_code(code, output_style=CommandOutputStyle.STANDARD)
    assert isinstance(minimal, CommandDisplay)
    # SIMPLE returns a Syntax object rendered via Rich
    from rich.syntax import Syntax

    assert isinstance(simple, CommandDisplay)
    assert isinstance(standard, CommandDisplay)
    assert isinstance(minimal.renderable, str)
    assert isinstance(simple.renderable, Syntax)
    assert isinstance(standard.renderable, Panel)


@pytest.mark.fast
def test_format_help_variants(formatter):
    examples = [{"description": "Run", "command": "devsynth run"}]
    options = [{"name": "--opt", "description": "Option desc", "default": "x"}]
    minimal = formatter.format_help(
        command="cmd",
        description="desc",
        usage="cmd --opt x",
        examples=examples,
        options=options,
        output_style=CommandOutputStyle.MINIMAL,
    )
    simple = formatter.format_help(
        command="cmd",
        description="desc",
        usage="cmd --opt x",
        examples=examples,
        options=options,
        output_style=CommandOutputStyle.SIMPLE,
    )
    standard = formatter.format_help(
        command="cmd",
        description="desc",
        usage="cmd --opt x",
        examples=examples,
        options=options,
        output_style=CommandOutputStyle.STANDARD,
    )

    assert isinstance(minimal, CommandDisplay)
    assert isinstance(simple, CommandDisplay)
    assert isinstance(standard, CommandDisplay)
    assert isinstance(minimal.renderable, str)
    assert isinstance(simple.renderable, Text)
    assert isinstance(standard.renderable, Panel)


@pytest.mark.fast
def test_display_does_not_raise(formatter):
    # Ensure display() calls console.print without raising
    formatter.display("ok", output_type=CommandOutputType.SUCCESS)
