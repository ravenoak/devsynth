"""Tests for sandboxed tool execution."""

import builtins
import subprocess
import sys
import types
from pathlib import Path

import pytest

if "argon2" not in sys.modules:
    argon2_stub = types.ModuleType("argon2")

    class _PasswordHasher:
        def __init__(self, *args: object, **kwargs: object) -> None: ...

        def hash(self, password: str) -> str:
            return f"argon2:{password}"

        def verify(self, stored_hash: str, password: str) -> bool:
            return stored_hash == self.hash(password)

    argon2_stub.PasswordHasher = _PasswordHasher  # type: ignore[attr-defined]

    exceptions_stub = types.ModuleType("argon2.exceptions")

    class _VerifyMismatchError(Exception):
        pass

    exceptions_stub.VerifyMismatchError = _VerifyMismatchError  # type: ignore[attr-defined]
    argon2_stub.exceptions = exceptions_stub  # type: ignore[attr-defined]

    sys.modules["argon2"] = argon2_stub
    sys.modules["argon2.exceptions"] = exceptions_stub

from devsynth.agents.sandbox import Sandbox
from devsynth.agents.tools import ToolRegistry

pytestmark = pytest.mark.fast


def bad_file_tool() -> None:
    with open(Path("/etc/passwd"), encoding="utf-8"):
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


def test_sandbox_context_restores_hooks(tmp_path: Path) -> None:
    """Sandbox temporarily overrides builtins and subprocess helpers."""

    original_open = builtins.open
    original_run = subprocess.run

    with Sandbox() as sandbox:
        forbidden_path = tmp_path / "forbidden.txt"
        with pytest.raises(PermissionError):
            open(
                forbidden_path, "w", encoding="utf-8"
            )  # noqa: A001 - deliberate builtin use
        with pytest.raises(PermissionError):
            subprocess.run(["echo", "hi"], check=False)

        assert sandbox.allow_shell is False

    assert builtins.open is original_open
    assert subprocess.run is original_run
