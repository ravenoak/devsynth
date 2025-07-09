"""Tests for the enhanced progress indicators in the CLI application."""
import pytest
from unittest.mock import patch, MagicMock, call
from rich.console import Console
from devsynth.application.cli.progress import EnhancedProgressIndicator, ProgressManager, create_enhanced_progress, create_task_table, run_with_progress
from devsynth.interface.ux_bridge import UXBridge


class TestEnhancedProgressIndicator:
    """Tests for the EnhancedProgressIndicator class.

ReqID: N/A"""

    @pytest.fixture
    def console(self):
        """Create a console that writes to /dev/null to avoid cluttering test output."""
        return Console(file=open('/dev/null', 'w'))

    @pytest.fixture
    def indicator(self, console):
        """Create an EnhancedProgressIndicator for testing."""
        indicator = EnhancedProgressIndicator(console, 'Main task', 100)
        original_add_task = indicator._progress.add_task
        original_update = indicator._progress.update
        add_task_calls = []
        update_calls = []

        def mock_add_task(description, total=100):
            add_task_calls.append((description, total))
            return f'task_{len(add_task_calls)}'

        def mock_update(task_id, **kwargs):
            update_calls.append((task_id, kwargs))
        indicator._progress.add_task = mock_add_task
        indicator._progress.update = mock_update
        indicator.add_task_calls = add_task_calls
        indicator.update_calls = update_calls
        yield indicator
        indicator._progress.add_task = original_add_task
        indicator._progress.update = original_update
        console.file.close()

    def test_add_subtask_succeeds(self, indicator):
        """Test adding a subtask to the progress indicator.

ReqID: N/A"""
        subtask_id = indicator.add_subtask('Subtask 1', 50)
        assert len(indicator.add_task_calls) == 1
        assert indicator.add_task_calls[0][0] == '  ↳ Subtask 1'
        assert indicator.add_task_calls[0][1] == 50
        assert 'Subtask 1' in indicator._subtasks
        assert indicator._subtasks['Subtask 1'] == 'task_1'
        assert subtask_id == 'Subtask 1'

    def test_update_subtask_succeeds(self, indicator):
        """Test updating a subtask's progress.

ReqID: N/A"""
        subtask_id = indicator.add_subtask('Subtask 1', 50)
        indicator.update_subtask(subtask_id, 10, 'Updated subtask')
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == 'task_1'
        assert indicator.update_calls[0][1]['advance'] == 10
        assert indicator.update_calls[0][1]['description'
            ] == '  ↳ Updated subtask'

    def test_complete_subtask_succeeds(self, indicator):
        """Test completing a subtask.

ReqID: N/A"""
        subtask_id = indicator.add_subtask('Subtask 1', 50)
        indicator.complete_subtask(subtask_id)
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == 'task_1'
        assert indicator.update_calls[0][1]['completed'] is True

    def test_update_succeeds(self, indicator):
        """Test updating the main task's progress.

ReqID: N/A"""
        indicator.update(advance=10, description='Updated main task')
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == indicator._task
        assert indicator.update_calls[0][1]['advance'] == 10
        assert indicator.update_calls[0][1]['description'
            ] == 'Updated main task'

    def test_complete_succeeds(self, indicator):
        """Test completing the main task and all subtasks.

ReqID: N/A"""
        subtask1_id = indicator.add_subtask('Subtask 1', 50)
        subtask2_id = indicator.add_subtask('Subtask 2', 30)
        indicator.complete()
        assert len(indicator.update_calls) == 3
        subtask_calls = [call for call in indicator.update_calls if call[0] !=
            indicator._task]
        assert len(subtask_calls) == 2
        for call in subtask_calls:
            assert call[1]['completed'] is True
        main_task_calls = [call for call in indicator.update_calls if call[
            0] == indicator._task]
        assert len(main_task_calls) == 1
        assert main_task_calls[0][1]['completed'] is True


class TestProgressManager:
    """Tests for the ProgressManager class.

ReqID: N/A"""

    @pytest.fixture
    def bridge(self):
        """Create a mock UXBridge for testing."""
        bridge = MagicMock(spec=UXBridge)
        bridge.create_progress.return_value = MagicMock()
        return bridge

    @pytest.fixture
    def manager(self, bridge):
        """Create a ProgressManager for testing."""
        return ProgressManager(bridge)

    def test_create_progress_succeeds(self, manager, bridge):
        """Test creating a progress indicator.

ReqID: N/A"""
        indicator = manager.create_progress('task1', 'Task 1', 100)
        bridge.create_progress.assert_called_once_with('Task 1', total=100)
        assert manager.indicators['task1'] == indicator

    def test_get_progress_succeeds(self, manager, bridge):
        """Test getting a progress indicator.

ReqID: N/A"""
        indicator = manager.create_progress('task1', 'Task 1', 100)
        retrieved = manager.get_progress('task1')
        assert retrieved == indicator
        assert manager.get_progress('non-existent') is None

    def test_update_progress_succeeds(self, manager, bridge):
        """Test updating a progress indicator.

ReqID: N/A"""
        indicator = manager.create_progress('task1', 'Task 1', 100)
        manager.update_progress('task1', 10, 'Updated task')
        indicator.update.assert_called_once_with(advance=10, description=
            'Updated task')
        manager.update_progress('non-existent', 10, 'Updated task')

    def test_complete_progress_succeeds(self, manager, bridge):
        """Test completing a progress indicator.

ReqID: N/A"""
        indicator = manager.create_progress('task1', 'Task 1', 100)
        manager.complete_progress('task1')
        indicator.complete.assert_called_once()
        assert 'task1' not in manager.indicators
        manager.complete_progress('non-existent')


def test_create_enhanced_progress_succeeds():
    """Test creating an enhanced progress indicator.

ReqID: N/A"""
    console = Console(file=open('/dev/null', 'w'))
    try:
        indicator = create_enhanced_progress(console, 'Task', 100)
        assert isinstance(indicator, EnhancedProgressIndicator)
        assert indicator._progress.console == console
        assert indicator._task is not None
    finally:
        console.file.close()


def test_create_task_table_succeeds():
    """Test creating a task table.

ReqID: N/A"""
    tasks = [{'name': 'Task 1', 'status': 'Complete', 'description':
        'Description 1'}, {'name': 'Task 2', 'status': 'In Progress',
        'description': 'Description 2'}, {'name': 'Task 3', 'status':
        'Failed', 'description': 'Description 3'}]
    table = create_task_table(tasks, 'Test Tasks')
    assert table.title == 'Test Tasks'
    assert len(table.columns) == 3
    assert table.columns[0].header == 'Task'
    assert table.columns[1].header == 'Status'
    assert table.columns[2].header == 'Description'


def test_run_with_progress_succeeds():
    """Test running a task with a progress indicator.

ReqID: N/A"""
    bridge = MagicMock(spec=UXBridge)
    progress = MagicMock()
    bridge.create_progress.return_value = progress

    def task_fn():
        return 'result'
    result = run_with_progress('Task', task_fn, bridge, 100, [{'name':
        'Subtask 1', 'total': 50}, {'name': 'Subtask 2', 'total': 30}])
    bridge.create_progress.assert_called_once_with('Task', total=100)
    assert result == 'result'
    progress.complete.assert_called_once()
