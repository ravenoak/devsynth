import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from devsynth.application.cli.autocomplete import get_completions, complete_command, command_autocomplete, file_path_autocomplete, get_command_help, get_all_commands_help, COMMANDS, COMMAND_DESCRIPTIONS, COMMAND_EXAMPLES

@pytest.mark.medium
def test_get_completions_returns_expected_result():
    """Test that get_completions returns commands that start with the incomplete string.

ReqID: N/A"""
    assert set(get_completions('')) == set(COMMANDS)
    assert set(get_completions('i')) == {cmd for cmd in COMMANDS if cmd.startswith('i')}
    assert get_completions('init') == ['init']
    assert get_completions('xyz') == []

@pytest.mark.medium
def test_complete_command_returns_expected_result():
    """Test that complete_command returns the completed command if there's a unique match.

ReqID: N/A"""
    assert complete_command('init') == 'init'
    incomplete = 'i'
    matches = [cmd for cmd in COMMANDS if cmd.startswith(incomplete)]
    if len(matches) > 1:
        assert complete_command(incomplete) == incomplete
    else:
        assert complete_command(incomplete) == matches[0]
    assert complete_command('xyz') == 'xyz'

@pytest.mark.medium
def test_command_autocomplete_returns_expected_result():
    """Test that command_autocomplete returns commands that start with the incomplete string.

ReqID: N/A"""
    ctx = MagicMock()
    assert set(command_autocomplete(ctx, '')) == set(COMMANDS)
    assert set(command_autocomplete(ctx, 'i')) == {cmd for cmd in COMMANDS if cmd.startswith('i')}
    assert command_autocomplete(ctx, 'init') == ['init']
    assert command_autocomplete(ctx, 'xyz') == []

@pytest.mark.medium
def test_file_path_autocomplete_returns_expected_result():
    """Test that file_path_autocomplete returns file paths that match the incomplete string.

ReqID: N/A"""
    ctx = MagicMock()
    with patch('devsynth.application.cli.autocomplete.Path') as mock_path:
        mock_cwd = MagicMock()
        mock_path.cwd.return_value = mock_cwd
        mock_file1 = MagicMock()
        mock_file1.name = 'file1.txt'
        mock_file1.__str__.return_value = 'file1.txt'
        mock_file2 = MagicMock()
        mock_file2.name = 'file2.txt'
        mock_file2.__str__.return_value = 'file2.txt'
        mock_dir1 = MagicMock()
        mock_dir1.name = 'dir1'
        mock_dir1.__str__.return_value = 'dir1'
        mock_cwd.iterdir.return_value = [mock_file1, mock_file2, mock_dir1]
        result = file_path_autocomplete(ctx, '')
        assert set(result) == {'file1.txt', 'file2.txt', 'dir1'}
        result = file_path_autocomplete(ctx, 'file')
        assert set(result) == {'file1.txt', 'file2.txt'}
        result = file_path_autocomplete(ctx, 'dir')
        assert set(result) == {'dir1'}
        result = file_path_autocomplete(ctx, 'xyz')
        assert result == []
        mock_path.side_effect = None
        mock_path.reset_mock()
        path_instance = MagicMock()
        mock_path.return_value = path_instance
        parent_dir = MagicMock()
        path_instance.parent = parent_dir
        path_instance.name = 'file'
        parent_dir.is_absolute.return_value = False
        mock_cwd.__truediv__.return_value = parent_dir
        mock_file1 = MagicMock()
        mock_file1.name = 'file1.txt'
        mock_file1.__str__.return_value = 'dir1/file1.txt'
        mock_file2 = MagicMock()
        mock_file2.name = 'file2.txt'
        mock_file2.__str__.return_value = 'dir1/file2.txt'
        parent_dir.iterdir.return_value = [mock_file1, mock_file2]
        result = file_path_autocomplete(ctx, 'dir1/file')
        assert set(result) == {'dir1/file1.txt', 'dir1/file2.txt'}

@pytest.mark.medium
def test_get_command_help_returns_expected_result():
    """Test that get_command_help returns detailed help text for a command.

ReqID: N/A"""
    command = next(iter(COMMAND_EXAMPLES.keys()))
    help_text = get_command_help(command)
    assert f'Command: {command}' in help_text
    assert COMMAND_DESCRIPTIONS.get(command, '') in help_text
    for example in COMMAND_EXAMPLES.get(command, []):
        assert example in help_text
    command_with_desc = next((cmd for cmd in COMMAND_DESCRIPTIONS if cmd not in COMMAND_EXAMPLES), None)
    if command_with_desc:
        help_text = get_command_help(command_with_desc)
        assert f'Command: {command_with_desc}' in help_text
        assert COMMAND_DESCRIPTIONS.get(command_with_desc, '') in help_text
        assert 'Examples:' not in help_text
    help_text = get_command_help('nonexistent')
    assert 'Command: nonexistent' in help_text
    assert 'No description available' in help_text

@pytest.mark.medium
def test_get_all_commands_help_returns_expected_result():
    """Test that get_all_commands_help returns help text for all available commands.

ReqID: N/A"""
    help_text = get_all_commands_help()
    assert 'Available Commands:' in help_text
    for command in COMMANDS:
        assert command in help_text
        assert COMMAND_DESCRIPTIONS.get(command, 'No description available') in help_text