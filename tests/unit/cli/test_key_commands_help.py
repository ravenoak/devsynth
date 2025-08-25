"""Validate key CLI commands exist and provide help without side-effects.

This test aligns with docs/user_guides/cli_command_reference.md by ensuring
that the following commands are available and their --help pages render:
- init
- spec
- test
- code
- run (alias for run-pipeline)
- config (group)
- doctor

The test uses Typer's CliRunner to avoid spawning subprocesses and is marked
as fast and no_network per project guidelines.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app


@pytest.mark.fast
@pytest.mark.no_network
@pytest.mark.parametrize(
    "argv",
    [
        ["init", "--help"],
        ["spec", "--help"],
        ["test", "--help"],
        ["code", "--help"],
        ["run", "--help"],  # alias for run-pipeline
        ["config", "--help"],  # Typer sub-app
        ["doctor", "--help"],
    ],
)
def test_key_commands_help_succeeds(argv: list[str]) -> None:
    """Each key command should return help successfully.

    This is a smoke test only; it does not execute the command logic.
    """
    runner = CliRunner()
    result = runner.invoke(build_app(), argv)
    assert (
        result.exit_code == 0
    ), f"Help failed for {argv}: {result.stdout}\n{result.stderr}"
    # Basic sanity: ensure help header mentions DevSynth or command keyword
    output = result.stdout
    assert output, "No help output produced"
    # Expect either the main banner or the command is named in output
    expected_snippets = [
        "DevSynth CLI",
        f"Usage: devsynth {' '.join(argv[:-1])}".strip(),
        argv[0],
    ]
    assert any(snippet in output for snippet in expected_snippets)
