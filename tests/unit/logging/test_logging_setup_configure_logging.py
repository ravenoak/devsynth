"""Focused tests for :func:`devsynth.logging_setup.configure_logging`."""

from __future__ import annotations

import importlib
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
@pytest.mark.parametrize(
    "project_env_enabled,no_file_logging,log_dir_kind,explicit_log_file",
    [
        pytest.param(True, False, "relative", None, id="project-dir_file-logging"),
        pytest.param(True, True, "relative", None, id="project-dir_console-only"),
        pytest.param(False, False, "absolute", None, id="no-project_file-logging"),
        pytest.param(
            False, True, "absolute", "custom.log", id="no-project_console-custom"
        ),
    ],
)
def test_configure_logging_resolves_paths(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    project_env_enabled: bool,
    no_file_logging: bool,
    log_dir_kind: str,
    explicit_log_file: str | None,
) -> None:
    """ReqID: LOG-CONF-04 — environment toggles resolve directories and handlers."""

    logging_setup = logging_setup_module

    if project_env_enabled:
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    else:
        project_dir = None
        monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)

    if no_file_logging:
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    else:
        monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    if log_dir_kind == "relative":
        provided_log_dir = "service/logs"
        expected_dir = (project_dir or tmp_path) / provided_log_dir
        log_dir_argument = provided_log_dir
    else:
        base_dir = tmp_path / (
            "absolute_logs" if explicit_log_file is None else "absolute_console"
        )
        provided_log_dir = base_dir
        expected_dir = base_dir
        log_dir_argument = str(provided_log_dir)

    if explicit_log_file is not None:
        log_file_argument = str(expected_dir / explicit_log_file)
        expected_file = expected_dir / explicit_log_file
    else:
        log_file_argument = None
        expected_file = expected_dir / logging_setup.DEFAULT_LOG_FILENAME

    logging_setup.configure_logging(
        log_dir=log_dir_argument,
        log_file=log_file_argument,
    )

    configured_dir = Path(logging_setup.get_log_dir())
    configured_file = Path(logging_setup.get_log_file())

    assert configured_dir == expected_dir
    assert configured_file == expected_file

    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    if no_file_logging:
        assert (
            not file_handlers
        ), "File handlers should be absent when file logging disabled."
    else:
        assert file_handlers, "Expected a configured file handler when logging to file."


@pytest.mark.fast
def test_configure_logging_idempotent_with_identical_settings(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CONF-05 — identical calls keep handler/filter sets stable."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    log_directory = tmp_path / "idempotent"
    logging_setup.configure_logging(log_dir=str(log_directory))

    root_logger = logging.getLogger()
    initial_handlers = tuple(root_logger.handlers)
    initial_filters = tuple(root_logger.filters)

    logging_setup.configure_logging(log_dir=str(log_directory))

    assert tuple(root_logger.handlers) == initial_handlers
    assert tuple(root_logger.filters) == initial_filters


@pytest.mark.fast
def test_configure_logging_invokes_directory_creation_once(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CONF-05A — ensure_log_dir_exists executes only on first configuration."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    calls: list[str] = []

    def fake_ensure(path: str) -> str:
        calls.append(path)
        return path

    monkeypatch.setattr(logging_setup, "ensure_log_dir_exists", fake_ensure)

    logging_setup.configure_logging(log_dir="logs")
    logging_setup.configure_logging(log_dir="logs")

    assert calls == [str(tmp_path / "logs")]


@pytest.mark.fast
def test_configure_logging_preserves_filters_on_reconfigure(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-CONF-06 — request-context filters survive reconfiguration."""

    logging_setup = logging_setup_module
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging(log_dir="logs")

    root_logger = logging.getLogger()
    context_filter = logging_setup.RequestContextFilter()
    root_logger.addFilter(context_filter)

    assert any(
        isinstance(existing, logging_setup.RedactSecretsFilter)
        for existing in root_logger.filters
    ), "Expected a redaction filter before reconfiguration."

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    logging_setup.configure_logging(log_dir="logs")

    remaining_filters = tuple(logging.getLogger().filters)
    assert context_filter in remaining_filters
    assert any(
        isinstance(existing, logging_setup.RedactSecretsFilter)
        for existing in remaining_filters
    )


@pytest.mark.fast
def test_configure_logging_falls_back_to_console_on_file_handler_failure(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: LOG-CONF-07 — console formatter updates when file handlers fail."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    caplog.set_level(logging.WARNING)

    original_file_handler = logging.FileHandler

    class ExplodingFileHandler(original_file_handler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise PermissionError("filesystem locked")

    monkeypatch.setattr(logging, "FileHandler", ExplodingFileHandler)

    logging_setup.configure_logging(log_dir=str(tmp_path / "fails"))

    root_logger = logging.getLogger()
    stream_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    assert stream_handlers, "Console handler should always be configured."
    assert stream_handlers[0].formatter is not None
    assert stream_handlers[0].formatter._style._fmt.startswith(
        "WARNING: File logging failed"
    )
    assert not any(
        isinstance(handler, original_file_handler) for handler in root_logger.handlers
    )
