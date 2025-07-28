import time
from devsynth.interface.webui_bridge import WebUIProgressIndicator


def test_update_records_time(monkeypatch):
    times = iter([100.0, 101.0])
    monkeypatch.setattr(time, "time", lambda: next(times))
    indicator = WebUIProgressIndicator("Task", 10)
    indicator.update()
    indicator.update(advance=2)
    assert indicator._update_times == [(100.0, 1), (101.0, 3)]
