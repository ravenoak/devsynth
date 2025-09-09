import logging
import threading

import pytest

from devsynth.logging_setup import configure_logging


@pytest.mark.fast
def test_configure_logging_idempotent_no_duplicate_handlers(monkeypatch):
    """configure_logging should not add duplicate handlers on repeated calls.

    ReqID: LOG-INIT-001
    """
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    # First configuration
    configure_logging(create_dir=False, log_level=logging.INFO)
    root = logging.getLogger()
    first_handlers = list(root.handlers)

    # Second configuration with identical effective parameters
    configure_logging(create_dir=False, log_level=logging.INFO)
    second_handlers = list(root.handlers)

    assert len(second_handlers) == len(first_handlers)
    # Ensure the same kinds of handlers (by class) remain
    assert [type(h) for h in second_handlers] == [type(h) for h in first_handlers]


@pytest.mark.fast
def test_configure_logging_thread_safe(monkeypatch):
    """Concurrent calls to configure_logging should not raise and should be stable.

    ReqID: LOG-INIT-002
    """
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    errors: list[BaseException] = []

    def worker():
        try:
            configure_logging(create_dir=False, log_level=logging.DEBUG)
        except BaseException as e:  # pragma: no cover - unexpected
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert not errors, f"configure_logging raised exceptions: {errors}"

    # Make sure we have a small, stable number of handlers (console only)
    root = logging.getLogger()
    handler_types = [type(h).__name__ for h in root.handlers]
    # Expect exactly one StreamHandler in this mode
    assert handler_types.count("StreamHandler") == 1


@pytest.mark.fast
def test_no_file_logging_toggle_prevents_file_handler(tmp_path, monkeypatch):
    """When DEVSYNTH_NO_FILE_LOGGING=1, no FileHandler should be added.

    ReqID: LOG-INIT-003
    """
    # Ensure the env toggle is respected
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    # Use a temp directory to pass in an explicit log dir; should still not create file handler
    configure_logging(log_dir=str(tmp_path), create_dir=True, log_level=logging.INFO)

    root = logging.getLogger()
    assert all(h.__class__.__name__ != "FileHandler" for h in root.handlers)
