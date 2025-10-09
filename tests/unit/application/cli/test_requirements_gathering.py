import logging

import pytest
from _pytest.logging import LogCaptureHandler

from devsynth.application.cli import requirements_commands as rc
from devsynth.application.cli.errors import handle_error
from devsynth.logging_setup import configure_logging

pytestmark = [pytest.mark.fast]


class DummyBridge:
    """Minimal bridge implementing bridge methods used in tests."""

    def display_result(self, *_a, **_k):
        pass

    def handle_error(self, *_a, **_k):
        pass


def test_gather_cmd_logging_exc_info_succeeds(monkeypatch):
    """gather_requirements_cmd should log exceptions with tuple exc_info."""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    configure_logging(create_dir=False)
    handler = LogCaptureHandler()
    logging.getLogger().addHandler(handler)

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr("devsynth.core.workflows.gather_requirements", boom)

    bridge = DummyBridge()
    try:
        rc.gather_requirements_cmd(bridge=bridge)
    except RuntimeError as err:
        handle_error(bridge, err)

    logging.getLogger().removeHandler(handler)
    record = next(rec for rec in handler.records if rec.exc_info)
    assert record.exc_info[0] is RuntimeError
