"""Tests for the tool registry."""

import pytest

from devsynth.agents.tools import ToolRegistry


def sample_tool(x: int) -> int:
    return x + 1


@pytest.mark.fast
def test_register_and_get_tool() -> None:
    registry = ToolRegistry()
    registry.register(
        "adder",
        sample_tool,
        description="Add one to the input",
        parameters={"x": {"type": "integer"}},
    )

    func = registry.get("adder")
    assert func is not None
    assert func(1) == 2
    metadata = registry.get_metadata("adder")
    assert metadata == {
        "description": "Add one to the input",
        "parameters": {"x": {"type": "integer"}},
    }


@pytest.mark.fast
def test_unknown_tool_returns_none() -> None:
    registry = ToolRegistry()
    assert registry.get("missing") is None
    assert registry.get_metadata("missing") is None


@pytest.mark.fast
def test_export_for_openai_formats_tools() -> None:
    registry = ToolRegistry()
    registry.register(
        "adder",
        sample_tool,
        description="Add one to the input",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
    )
    exported = registry.export_for_openai()
    assert exported == [
        {
            "type": "function",
            "function": {
                "name": "adder",
                "description": "Add one to the input",
                "parameters": {
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                },
            },
        }
    ]
