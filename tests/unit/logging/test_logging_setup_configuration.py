from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture()
def logging_setup_module() -> Iterator[ModuleType]:
    """Reload :mod:`devsynth.logging_setup` with a clean root logger."""

    import devsynth.logging_setup as logging_setup

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for existing_filter in root_logger.filters[:]:
        root_logger.removeFilter(existing_filter)

    reloaded = importlib.reload(logging_setup)

    try:
        yield reloaded
    finally:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            if handler not in original_handlers:
                try:
                    handler.close()
                except Exception:  # pragma: no cover - defensive cleanup
                    pass
        for existing_filter in root_logger.filters[:]:
            root_logger.removeFilter(existing_filter)
        root_logger.setLevel(original_level)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        for filt in original_filters:
            root_logger.addFilter(filt)
        importlib.reload(logging_setup)


@pytest.mark.fast
def test_configure_logging_explicit_level_overrides_env(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ReqID: LOG-CONF-01 — explicit ``log_level`` outranks env overrides.

    Issue: issues/coverage-below-threshold.md
    """

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_LOG_LEVEL", str(logging.DEBUG))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(
        log_dir=str(tmp_path / "explicit"),
        log_level=logging.WARNING,
    )

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING

    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert file_handlers, "Expected file handler when file logging is enabled."
    assert isinstance(file_handlers[0].formatter, logging_setup.JSONFormatter)


@pytest.mark.fast
def test_configure_logging_json_handler_writes_structured_output(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ReqID: LOG-CONF-02 — JSON file handler emits structured records with extras.

    Issue: issues/coverage-below-threshold.md
    """

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    log_dir = tmp_path / "json"
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir=str(log_dir))

    logger = logging_setup.DevSynthLogger("devsynth.tests.configuration")
    logger.info("structured entry", extra={"marker": "value"})

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    log_file = Path(logging_setup.get_log_file())
    assert log_file.exists(), "Log file should exist after structured write."
    payloads = [
        json.loads(line) for line in log_file.read_text().splitlines() if line.strip()
    ]
    assert payloads, "Expected JSON payload to be written."
    last = payloads[-1]
    assert last["message"] == "structured entry"
    assert last["logger"] == "devsynth.tests.configuration"
    assert last["marker"] == "value"


@pytest.mark.fast
def test_configure_logging_reconfigures_console_only_toggle(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ReqID: LOG-CONF-03 — console-only reconfigure removes JSON handler.

    Issue: issues/coverage-below-threshold.md
    """

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    log_dir = tmp_path / "toggle"
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir=str(log_dir))
    root_logger = logging.getLogger()
    assert any(
        isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
    ), "Initial configuration should attach a file handler."

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    logging_setup.configure_logging(log_dir=str(log_dir))

    root_logger = logging.getLogger()
    assert all(
        not isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
    ), "File handlers should be removed when file logging is disabled."
    assert any(
        isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers
    ), "Console handler should remain present."
