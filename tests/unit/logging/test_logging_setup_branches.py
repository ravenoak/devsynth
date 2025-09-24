"""Branch coverage for ``devsynth.logging_setup.configure_logging``.

These tests exercise the different handler initialization paths to ensure the
structured logging configuration is resilient to environment flags and
file-system failures.
"""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from _pytest.logging import LogCaptureHandler


@pytest.fixture()
def logging_setup_module() -> Iterator[ModuleType]:
    """Reload ``devsynth.logging_setup`` and restore the root logger state."""

    import devsynth.logging_setup as logging_setup

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for existing_filter in root_logger.filters[:]:
        root_logger.removeFilter(existing_filter)

    reloaded_module = importlib.reload(logging_setup)

    try:
        yield reloaded_module
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
def test_configure_logging_provisions_json_file_handler(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ReqID: LOG-07 — file logging path uses ``JSONFormatter`` output."""

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    log_dir = tmp_path / "branch_logs"
    logging_setup.configure_logging(log_dir=str(log_dir))

    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert file_handlers, "Expected file logging handler to be configured."
    file_handler = file_handlers[0]
    assert isinstance(file_handler.formatter, logging_setup.JSONFormatter)
    configured_dir = Path(logging_setup.get_log_dir())
    assert configured_dir.exists()
    assert configured_dir.is_dir()
    assert configured_dir.name == "branch_logs"

    console_handler = next(
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
        and getattr(getattr(handler, "formatter", None), "_fmt", None)
        == logging_setup.DEFAULT_LOG_FORMAT
    )
    assert console_handler is not None

    capture_handler = LogCaptureHandler()
    capture_handler.setLevel(logging.INFO)
    root_logger.addHandler(capture_handler)
    try:
        logger = logging_setup.DevSynthLogger("devsynth.branch.file")
        logger.info("structured branch message", extra={"workflow": "branch-mode"})

        assert capture_handler.records, "Expected structured log record to be emitted."
        record = capture_handler.records[-1]
        formatted = file_handler.format(record)
    finally:
        root_logger.removeHandler(capture_handler)
        capture_handler.close()
    payload = json.loads(formatted)
    assert payload["message"] == "structured branch message"
    assert payload["logger"] == "devsynth.branch.file"
    assert payload["workflow"] == "branch-mode"
    assert payload["level"] == "INFO"


@pytest.mark.fast
def test_configure_logging_console_only_mode(
    logging_setup_module: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ReqID: LOG-08 — environment flag disables file handler entirely."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    logging_setup.configure_logging(log_dir=str(tmp_path / "logs"))

    root_logger = logging.getLogger()
    assert all(
        not isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
    ), "File handler should not be present when file logging is disabled."

    console_handler = next(
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
        and getattr(getattr(handler, "formatter", None), "_fmt", None)
        == logging_setup.DEFAULT_LOG_FORMAT
    )

    capture_handler = LogCaptureHandler()
    capture_handler.setLevel(logging.INFO)
    root_logger.addHandler(capture_handler)
    try:
        logger = logging_setup.DevSynthLogger("devsynth.branch.console")
        logger.info("console output only")

        assert capture_handler.records, "Expected console log record to be captured."
        record = capture_handler.records[-1]
        rendered = console_handler.format(record)
    finally:
        root_logger.removeHandler(capture_handler)
        capture_handler.close()
    assert "console output only" in rendered
    assert "devsynth.branch.console" in rendered


@pytest.mark.fast
@pytest.mark.parametrize(
    ("exception_cls", "message"),
    [
        (PermissionError, "no-permission"),
        (FileNotFoundError, "missing-log"),
    ],
    ids=["permission-error", "file-not-found"],
)
def test_configure_logging_handler_parity_when_file_handler_fails(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception_cls: type[Exception],
    message: str,
) -> None:
    """ReqID: LOG-09 — gracefully degrade when file handler initialization fails."""

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    real_file_handler_type = logging_setup.logging.FileHandler

    def boom(*_args, **_kwargs):
        raise exception_cls(message)

    monkeypatch.setattr(logging_setup.logging, "FileHandler", boom)

    emitted_warnings: list[str] = []
    original_warning = logging.Logger.warning

    def spy_warning(self: logging.Logger, msg: str, *args, **kwargs):
        rendered = msg % args if args else msg
        emitted_warnings.append(rendered)
        return original_warning(self, msg, *args, **kwargs)

    monkeypatch.setattr(logging.Logger, "warning", spy_warning)

    logging_setup.configure_logging(log_dir=str(tmp_path / "logs"))

    root_logger = logging.getLogger()
    assert all(
        not isinstance(handler, real_file_handler_type)
        for handler in root_logger.handlers
    ), "No file handler should be attached after a failure."

    warning_format = "WARNING: File logging failed - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_handler = next(
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
        and getattr(getattr(handler, "formatter", None), "_fmt", "") == warning_format
    )

    assert any(
        f"Failed to set up file logging: {message}" in rendered
        for rendered in emitted_warnings
    ), "Expected warning about the file handler failure."

    capture_handler = LogCaptureHandler()
    capture_handler.setLevel(logging.INFO)
    root_logger.addHandler(capture_handler)
    try:
        logger = logging_setup.DevSynthLogger("devsynth.branch.error")
        logger.info("still logging after failure")

        record = capture_handler.records[-1]
        rendered = console_handler.format(record)
    finally:
        root_logger.removeHandler(capture_handler)
        capture_handler.close()

    segments = rendered.split(" - ")
    assert segments[0] == "WARNING: File logging failed"
    assert len(segments) >= 5
    assert segments[2] == "devsynth.branch.error"
    assert segments[3] == "INFO"
    assert segments[4] == "still logging after failure"


@pytest.mark.fast
def test_configure_logging_idempotent_with_identical_configuration(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-09A — repeated configuration with same inputs is a no-op."""

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    target_dir = tmp_path / "idempotent"
    logging_setup.configure_logging(log_dir=str(target_dir))

    root_logger = logging.getLogger()
    handlers_before = list(root_logger.handlers)
    filters_before = list(root_logger.filters)

    assert handlers_before, "Initial configuration should attach handlers."

    logging_setup.configure_logging(log_dir=str(target_dir))

    assert list(root_logger.handlers) == handlers_before
    assert list(root_logger.filters) == filters_before
