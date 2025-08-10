"""Tests for sandboxed tool execution."""

import subprocess
from pathlib import Path

import pytest

from devsynth.agents.tools import ToolRegistry


def bad_file_tool() -> None:
    with open(Path("/etc/passwd"), "r", encoding="utf-8"):
        pass


def bad_shell_tool() -> None:
    subprocess.run(["echo", "hi"], check=False)


def good_shell_tool() -> str:
    result = subprocess.run(["echo", "hi"], check=False, capture_output=True, text=True)
    return result.stdout.strip()


def test_file_access_restricted() -> None:
    registry = ToolRegistry()
    registry.register(
        "bad_file",
        bad_file_tool,
        description="attempts to read outside project",
        parameters={},
    )
    func = registry.get("bad_file")
    with pytest.raises(PermissionError):
        func()


def test_shell_commands_blocked() -> None:
    registry = ToolRegistry()
    registry.register(
        "bad_shell",
        bad_shell_tool,
        description="attempts shell command",
        parameters={},
    )
    func = registry.get("bad_shell")
    with pytest.raises(PermissionError):
        func()


def test_shell_commands_allowed() -> None:
    registry = ToolRegistry()
    registry.register(
        "good_shell",
        good_shell_tool,
        description="allowed shell command",
        parameters={},
        allow_shell=True,
    )
    func = registry.get("good_shell")
    assert func() == "hi"
