from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.cli import autocomplete as module


@pytest.mark.medium
def test_get_completions_returns_expected_result():
    """Test that get_completions returns commands that start with the incomplete string.

    ReqID: FR-66a"""
    assert set(module.get_completions("")) == set(module.COMMANDS)
    assert set(module.get_completions("i")) == {
        cmd for cmd in module.COMMANDS if cmd.startswith("i")
    }
    assert module.get_completions("init") == ["init"]
    assert module.get_completions("xyz") == []


@pytest.mark.medium
def test_complete_command_returns_expected_result():
    """Test that complete_command returns the completed command if there's a unique match.

    ReqID: FR-66a"""
    assert module.complete_command("init") == "init"
    incomplete = "i"
    matches = [cmd for cmd in module.COMMANDS if cmd.startswith(incomplete)]
    if len(matches) > 1:
        assert module.complete_command(incomplete) == incomplete
    else:
        assert module.complete_command(incomplete) == matches[0]
    assert module.complete_command("xyz") == "xyz"


@pytest.mark.medium
def test_command_autocomplete_returns_expected_result():
    """Test that command_autocomplete returns commands that start with the incomplete string.

    ReqID: FR-66a"""
    ctx = MagicMock()
    assert set(module.command_autocomplete(ctx, "")) == set(module.COMMANDS)
    assert set(module.command_autocomplete(ctx, "i")) == {
        cmd for cmd in module.COMMANDS if cmd.startswith("i")
    }
    assert module.command_autocomplete(ctx, "init") == ["init"]
    assert module.command_autocomplete(ctx, "xyz") == []


@pytest.mark.medium
def test_command_autocomplete_matches_metadata() -> None:
    """Validate CLI suggestions mirror metadata (see autocomplete.py::COMMANDS)."""

    ctx = MagicMock()
    # Empty input should expose the full command roster described in COMMANDS.
    suggestions = module.command_autocomplete(ctx, "")
    assert suggestions == module.get_completions("")
    assert set(suggestions) == set(module.COMMANDS)

    # Ambiguous prefixes should return every matching command with metadata entries.
    ambiguous = module.command_autocomplete(ctx, "co")
    expected_matches = {cmd for cmd in module.COMMANDS if cmd.startswith("co")}
    assert set(ambiguous) == expected_matches
    for cmd in ambiguous:
        assert module.COMMAND_DESCRIPTIONS[cmd]
        # Examples are optional but should exist for all current commands.
        assert cmd in module.COMMAND_EXAMPLES


@pytest.mark.medium
def test_file_path_autocomplete_returns_expected_result():
    """Test that file_path_autocomplete returns file paths that match the incomplete string.

    ReqID: FR-66a"""
    ctx = MagicMock()
    with patch("devsynth.application.cli.autocomplete.Path") as mock_path:
        mock_cwd = MagicMock()
        mock_path.cwd.return_value = mock_cwd
        mock_file1 = MagicMock()
        mock_file1.name = "file1.txt"
        mock_file1.__str__.return_value = "file1.txt"
        mock_file2 = MagicMock()
        mock_file2.name = "file2.txt"
        mock_file2.__str__.return_value = "file2.txt"
        mock_dir1 = MagicMock()
        mock_dir1.name = "dir1"
        mock_dir1.__str__.return_value = "dir1"
        mock_cwd.iterdir.return_value = [mock_file1, mock_file2, mock_dir1]
        result = module.file_path_autocomplete(ctx, "")
        assert set(result) == {"file1.txt", "file2.txt", "dir1"}
        result = module.file_path_autocomplete(ctx, "file")
        assert set(result) == {"file1.txt", "file2.txt"}
        result = module.file_path_autocomplete(ctx, "dir")
        assert set(result) == {"dir1"}
        result = module.file_path_autocomplete(ctx, "xyz")
        assert result == []
        mock_path.side_effect = None
        mock_path.reset_mock()
        path_instance = MagicMock()
        mock_path.return_value = path_instance
        parent_dir = MagicMock()
        path_instance.parent = parent_dir
        path_instance.name = "file"
        parent_dir.is_absolute.return_value = False
        mock_cwd.__truediv__.return_value = parent_dir
        mock_file1 = MagicMock()
        mock_file1.name = "file1.txt"
        mock_file1.__str__.return_value = "dir1/file1.txt"
        mock_file2 = MagicMock()
        mock_file2.name = "file2.txt"
        mock_file2.__str__.return_value = "dir1/file2.txt"
        parent_dir.iterdir.return_value = [mock_file1, mock_file2]
        result = module.file_path_autocomplete(ctx, "dir1/file")
        assert set(result) == {"dir1/file1.txt", "dir1/file2.txt"}


@pytest.mark.medium
def test_file_path_autocomplete_handles_nested_prefixes(monkeypatch, tmp_path):
    """Ensure nested path autocompletion mirrors Path logic (autocomplete.py::file_path_autocomplete)."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    # Build a directory tree with overlapping prefixes to validate ambiguity handling.
    file_alpha = workspace / "alpha.txt"
    file_beta = workspace / "alphabet.txt"
    nested = workspace / "archive"
    nested.mkdir()
    nested_file = nested / "alpha-report.md"
    nested_other = nested / "beta-report.md"
    file_alpha.write_text("alpha")
    file_beta.write_text("beta")
    nested_file.write_text("nested alpha")
    nested_other.write_text("nested beta")

    ctx = MagicMock()

    empty = module.file_path_autocomplete(ctx, "")
    assert {Path(p).name for p in empty} == {
        file_alpha.name,
        file_beta.name,
        nested.name,
    }

    ambiguous_local = module.file_path_autocomplete(ctx, "alp")
    assert {Path(p).name for p in ambiguous_local} == {file_alpha.name, file_beta.name}

    nested_matches = module.file_path_autocomplete(ctx, f"{nested.name}/a")
    assert {Path(p).name for p in nested_matches} == {nested_file.name}


@pytest.mark.medium
def test_get_command_help_returns_expected_result():
    """Test that get_command_help returns detailed help text for a command.

    ReqID: FR-66a"""
    command = next(iter(module.COMMAND_EXAMPLES.keys()))
    help_text = module.get_command_help(command)
    assert f"Command: {command}" in help_text
    assert module.COMMAND_DESCRIPTIONS.get(command, "") in help_text
    for example in module.COMMAND_EXAMPLES.get(command, []):
        assert example in help_text
    command_with_desc = next(
        (
            cmd
            for cmd in module.COMMAND_DESCRIPTIONS
            if cmd not in module.COMMAND_EXAMPLES
        ),
        None,
    )
    if command_with_desc:
        help_text = module.get_command_help(command_with_desc)
        assert f"Command: {command_with_desc}" in help_text
        assert module.COMMAND_DESCRIPTIONS.get(command_with_desc, "") in help_text
        assert "Examples:" not in help_text
    help_text = module.get_command_help("nonexistent")
    assert "Command: nonexistent" in help_text
    assert "No description available" in help_text


@pytest.mark.medium
def test_get_all_commands_help_returns_expected_result():
    """Test that get_all_commands_help returns help text for all available commands.

    ReqID: FR-66a"""

    help_text = module.get_all_commands_help()
    assert "Available Commands:" in help_text
    for command in module.COMMANDS:
        assert command in help_text
        assert (
            module.COMMAND_DESCRIPTIONS.get(command, "No description available")
            in help_text
        )


class _StubCompletion:
    """Simple stand-in for Click's ``ShellComplete``."""

    def __init__(self, script: str) -> None:
        self._script = script

    def source(self) -> str:
        return self._script


@pytest.mark.medium
def test_generate_completion_script_installs_to_target(monkeypatch, tmp_path):
    """Ensure installation writes the generated script to the provided path."""

    expected = "# completion script"
    monkeypatch.setattr(module, "_load_click_command", lambda: object())
    monkeypatch.setattr(
        module,
        "_build_shell_complete",
        lambda shell, command: _StubCompletion(expected),
    )

    target = tmp_path / "devsynth.zsh"
    result = module.generate_completion_script("zsh", install=True, path=target)

    assert result == str(target)
    assert target.read_text() == expected


@pytest.mark.medium
def test_generate_completion_script_uses_home_directory(monkeypatch, tmp_path):
    """Validate the default install path leverages ``Path.home()``."""

    expected = "# bash completion"
    monkeypatch.setattr(module, "_load_click_command", lambda: object())
    monkeypatch.setattr(
        module,
        "_build_shell_complete",
        lambda shell, command: _StubCompletion(expected),
    )
    monkeypatch.setattr(
        module.Path,
        "home",
        classmethod(lambda cls: tmp_path),
    )

    result = module.generate_completion_script("bash", install=True)

    destination = tmp_path / ".devsynth-completion.bash"
    assert result == str(destination)
    assert destination.read_text() == expected


@pytest.mark.medium
def test_generate_completion_script_returns_source(monkeypatch):
    """The helper should return the script text when not installing."""

    expected = "# fish completion"
    monkeypatch.setattr(module, "_load_click_command", lambda: object())
    monkeypatch.setattr(
        module,
        "_build_shell_complete",
        lambda shell, command: _StubCompletion(expected),
    )

    script = module.generate_completion_script("fish", install=False, path=None)
    assert script == expected
