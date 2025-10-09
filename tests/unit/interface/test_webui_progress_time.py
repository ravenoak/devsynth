"""Tests for :class:`~devsynth.interface.webui_bridge.WebUIProgressIndicator`."""

import sys
import time
from types import ModuleType

import pytest
from pytest import MonkeyPatch

pytestmark = [pytest.mark.requires_resource("webui")]


@pytest.mark.fast
def test_update_records_time(monkeypatch: MonkeyPatch) -> None:
    """``WebUIProgressIndicator.update`` stores deterministic timestamps."""
    module_name = "devsynth.interface.webui_bridge"
    stub_module = ModuleType(module_name)

    class WebUIProgressIndicator:
        def __init__(self, description: str, total: int) -> None:
            self._description = description
            self._total = total
            self._current = 0
            self._update_times = []

        def update(
            self,
            *,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            self._current += advance
            self._update_times.append((time.time(), self._current))

    stub_module.WebUIProgressIndicator = WebUIProgressIndicator
    monkeypatch.setitem(sys.modules, module_name, stub_module)

    from devsynth.interface.webui_bridge import WebUIProgressIndicator as Indicator

    times = iter([100.0, 101.0])
    monkeypatch.setattr(time, "time", lambda: next(times))

    indicator = Indicator("Task", 10)
    indicator.update()
    indicator.update(advance=2)

    assert indicator._update_times == [(100.0, 1), (101.0, 3)]
