import io
import json
import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.devsynth.logging_setup import (
    DEFAULT_LOG_FILENAME,
    DEFAULT_LOG_FORMAT,
    DevSynthLogger,
    JSONFormatter,
    RedactSecretsFilter,
    RequestContextFilter,
    clear_request_context,
    configure_logging,
    ensure_log_dir_exists,
    get_log_dir,
    get_log_file,
    set_request_context,
)


def _make_logger(
    name: str, with_context_filter: bool = False
) -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RedactSecretsFilter())
    if with_context_filter:
        handler.addFilter(RequestContextFilter())
    logger = logging.getLogger(name)
    # Ensure a clean logger each time
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger, stream


@pytest.mark.fast
def test_redact_filter_masks_message_args_and_mappings(monkeypatch):
    """ReqID: LOG-00A — filter masks secrets in message, args, and mapping extras."""

    secret = "sk-secret-1234567890"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    filt = RedactSecretsFilter()
    record = logging.LogRecord(
        name="devsynth.test.filter",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg=f"Token inline {secret}",
        args=(secret,),
        exc_info=None,
        func="test",
    )
    record.extra = {"token": secret, "count": 2}
    record.details = {"api_key": secret}

    assert filt.filter(record) is True

    assert secret not in record.msg
    assert "***REDACTED***" in record.msg
    masked_arg = record.args[0]
    assert isinstance(masked_arg, str) and secret not in masked_arg
    assert masked_arg.endswith(secret[-4:])

    assert record.extra["token"].startswith("***REDACTED***")
    assert record.extra["token"].endswith(secret[-4:])
    assert record.extra["count"] == 2
    assert record.details["api_key"].startswith("***REDACTED***")


@pytest.mark.fast
def test_request_context_filter_attaches_context():
    """ReqID: LOG-00B — request context filter injects context vars into records."""

    set_request_context("req-filter-1", "phase-filter")
    record = logging.LogRecord(
        name="devsynth.test.context.filter",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="context",
        args=(),
        exc_info=None,
        func="test",
    )
    try:
        assert RequestContextFilter().filter(record) is True
        assert record.request_id == "req-filter-1"
        assert record.phase == "phase-filter"
    finally:
        clear_request_context()

    empty_record = logging.LogRecord(
        name="devsynth.test.context.filter",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="context",
        args=(),
        exc_info=None,
        func="test",
    )
    assert RequestContextFilter().filter(empty_record) is True
    assert empty_record.request_id is None
    assert empty_record.phase is None


@pytest.mark.fast
def test_redaction_in_message_and_payload(monkeypatch):
    """ReqID: LOG-01 — redacts secrets in message/payload.
    Keeps non-sensitive fields intact.
    """
    # Arrange a realistic-looking secret
    secret = "sk-test-1234567890"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    logger, stream = _make_logger("devsynth.test.redact")

    # Act: include secret in both message args and payload extra
    logger.info(
        "Connecting with key %s",  # args path hits getMessage()
        secret,
        extra={"payload": {"api_key": secret, "count": 2}},
    )

    out = stream.getvalue().strip()
    data = json.loads(out)

    # Assert: message redacted and payload redacted, numeric preserved
    assert secret not in data["message"]
    assert "***REDACTED***" in data["message"]
    assert data["payload"]["api_key"].startswith("***REDACTED***")
    assert data["payload"]["api_key"].endswith(secret[-4:])
    assert data["payload"]["count"] == 2


@pytest.mark.fast
def test_request_context_filter_injects_fields_and_clears():
    """ReqID: LOG-02 — request context fields are injected and cleared correctly."""
    logger, stream = _make_logger("devsynth.test.context", with_context_filter=True)

    # With context set, fields should appear
    set_request_context("req-123", "phase-alpha")
    logger.info("hello")

    # After clearing, fields should not appear
    clear_request_context()
    logger.info("world")

    lines = [json.loads(line) for line in stream.getvalue().strip().splitlines()]

    assert lines[0]["request_id"] == "req-123"
    assert lines[0]["phase"] == "phase-alpha"
    # Second line should not retain non-empty context; keys may exist but be null/empty
    assert not lines[1].get("request_id")
    assert not lines[1].get("phase")


@pytest.mark.fast
def test_jsonformatter_includes_exception_block():
    """ReqID: LOG-03 — JSONFormatter includes exception block with traceback lines."""
    logger, stream = _make_logger("devsynth.test.exc")

    try:
        raise ValueError("boom")
    except Exception:
        logger.exception("something happened")

    data = json.loads(stream.getvalue().strip())
    assert data["level"] == "ERROR"
    assert "exception" in data
    exception = data["exception"]
    assert exception["type"] == "ValueError"
    assert exception["message"] == "boom"

    tb = exception["traceback"]
    assert isinstance(tb, list)
    assert tb and tb[0].startswith("Traceback")
    assert all(isinstance(line, str) for line in tb)
    assert any("ValueError: boom" in line for line in tb)


@pytest.mark.fast
def test_ensure_log_dir_respects_no_file_logging(monkeypatch, tmp_path):
    """ReqID: LOG-04 — no file logging skips dir creation but returns given path."""
    # Ensure no directories are created when DEVSYNTH_NO_FILE_LOGGING is set
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    # Provide a path under tmp_path that does not exist yet
    d = tmp_path / "logs_subdir"
    assert not d.exists()

    out_dir = ensure_log_dir_exists(str(d))
    # Path is returned as-is
    assert out_dir == str(d)
    # And directory should still not exist (no filesystem writes)
    assert not d.exists()


@pytest.mark.fast
def test_get_log_dir_and_file_use_env_overrides(monkeypatch, tmp_path):
    """ReqID: LOG-05 — env overrides for log dir and filename are honored."""
    # Override directory and filename via env
    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DEVSYNTH_LOG_FILENAME", "custom.jsonl")
    d = get_log_dir()
    f = get_log_file()
    assert d.endswith("logs")
    assert f.endswith("logs/custom.jsonl")


@pytest.mark.fast
def test_ensure_log_dir_uses_project_dir_for_relative_path(monkeypatch, tmp_path):
    """ReqID: LOG-05A — relative paths honor DEVSYNTH_PROJECT_DIR redirection."""

    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    relative = "nested/logs"
    out_dir = ensure_log_dir_exists(relative)
    expected = tmp_path / relative

    assert out_dir == str(expected)
    assert expected.exists() and expected.is_dir()


@pytest.mark.fast
def test_ensure_log_dir_redirects_under_test_project_dir(monkeypatch, tmp_path):
    """ReqID: LOG-06 — absolute paths redirect under DEVSYNTH_PROJECT_DIR in tests."""
    # Simulate test environment with DEVSYNTH_PROJECT_DIR
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    # Provide an absolute path under user's home to trigger redirection branch
    abs_path = os.path.join(str(Path.home()), "some", "app", "logs")
    out_dir = ensure_log_dir_exists(abs_path)
    # Should be redirected to live under tmp_path
    assert str(out_dir).startswith(str(tmp_path))
    # Directory should be created under tmp_path
    assert os.path.isdir(out_dir)


@pytest.mark.fast
def test_configure_logging_redirects_home_and_disables_file_handler(
    monkeypatch, tmp_path
):
    """ReqID: LOG-06A — home paths redirect under project dir with console-only fallback."""

    import src.devsynth.logging_setup as logging_setup_module

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    for filt in root_logger.filters[:]:
        root_logger.removeFilter(filt)

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "true")
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_LOG_DIR", raising=False)
    monkeypatch.delenv("DEVSYNTH_LOG_FILENAME", raising=False)

    monkeypatch.setattr(logging_setup_module, "_logging_configured", False)
    monkeypatch.setattr(logging_setup_module, "_last_effective_config", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_dir", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_file", None)

    home_dir = Path.home() / "devsynth-home" / "logs"
    expected_suffix = Path(home_dir).relative_to(Path.home())

    try:
        configure_logging(log_dir=str(home_dir))

        configured_dir = Path(get_log_dir())
        assert configured_dir.is_relative_to(tmp_path)
        relative_to_project = configured_dir.relative_to(tmp_path)
        assert relative_to_project.parts[-len(expected_suffix.parts) :] == expected_suffix.parts
        assert not configured_dir.exists(), "Directory should not be created when file logging is off"

        configured_file = Path(get_log_file())
        assert configured_file.parent == configured_dir
        assert configured_file.name == DEFAULT_LOG_FILENAME

        handlers = list(logging.getLogger().handlers)
        assert all(
            not isinstance(handler, logging.FileHandler) for handler in handlers
        ), "File handler should be absent"

        console_handlers = [
            handler
            for handler in handlers
            if isinstance(handler, logging.StreamHandler)
        ]
        assert console_handlers, "Console handler should be configured"
        assert any(
            getattr(getattr(handler, "formatter", None), "_fmt", None)
            == DEFAULT_LOG_FORMAT
            for handler in console_handlers
        ), "Console handler should use default formatter"
    finally:
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
            if handler not in original_handlers:
                try:
                    handler.close()
                except Exception:
                    pass
        for handler in original_handlers:
            logging.getLogger().addHandler(handler)

        for filt in logging.getLogger().filters[:]:
            logging.getLogger().removeFilter(filt)
        for filt in original_filters:
            logging.getLogger().addFilter(filt)

        logging.getLogger().setLevel(original_level)


@pytest.mark.fast
def test_short_secret_not_redacted(monkeypatch):
    """Secrets shorter than 8 chars remain visible; mask handles empty.

    ReqID: N/A"""
    monkeypatch.setenv("OPENAI_API_KEY", "short")
    logger, stream = _make_logger("devsynth.test.short")
    logger.info("using key %s", "short")
    data = json.loads(stream.getvalue().strip())
    assert "short" in data["message"]
    assert RedactSecretsFilter._mask("") == ""


@pytest.mark.fast
def test_devsynth_logger_log_merges_and_filters_kwargs():
    """ReqID: LOG-06B — ``DevSynthLogger._log`` merges kwargs and strips reserved fields."""

    logger_wrapper = DevSynthLogger("devsynth.test.merge")
    inner_logger = logger_wrapper.logger
    original_log = inner_logger.log

    mock_log = MagicMock()
    inner_logger.log = mock_log

    try:
        try:
            raise RuntimeError("boom")
        except RuntimeError as err:
            logger_wrapper._log(
                logging.ERROR,
                "merge kwargs",
                extra={"custom": "value", "name": "intruder", "lineno": 999},
                stacklevel=4,
                stack_info="stack details",
                exc_info=err,
                correlation="abc123",
                process=555,
            )
    finally:
        inner_logger.log = original_log
        inner_logger.handlers = []
        inner_logger.filters = []
        inner_logger.propagate = True

    mock_log.assert_called_once()
    call_args, call_kwargs = mock_log.call_args
    assert call_args[0] == logging.ERROR
    assert call_args[1] == "merge kwargs"
    assert set(call_kwargs.keys()) == {"extra", "exc_info", "stack_info", "stacklevel"}
    assert call_kwargs["stacklevel"] == 4
    assert call_kwargs["stack_info"] == "stack details"

    exc_info = call_kwargs["exc_info"]
    assert isinstance(exc_info, tuple)
    assert exc_info[0] is RuntimeError
    assert str(exc_info[1]) == "boom"

    extra = call_kwargs["extra"]
    assert extra["custom"] == "value"
    assert extra["correlation"] == "abc123"
    assert "name" not in extra
    assert "lineno" not in extra
    assert "process" not in extra
