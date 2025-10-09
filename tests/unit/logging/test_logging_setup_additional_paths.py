"""Targeted tests for unexercised paths in :mod:`devsynth.logging_setup`."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture()
def logging_setup_module() -> Iterator[object]:
    """Reload logging module and restore root logger configuration afterwards."""

    import devsynth.logging_setup as logging_setup

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for filt in root_logger.filters[:]:
        root_logger.removeFilter(filt)

    module = importlib.reload(logging_setup)

    try:
        yield module
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        for filt in root_logger.filters[:]:
            root_logger.removeFilter(filt)
        for filt in original_filters:
            root_logger.addFilter(filt)
        root_logger.setLevel(original_level)
        importlib.reload(logging_setup)


def test_redact_secrets_filter_masks_values(
    monkeypatch: pytest.MonkeyPatch, logging_setup_module: object
) -> None:
    """Known secrets are masked in messages and extras.

    ReqID: coverage-logging-setup
    """

    logging_setup = logging_setup_module
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    filter_ = logging_setup.RedactSecretsFilter()

    record = logging.LogRecord(
        name="devsynth.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="using key sk-test-secret",
        args=(),
        exc_info=None,
    )
    record.extra = {"api_key": "sk-test-secret"}

    assert filter_.filter(record) is True
    assert "***REDACTED***cret" in record.msg
    assert record.extra["api_key"].startswith("***REDACTED***")


def test_json_formatter_includes_context_and_extras(
    logging_setup_module: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Structured formatter emits contextual attributes and exception info.

    ReqID: coverage-logging-setup
    """

    logging_setup = logging_setup_module
    logging_setup.set_request_context(request_id="req-1", phase="bootstrap")

    formatter = logging_setup.JSONFormatter()
    record = logging.LogRecord(
        name="devsynth.json",
        level=logging.ERROR,
        pathname=__file__,
        lineno=42,
        msg="boom",
        args=(),
        exc_info=(ValueError, ValueError("boom"), None),
    )
    record.some_extra = "value"
    record.request_id = logging_setup.request_id_var.get()
    record.phase = logging_setup.phase_var.get()

    payload = formatter.format(record)
    assert "req-1" in payload
    assert "bootstrap" in payload
    assert "some_extra" in payload
    assert "ValueError" in payload

    logging_setup.clear_request_context()


def test_ensure_log_dir_exists_respects_project_dir(
    logging_setup_module: object, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Log paths are redirected inside ``DEVSYNTH_PROJECT_DIR``.

    ReqID: coverage-logging-setup
    """

    logging_setup = logging_setup_module
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))

    resolved = logging_setup.ensure_log_dir_exists(log_dir="logs/output")

    assert Path(resolved).is_dir()
    assert resolved.startswith(str(project_dir))


def test_ensure_log_dir_exists_skips_creation_when_disabled(
    logging_setup_module: object, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When file logging is disabled the directory is not created.

    ReqID: coverage-logging-setup
    """

    logging_setup = logging_setup_module
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    resolved = logging_setup.ensure_log_dir_exists(log_dir="logs")

    assert Path(resolved).exists() is False


def test_ensure_log_dir_exists_warns_when_creation_fails(
    logging_setup_module: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: coverage-logging-setup-guard — warning emitted when makedirs fails.

    Issue: issues/coverage-below-threshold.md
    """

    logging_setup = logging_setup_module
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)

    target = tmp_path / "guarded"

    caplog.set_level(logging.WARNING)

    def raise_permission(path: str, exist_ok: bool = True) -> None:  # noqa: FBT002
        raise PermissionError("denied")

    monkeypatch.setattr(logging_setup.os, "makedirs", raise_permission)

    resolved = logging_setup.ensure_log_dir_exists(str(target))

    assert resolved == str(target)
    assert any(
        "Failed to create log directory" in record.getMessage()
        for record in caplog.records
    )


def test_devsynth_logger_filters_reserved_extra_keys(
    logging_setup_module: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reserved logging keys are stripped from the ``extra`` payload.

    ReqID: coverage-logging-setup
    """

    logging_setup = logging_setup_module

    captured = {}

    class FakeLogger(logging.Logger):
        def log(self, level, msg, *args, **kwargs):  # noqa: ANN001
            captured["level"] = level
            captured["msg"] = msg
            captured["kwargs"] = kwargs

    fake_logger = FakeLogger("devsynth.fake")

    def fake_get_logger(name: str | None = None) -> FakeLogger:
        return fake_logger

    monkeypatch.setattr(logging_setup.logging, "getLogger", fake_get_logger)

    logger = logging_setup.DevSynthLogger("devsynth.fake")
    logger._log(  # type: ignore[attr-defined]
        logging.INFO,
        "hello",
        extra={"name": "bad", "safe": "ok"},
        stack_info=True,
        stacklevel=2,
    )

    assert captured["level"] == logging.INFO
    assert captured["msg"] == "hello"
    assert captured["kwargs"]["extra"] == {"safe": "ok"}
    assert captured["kwargs"]["stack_info"] is True
    assert captured["kwargs"]["stacklevel"] == 2


def test_redact_filter_masks_args_and_payload(
    monkeypatch: pytest.MonkeyPatch, logging_setup_module: object
) -> None:
    """ReqID: coverage-logging-setup-args — tuple args and payload fields are redacted."""

    logging_setup = logging_setup_module
    monkeypatch.setenv("OPENAI_API_KEY", "sk-new-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret")

    filt = logging_setup.RedactSecretsFilter()

    record = logging.LogRecord(
        name="devsynth.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=99,
        msg="sending sk-new-secret over the wire",
        args=("header anthropic-secret", 42),
        exc_info=None,
    )
    record.payload = {"api_key": "sk-new-secret", "note": "anthropic-secret"}

    assert filt.filter(record) is True
    masked_msg = record.msg
    assert "sk-new-secret" not in masked_msg
    assert "anthropic-secret" not in masked_msg
    assert record.args[0].startswith("header ***REDACTED***")
    assert record.payload["api_key"].startswith("***REDACTED***")
    assert record.payload["note"].startswith("***REDACTED***")
