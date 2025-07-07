import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from devsynth.application.cli.autocomplete import (
    get_completions,
    complete_command,
    command_autocomplete,
    file_path_autocomplete,
    get_command_help,
    get_all_commands_help,
    COMMANDS,
    COMMAND_DESCRIPTIONS,
    COMMAND_EXAMPLES,
)


def test_get_completions():
    """Test that get_completions returns commands that start with the incomplete string."""
    # Test with empty string (should return all commands)
    assert set(get_completions("")) == set(COMMANDS)
    
    # Test with a prefix that matches multiple commands
    assert set(get_completions("i")) == {cmd for cmd in COMMANDS if cmd.startswith("i")}
    
    # Test with a prefix that matches a single command
    assert get_completions("init") == ["init"]
    
    # Test with a prefix that doesn't match any command
    assert get_completions("xyz") == []


def test_complete_command():
    """Test that complete_command returns the completed command if there's a unique match."""
    # Test with a prefix that matches a single command
    assert complete_command("init") == "init"
    
    # Test with a prefix that matches multiple commands
    incomplete = "i"
    matches = [cmd for cmd in COMMANDS if cmd.startswith(incomplete)]
    if len(matches) > 1:
        assert complete_command(incomplete) == incomplete
    else:
        assert complete_command(incomplete) == matches[0]
    
    # Test with a prefix that doesn't match any command
    assert complete_command("xyz") == "xyz"


def test_command_autocomplete():
    """Test that command_autocomplete returns commands that start with the incomplete string."""
    # Mock Typer context
    ctx = MagicMock()
    
    # Test with empty string (should return all commands)
    assert set(command_autocomplete(ctx, "")) == set(COMMANDS)
    
    # Test with a prefix that matches multiple commands
    assert set(command_autocomplete(ctx, "i")) == {cmd for cmd in COMMANDS if cmd.startswith("i")}
    
    # Test with a prefix that matches a single command
    assert command_autocomplete(ctx, "init") == ["init"]
    
    # Test with a prefix that doesn't match any command
    assert command_autocomplete(ctx, "xyz") == []


def test_file_path_autocomplete():
    """Test that file_path_autocomplete returns file paths that match the incomplete string."""
    # Mock Typer context
    ctx = MagicMock()
    
    # Mock Path.cwd() and Path.iterdir()
    with patch("devsynth.application.cli.autocomplete.Path") as mock_path:
        # Setup mock for current directory
        mock_cwd = MagicMock()
        mock_path.cwd.return_value = mock_cwd
        
        # Setup mock for iterdir
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
        
        # Test with empty string (should return all files and directories)
        result = file_path_autocomplete(ctx, "")
        assert set(result) == {"file1.txt", "file2.txt", "dir1"}
        
        # Test with a prefix that matches a file
        result = file_path_autocomplete(ctx, "file")
        assert set(result) == {"file1.txt", "file2.txt"}
        
        # Test with a prefix that matches a directory
        result = file_path_autocomplete(ctx, "dir")
        assert set(result) == {"dir1"}
        
        # Test with a prefix that doesn't match any file or directory
        result = file_path_autocomplete(ctx, "xyz")
        assert result == []
        
        # Test with a path containing a separator
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.parent = Path("dir1")
        mock_path_obj.name = "file"
        
        mock_parent_dir = MagicMock()
        mock_path.side_effect = lambda x: mock_parent_dir if x == Path("dir1") else mock_path_obj
        mock_parent_dir.is_absolute.return_value = False
        mock_parent_dir.__truediv__.return_value = mock_parent_dir
        
        mock_subfile1 = MagicMock()
        mock_subfile1.name = "file1.txt"
        mock_subfile1.__str__.return_value = "dir1/file1.txt"
        
        mock_subfile2 = MagicMock()
        mock_subfile2.name = "file2.txt"
        mock_subfile2.__str__.return_value = "dir1/file2.txt"
        
        mock_parent_dir.iterdir.return_value = [mock_subfile1, mock_subfile2]
        
        result = file_path_autocomplete(ctx, "dir1/file")
        assert set(result) == {"dir1/file1.txt", "dir1/file2.txt"}


def test_get_command_help():
    """Test that get_command_help returns detailed help text for a command."""
    # Test with a command that has description and examples
    command = next(iter(COMMAND_EXAMPLES.keys()))
    help_text = get_command_help(command)
    assert f"Command: {command}" in help_text
    assert COMMAND_DESCRIPTIONS.get(command, "") in help_text
    for example in COMMAND_EXAMPLES.get(command, []):
        assert example in help_text
    
    # Test with a command that has description but no examples
    command_with_desc = next((cmd for cmd in COMMAND_DESCRIPTIONS if cmd not in COMMAND_EXAMPLES), None)
    if command_with_desc:
        help_text = get_command_help(command_with_desc)
        assert f"Command: {command_with_desc}" in help_text
        assert COMMAND_DESCRIPTIONS.get(command_with_desc, "") in help_text
        assert "Examples:" not in help_text
    
    # Test with a command that doesn't exist
    help_text = get_command_help("nonexistent")
    assert "Command: nonexistent" in help_text
    assert "No description available" in help_text


def test_get_all_commands_help():
    """Test that get_all_commands_help returns help text for all available commands."""
    help_text = get_all_commands_help()
    assert "Available Commands:" in help_text
    for command in COMMANDS:
        assert command in help_text
        assert COMMAND_DESCRIPTIONS.get(command, "No description available") in help_text