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
def test_cli_context_wires_console_and_json_file_handlers(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CTX-01 — CLI wiring keeps console and JSON handlers aligned."""

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(tmp_path / "cli-logs"))
    monkeypatch.setenv("DEVSYNTH_LOG_FILENAME", "cli.jsonl")

    logging_setup.configure_logging()

    root_logger = logging.getLogger()

    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert len(file_handlers) == 1, "Expected JSON file handler for CLI output."
    file_handler = file_handlers[0]
    assert isinstance(file_handler.formatter, logging_setup.JSONFormatter)
    assert Path(file_handler.baseFilename).name == "cli.jsonl"

    console_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
    ]
    assert len(console_handlers) == 1
    assert (
        getattr(console_handlers[0].formatter, "_fmt", None)
        == logging_setup.DEFAULT_LOG_FORMAT
    )

    logger = logging_setup.DevSynthLogger("devsynth.tests.cli")
    logger.info("cli run", extra={"mode": "cli"})

    for handler in root_logger.handlers:
        try:
            handler.flush()
        except Exception:  # pragma: no cover - defensive flush guard
            pass

    log_path = Path(logging_setup.get_log_file())
    lines = log_path.read_text().splitlines()
    payloads = [json.loads(line) for line in lines if line]
    assert payloads, "Expected structured payload in CLI log file."
    last = payloads[-1]
    assert last["message"] == "cli run"
    assert last["logger"] == "devsynth.tests.cli"
    assert last["mode"] == "cli"


@pytest.mark.fast
def test_test_context_redirects_and_supports_console_only_toggle(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CTX-02 — Test runs redirect logs and respect console-only toggles."""

    logging_setup = logging_setup_module
    project_dir = tmp_path / "project"
    project_dir.mkdir(exist_ok=True)

    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    absolute_dir = Path.home() / "devsynth" / "logs"
    logging_setup.configure_logging(log_dir=str(absolute_dir))

    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert file_handlers, "File handler should be present before toggle."
    redirected_path = Path(file_handlers[0].baseFilename)
    assert str(redirected_path).startswith(str(project_dir))

    logger = logging_setup.DevSynthLogger("devsynth.tests.redirect")
    logger.info("redirected file message", extra={"phase": "refine"})
    for handler in file_handlers:
        handler.flush()

    log_file_path = Path(file_handlers[0].baseFilename)
    entries = [
        json.loads(line) for line in log_file_path.read_text().splitlines() if line
    ]
    assert entries, "Expected redirected file log entries."
    payload = entries[-1]
    assert payload["phase"] == "refine"

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    logging_setup.configure_logging(log_dir=str(absolute_dir))

    root_logger = logging.getLogger()
    console_only = all(
        not isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
    )
    assert console_only, "Console-only toggle should remove file handlers."

    capture_handler = LogCaptureHandler()
    capture_handler.setLevel(logging.INFO)
    root_logger.addHandler(capture_handler)
    try:
        logging_setup.DevSynthLogger("devsynth.tests.console").info(
            "console only", extra={"workflow": "test"}
        )
    finally:
        root_logger.removeHandler(capture_handler)
        capture_handler.close()

    assert any(
        record.name == "devsynth.tests.console"
        and record.getMessage() == "console only"
        for record in capture_handler.records
    )


@pytest.mark.fast
def test_create_dir_toggle_disables_json_file_handler(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CTX-03 — create_dir disables JSON handler; console logs persist."""

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir=str(tmp_path / "manual"), create_dir=False)

    assert all(
        not isinstance(handler, logging.FileHandler)
        for handler in logging.getLogger().handlers
    )

    root_logger = logging.getLogger()
    capture_handler = LogCaptureHandler()
    capture_handler.setLevel(logging.INFO)
    root_logger.addHandler(capture_handler)
    try:
        logging_setup.DevSynthLogger("devsynth.tests.manual").info(
            "manual toggle", extra={"mode": "manual"}
        )
    finally:
        root_logger.removeHandler(capture_handler)
        capture_handler.close()

    assert capture_handler.records, "Console handler should capture manual toggle log."
    last_record = capture_handler.records[-1]
    assert last_record.name == "devsynth.tests.manual"
    assert last_record.getMessage() == "manual toggle"
