from unittest.mock import MagicMock

import pytest

from devsynth.application.cli.progress import ProgressManager

pytestmark = [pytest.mark.fast]


class DummyBridge:
    def __init__(self):
        self.indicator = MagicMock()

    def create_progress(self, description: str, total: int = 100):
        return self.indicator


def test_progress_manager_handles_lifecycle():
    bridge = DummyBridge()
    manager = ProgressManager(bridge)  # type: ignore[arg-type]

    indicator = manager.create_progress("task", "Task", total=2)
    manager.update_progress("task", description="step one")
    bridge.indicator.update.assert_called_once_with(advance=1, description="step one")

    manager.complete_progress("task")
    bridge.indicator.complete.assert_called_once()
    assert manager.get_progress("task") is None
