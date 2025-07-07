"""Tests for the enhanced progress indicators in the CLI application."""

import pytest
from unittest.mock import patch, MagicMock, call
from rich.console import Console

from devsynth.application.cli.progress import (
    EnhancedProgressIndicator,
    ProgressManager,
    create_enhanced_progress,
    create_task_table,
    run_with_progress,
)
from devsynth.interface.ux_bridge import UXBridge


class TestEnhancedProgressIndicator:
    """Tests for the EnhancedProgressIndicator class."""

    @pytest.fixture
    def console(self):
        """Create a console that writes to /dev/null to avoid cluttering test output."""
        return Console(file=open("/dev/null", "w"))

    @pytest.fixture
    def indicator(self, console):
        """Create an EnhancedProgressIndicator for testing."""
        indicator = EnhancedProgressIndicator(console, "Main task", 100)

        # Store the original _progress.add_task and _progress.update methods
        original_add_task = indicator._progress.add_task
        original_update = indicator._progress.update

        # Replace with our own tracking functions
        add_task_calls = []
        update_calls = []

        def mock_add_task(description, total=100):
            add_task_calls.append((description, total))
            return f"task_{len(add_task_calls)}"

        def mock_update(task_id, **kwargs):
            update_calls.append((task_id, kwargs))

        indicator._progress.add_task = mock_add_task
        indicator._progress.update = mock_update

        # Add the tracking lists to the indicator for inspection in tests
        indicator.add_task_calls = add_task_calls
        indicator.update_calls = update_calls

        yield indicator

        # Restore original methods
        indicator._progress.add_task = original_add_task
        indicator._progress.update = original_update

        # Close the console file
        console.file.close()

    def test_add_subtask(self, indicator):
        """Test adding a subtask to the progress indicator."""
        # Add a subtask
        subtask_id = indicator.add_subtask("Subtask 1", 50)

        # Check that add_task was called with the correct parameters
        assert len(indicator.add_task_calls) == 1
        assert indicator.add_task_calls[0][0] == "  ↳ Subtask 1"
        assert indicator.add_task_calls[0][1] == 50

        # Check that the subtask was stored correctly
        assert "Subtask 1" in indicator._subtasks
        assert indicator._subtasks["Subtask 1"] == "task_1"

        # Check that the returned ID is the description
        assert subtask_id == "Subtask 1"

    def test_update_subtask(self, indicator):
        """Test updating a subtask's progress."""
        # Add a subtask
        subtask_id = indicator.add_subtask("Subtask 1", 50)

        # Update the subtask
        indicator.update_subtask(subtask_id, 10, "Updated subtask")

        # Check that update was called with the correct parameters
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == "task_1"
        assert indicator.update_calls[0][1]["advance"] == 10
        assert indicator.update_calls[0][1]["description"] == "  ↳ Updated subtask"

    def test_complete_subtask(self, indicator):
        """Test completing a subtask."""
        # Add a subtask
        subtask_id = indicator.add_subtask("Subtask 1", 50)

        # Complete the subtask
        indicator.complete_subtask(subtask_id)

        # Check that update was called with the correct parameters
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == "task_1"
        assert indicator.update_calls[0][1]["completed"] is True

    def test_update(self, indicator):
        """Test updating the main task's progress."""
        # Update the main task
        indicator.update(advance=10, description="Updated main task")

        # Check that update was called with the correct parameters
        assert len(indicator.update_calls) == 1
        assert indicator.update_calls[0][0] == indicator._task
        assert indicator.update_calls[0][1]["advance"] == 10
        assert indicator.update_calls[0][1]["description"] == "Updated main task"

    def test_complete(self, indicator):
        """Test completing the main task and all subtasks."""
        # Add some subtasks
        subtask1_id = indicator.add_subtask("Subtask 1", 50)
        subtask2_id = indicator.add_subtask("Subtask 2", 30)

        # Complete the main task
        indicator.complete()

        # Check that update was called for each subtask and the main task
        assert len(indicator.update_calls) == 3

        # Check that the subtasks were completed
        subtask_calls = [call for call in indicator.update_calls if call[0] != indicator._task]
        assert len(subtask_calls) == 2
        for call in subtask_calls:
            assert call[1]["completed"] is True

        # Check that the main task was completed
        main_task_calls = [call for call in indicator.update_calls if call[0] == indicator._task]
        assert len(main_task_calls) == 1
        assert main_task_calls[0][1]["completed"] is True


class TestProgressManager:
    """Tests for the ProgressManager class."""

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

    def test_create_progress(self, manager, bridge):
        """Test creating a progress indicator."""
        # Create a progress indicator
        indicator = manager.create_progress("task1", "Task 1", 100)

        # Check that the bridge's create_progress method was called
        bridge.create_progress.assert_called_once_with("Task 1", total=100)

        # Check that the indicator was stored
        assert manager.indicators["task1"] == indicator

    def test_get_progress(self, manager, bridge):
        """Test getting a progress indicator."""
        # Create a progress indicator
        indicator = manager.create_progress("task1", "Task 1", 100)

        # Get the indicator
        retrieved = manager.get_progress("task1")

        # Check that the correct indicator was returned
        assert retrieved == indicator

        # Check that getting a non-existent indicator returns None
        assert manager.get_progress("non-existent") is None

    def test_update_progress(self, manager, bridge):
        """Test updating a progress indicator."""
        # Create a progress indicator
        indicator = manager.create_progress("task1", "Task 1", 100)

        # Update the indicator
        manager.update_progress("task1", 10, "Updated task")

        # Check that the indicator's update method was called
        indicator.update.assert_called_once_with(advance=10, description="Updated task")

        # Check that updating a non-existent indicator doesn't raise an error
        manager.update_progress("non-existent", 10, "Updated task")

    def test_complete_progress(self, manager, bridge):
        """Test completing a progress indicator."""
        # Create a progress indicator
        indicator = manager.create_progress("task1", "Task 1", 100)

        # Complete the indicator
        manager.complete_progress("task1")

        # Check that the indicator's complete method was called
        indicator.complete.assert_called_once()

        # Check that the indicator was removed from the manager
        assert "task1" not in manager.indicators

        # Check that completing a non-existent indicator doesn't raise an error
        manager.complete_progress("non-existent")


def test_create_enhanced_progress():
    """Test creating an enhanced progress indicator."""
    # Create a real console that writes to /dev/null to avoid cluttering test output
    console = Console(file=open("/dev/null", "w"))

    try:
        # Create an enhanced progress indicator
        indicator = create_enhanced_progress(console, "Task", 100)

        # Check that the indicator is an EnhancedProgressIndicator
        assert isinstance(indicator, EnhancedProgressIndicator)

        # Check that the indicator was initialized correctly
        assert indicator._progress.console == console
        assert indicator._task is not None
    finally:
        # Close the console file
        console.file.close()


def test_create_task_table():
    """Test creating a task table."""
    tasks = [
        {"name": "Task 1", "status": "Complete", "description": "Description 1"},
        {"name": "Task 2", "status": "In Progress", "description": "Description 2"},
        {"name": "Task 3", "status": "Failed", "description": "Description 3"},
    ]

    # Create a task table
    table = create_task_table(tasks, "Test Tasks")

    # Check that the table has the correct title
    assert table.title == "Test Tasks"

    # Check that the table has the correct columns
    assert len(table.columns) == 3
    assert table.columns[0].header == "Task"
    assert table.columns[1].header == "Status"
    assert table.columns[2].header == "Description"


def test_run_with_progress():
    """Test running a task with a progress indicator."""
    bridge = MagicMock(spec=UXBridge)
    progress = MagicMock()
    bridge.create_progress.return_value = progress

    # Define a task function
    def task_fn():
        return "result"

    # Run the task with progress
    result = run_with_progress("Task", task_fn, bridge, 100, [
        {"name": "Subtask 1", "total": 50},
        {"name": "Subtask 2", "total": 30},
    ])

    # Check that the bridge's create_progress method was called
    bridge.create_progress.assert_called_once_with("Task", total=100)

    # Check that the task function was called
    assert result == "result"

    # Check that the progress was completed
    progress.complete.assert_called_once()
