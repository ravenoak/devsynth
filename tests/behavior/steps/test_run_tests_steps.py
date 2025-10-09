"""Step definitions for run-tests behavior tests."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

# Resolve repository root (three levels up from this steps file)
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
)


@pytest.fixture
def command_result() -> dict[str, str]:
    """Store information about a command execution."""
    return {}


@given(parsers.parse('the environment variable "{name}" is "{value}"'))
def set_env(name: str, value: str, monkeypatch) -> None:
    """Set an environment variable for the command invocation."""
    monkeypatch.setenv(name, value)


@given(parsers.parse('the environment variable "{name}" is unset'))
def unset_env(name: str, monkeypatch) -> None:
    """Remove an environment variable for the command invocation."""
    monkeypatch.delenv(name, raising=False)


@when('I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel"')
def invoke_run_tests(command_result: dict[str, str]) -> None:
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


@when('I invoke "devsynth run-tests --target unit-tests --speed=fast"')
def invoke_run_tests_parallel(command_result: dict[str, str]) -> None:
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
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@when(
    'I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --segment --segment-size=1"'
)
def invoke_run_tests_segment(command_result: dict[str, str]) -> None:
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
        "--segment",
        "--segment-size",
        "1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@when(
    'I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --feature experimental"'
)
def invoke_run_tests_feature(command_result: dict[str, str]) -> None:
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
        "--feature",
        "experimental",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@when(
    'I invoke "devsynth run-tests --speed=fast --speed=medium --report --no-parallel"'
)
def invoke_run_tests_fast_medium(command_result: dict[str, str]) -> None:
    env = os.environ.copy()
    env.setdefault("DEVSYNTH_NO_FILE_LOGGING", "1")
    env.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")
    cmd = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--speed=fast",
        "--speed=medium",
        "--report",
        "--no-parallel",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@when(
    'I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1"'
)
def invoke_run_tests_maxfail(command_result: dict[str, str]) -> None:
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
        "--maxfail=1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@then("the command should succeed")
def command_succeeds(command_result: dict[str, str]) -> None:
    assert command_result.get("exit_code") == 0


@then("the command should fail")
def command_fails(command_result: dict[str, str]) -> None:
    assert command_result.get("exit_code") != 0


@then("the output should mention no tests were run")
def output_mentions_no_tests(command_result: dict[str, str]) -> None:
    output = command_result.get("output", "").lower()
    assert "collected 0 items" in output or "no tests ran" in output


@then("the output should not contain xdist assertions")
def output_no_xdist_assertions(command_result: dict[str, str]) -> None:
    output = command_result.get("output", "")
    assert "INTERNALERROR" not in output


@then(parsers.parse('the coverage report "{path}" should exist'))
def coverage_report_exists(path: str) -> None:
    report_path = Path(_REPO_ROOT) / path
    assert report_path.exists(), f"Coverage report {path} does not exist"
    assert report_path.stat().st_size > 0, f"Coverage report {path} is empty"


@then(
    parsers.parse('the coverage report speeds should include "{speed1}" and "{speed2}"')
)
def coverage_report_includes_speeds(speed1: str, speed2: str) -> None:
    report_path = Path(_REPO_ROOT) / "test_reports" / "coverage.json"
    with report_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    speeds = set(payload.get("meta", {}).get("speeds", []))
    assert speed1 in speeds, f"Expected {speed1} in coverage speeds: {sorted(speeds)}"
    assert speed2 in speeds, f"Expected {speed2} in coverage speeds: {sorted(speeds)}"


@when(
    'I invoke "devsynth run-tests --target unit-tests --speed=fast --no-parallel --report"'
)
def invoke_run_tests_report(command_result: dict[str, str]) -> None:
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
        "--report",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr


@then("the output should mention html report path")
def output_mentions_html_report_path(command_result: dict[str, str]) -> None:
    output = command_result.get("output", "").lower()
    assert "html report available under" in output


@when('I invoke "devsynth run-tests --smoke --speed=fast --no-parallel"')
def invoke_run_tests_smoke(command_result: dict[str, str]) -> None:
    env = os.environ.copy()
    env.setdefault("DEVSYNTH_NO_FILE_LOGGING", "1")
    env.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")
    cmd = [
        "poetry",
        "run",
        "devsynth",
        "run-tests",
        "--smoke",
        "--speed=fast",
        "--no-parallel",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    command_result["exit_code"] = result.returncode
    command_result["output"] = result.stdout + result.stderr
