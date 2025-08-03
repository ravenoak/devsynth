"""Tests for the tool registry."""

from devsynth.agents.tools import ToolRegistry


def sample_tool(x: int) -> int:
    return x + 1


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


def test_unknown_tool_returns_none() -> None:
    registry = ToolRegistry()
    assert registry.get("missing") is None
    assert registry.get_metadata("missing") is None
