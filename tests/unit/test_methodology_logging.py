import logging
from devsynth.methodology.sprint import SprintAdapter
from devsynth.methodology.base import Phase


def test_phase_timeout_logs_warning(caplog):
    caplog.set_level(logging.WARNING)
    adapter = SprintAdapter({"settings": {}})
    adapter._log_phase_timeout(Phase.EXPAND, ["activity1", "activity2"])
    assert any(
        "timed out" in record.message and record.levelno == logging.WARNING
        for record in caplog.records
    )
