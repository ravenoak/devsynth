"""Additional coverage for logging configuration behaviours."""

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
    for filt in root_logger.filters[:]:
        root_logger.removeFilter(filt)

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
        for filt in root_logger.filters[:]:
            root_logger.removeFilter(filt)
        root_logger.setLevel(original_level)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        for filt in original_filters:
            root_logger.addFilter(filt)
        importlib.reload(logging_setup)


@pytest.mark.fast
def test_configure_logging_honors_env_log_level(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment log level overrides propagate to the root logger."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_LOG_LEVEL", str(logging.DEBUG))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir=str(tmp_path / "logs"))

    assert logging.getLogger().level == logging.DEBUG


@pytest.mark.fast
def test_json_formatter_captures_request_context(
    logging_setup_module: ModuleType,
) -> None:
    """Structured logs include custom context fields and computed message."""

    formatter = logging_setup_module.JSONFormatter()

    record = logging.LogRecord(
        name="devsynth.tests.json",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="processing %s",
        args=("payload",),
        exc_info=None,
        func="test_json_formatter_captures_request_context",
    )
    record.caller_module = "custom.module"
    record.caller_function = "custom_function"
    record.caller_line = 101
    record.request_id = "req-xyz"
    record.phase = "refine"
    record.extra_detail = "value"

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "processing payload"
    assert payload["module"] == "custom.module"
    assert payload["function"] == "custom_function"
    assert payload["line"] == 101
    assert payload["request_id"] == "req-xyz"
    assert payload["phase"] == "refine"
    assert payload["extra_detail"] == "value"


@pytest.mark.fast
def test_dev_logger_attaches_filters_and_handlers(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DevSynth loggers inherit redaction filters and structured handlers."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir=str(tmp_path / "logs"))

    root_logger = logging.getLogger()
    assert any(
        isinstance(filt, logging_setup.RedactSecretsFilter)
        for filt in root_logger.filters
    )

    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert file_handlers, "Expected JSON file handler to be configured"
    assert isinstance(file_handlers[0].formatter, logging_setup.JSONFormatter)

    dev_logger = logging_setup.DevSynthLogger("devsynth.tests.wiring")
    attached_filters = dev_logger.logger.filters
    assert any(
        isinstance(filt, logging_setup.RequestContextFilter)
        for filt in attached_filters
    )
    assert any(
        isinstance(filt, logging_setup.RedactSecretsFilter) for filt in attached_filters
    )
