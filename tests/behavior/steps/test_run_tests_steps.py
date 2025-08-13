"""Step definitions for run-tests behavior tests."""

import os
import subprocess
from typing import Dict

import pytest
from pytest_bdd import given, parsers, then, when


@pytest.fixture
def command_result() -> Dict[str, str]:
    """Store information about a command execution."""
    return {}


@given(parsers.parse('the environment variable "{name}" is "{value}"'))
def set_env(name: str, value: str, monkeypatch) -> None:
    """Set an environment variable for the command invocation."""
    monkeypatch.setenv(name, value)


@when('I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"')
def invoke_run_tests(command_result: Dict[str, str]) -> None:
    env = os.environ.copy()
    env.setdefault("DEVSYNTH_NO_FILE_LOGGING", "1")
    env.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")
    cmd = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--target",
        "unit-tests",
        "--speed=fast",
        "--no-parallel",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@then("the command should succeed")
def command_succeeds(command_result: Dict[str, str]) -> None:
    assert command_result.get("exit_code") == 0


@then("the command should fail")
def command_fails(command_result: Dict[str, str]) -> None:
    assert command_result.get("exit_code") != 0


@then("the output should mention no tests were run")
def output_mentions_no_tests(command_result: Dict[str, str]) -> None:
    output = command_result.get("output", "").lower()
    assert "collected 0 items" in output or "no tests ran" in output
