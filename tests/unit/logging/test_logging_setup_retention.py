"""Retention and sandbox relocation tests for ``devsynth.logging_setup``."""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Optional

import pytest


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
@pytest.mark.parametrize(
    ("create_dir", "no_file_env", "expected_effective"),
    [
        pytest.param(True, None, True, id="create-dir"),
        pytest.param(True, "1", False, id="no-file-env"),
        pytest.param(False, None, False, id="create-dir-disabled"),
        pytest.param(False, "1", False, id="no-file-env-create-dir-disabled"),
    ],
)
def test_configure_logging_retention_matrix(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    create_dir: bool,
    no_file_env: str | None,
    expected_effective: bool,
) -> None:
    """Exercise retention decisions across create_dir and environment flags."""

    logging_setup = logging_setup_module
    project_dir = tmp_path / "retention_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    if no_file_env is not None:
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", no_file_env)

    log_dir_argument = "relative/logs"
    ensure_calls: list[str | None] = []
    real_ensure = logging_setup.ensure_log_dir_exists

    def tracking(log_dir: str | None = None) -> str:
        ensure_calls.append(log_dir)
        return real_ensure(log_dir)

    monkeypatch.setattr(logging_setup, "ensure_log_dir_exists", tracking)

    logging_setup.configure_logging(log_dir=log_dir_argument, create_dir=create_dir)

    expected_dir = os.path.join(str(project_dir), log_dir_argument)
    expected_file = os.path.join(
        expected_dir,
        os.environ.get("DEVSYNTH_LOG_FILENAME", logging_setup.DEFAULT_LOG_FILENAME),
    )

    assert logging_setup._configured_log_dir == expected_dir
    assert logging_setup._configured_log_file == expected_file
    assert logging_setup._last_effective_config[0] == expected_dir
    assert logging_setup._last_effective_config[1] == expected_file
    assert logging_setup._last_effective_config[3] is expected_effective

    if expected_effective:
        assert ensure_calls == [expected_dir]
    else:
        assert ensure_calls == []

    root_logger = logging.getLogger()
    console_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    assert console_handlers, "Console handler must always be configured."

    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    if expected_effective:
        assert len(file_handlers) == 1
        file_handler = file_handlers[0]
        assert isinstance(file_handler.formatter, logging_setup.JSONFormatter)
        assert Path(file_handler.baseFilename) == Path(expected_file)
    else:
        assert file_handlers == []


@pytest.mark.fast
@pytest.mark.parametrize(
    ("log_dir_input", "log_file_name"),
    [
        pytest.param(
            Path.home() / "devsynth" / "logs", "home.json", id="home-absolute"
        ),
        pytest.param(
            Path("/var/tmp/devsynth/logs"), "system.json", id="non-home-absolute"
        ),
    ],
)
def test_configure_logging_relocates_absolute_paths(
    logging_setup_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    log_dir_input: Path,
    log_file_name: str,
) -> None:
    """Absolute paths are redirected into the sandboxed project directory."""

    logging_setup = logging_setup_module
    project_dir = tmp_path / "sandbox_relocation"
    project_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    log_file_input = log_dir_input / log_file_name

    ensure_calls: list[str | None] = []
    real_ensure = logging_setup.ensure_log_dir_exists

    def tracking(log_dir: str | None = None) -> str:
        ensure_calls.append(log_dir)
        return real_ensure(log_dir)

    monkeypatch.setattr(logging_setup, "ensure_log_dir_exists", tracking)

    logging_setup.configure_logging(
        log_dir=str(log_dir_input),
        log_file=str(log_file_input),
        create_dir=True,
    )

    home_prefix = str(Path.home())

    def expected_relative(path: Path) -> str:
        path_str = str(path)
        if path_str.startswith(home_prefix):
            return path_str.replace(home_prefix, "", 1).lstrip("/\\")
        return str(path.relative_to(path.anchor))

    expected_dir = os.path.join(str(project_dir), expected_relative(log_dir_input))
    expected_file = os.path.join(str(project_dir), expected_relative(log_file_input))

    assert ensure_calls == [expected_dir]
    assert logging_setup._configured_log_dir == expected_dir
    assert logging_setup._configured_log_file == expected_file
    assert logging_setup._last_effective_config[0] == expected_dir
    assert logging_setup._last_effective_config[1] == expected_file
    assert logging_setup._last_effective_config[3] is True

    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert len(file_handlers) == 1
    file_handler = file_handlers[0]
    assert Path(file_handler.baseFilename) == Path(expected_file)
    assert isinstance(file_handler.formatter, logging_setup.JSONFormatter)

    console_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    assert (
        console_handlers
    ), "Console handler should remain active alongside file handler."
