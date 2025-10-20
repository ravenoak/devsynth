import copy
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
def test_redact_filter_property_loop_preserves_inputs(monkeypatch: pytest.MonkeyPatch):
    """ReqID: LOG-01A — secrets are redacted while benign values remain intact."""

    openai_secret = "sk-property-123456789"
    anthropic_secret = "anthropic-secret-abcdef"
    monkeypatch.setenv("OPENAI_API_KEY", openai_secret)
    monkeypatch.setenv("ANTHROPIC_API_KEY", anthropic_secret)

    filt = RedactSecretsFilter()

    secret_cases = [
        ("openai", openai_secret, True),
        ("anthropic", anthropic_secret, True),
        ("benign", "no secrets here", False),
        ("blank", "", False),
    ]

    for label, candidate, should_mask in secret_cases:
        if should_mask and candidate:
            masked = filt._mask(candidate)
            assert masked.startswith("***REDACTED***"), label
            assert masked.endswith(candidate[-4:]), label
            assert candidate not in masked, label
            expected_fragment = masked
        elif not candidate:
            masked = filt._mask(candidate)
            assert masked == candidate, label
            expected_fragment = candidate
        else:
            expected_fragment = candidate

        if candidate:
            text = f"token::{candidate}::payload"
        else:
            text = candidate
        redacted_text = filt._redact_in_text(text)
        if should_mask and candidate:
            assert candidate not in redacted_text, label
            assert expected_fragment in redacted_text, label
        else:
            assert redacted_text == text, label

    sample_mapping = {
        "primary": openai_secret,
        "secondary": anthropic_secret,
        "note": "retain me",
        "empty": "",
        "count": 5,
        "nested": {"unchanged": True},
    }
    original_snapshot = copy.deepcopy(sample_mapping)

    redacted_mapping = filt._redact_in_mapping(sample_mapping)

    assert redacted_mapping is not sample_mapping
    assert sample_mapping == original_snapshot
    assert redacted_mapping["primary"].endswith(openai_secret[-4:])
    assert redacted_mapping["secondary"].endswith(anthropic_secret[-4:])
    assert redacted_mapping["note"] == "retain me"
    assert redacted_mapping["empty"] == ""
    assert redacted_mapping["count"] == 5
    assert redacted_mapping["nested"] == {"unchanged": True}


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
def test_json_formatter_serializes_request_context() -> None:
    """JSON formatter includes request metadata from context vars."""

    set_request_context("req-json-7", "phase-json")
    try:
        record = logging.LogRecord(
            name="devsynth.test.json.context",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="payload",  # message is required even if unused
            args=(),
            exc_info=None,
            func="test",
        )
        RequestContextFilter().filter(record)
        formatted = JSONFormatter().format(record)
    finally:
        clear_request_context()

    payload = json.loads(formatted)
    assert payload["request_id"] == "req-json-7"
    assert payload["phase"] == "phase-json"


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
def test_ensure_log_dir_redirects_absolute_outside_home(monkeypatch, tmp_path):
    """ReqID: LOG-06C — non-home absolute paths mirror under project directory."""

    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    # Use an absolute path that does not live under the user's home directory
    abs_path = os.path.join(os.sep, "var", "devsynth", "logs")

    redirected = ensure_log_dir_exists(abs_path)

    expected = tmp_path / "var" / "devsynth" / "logs"
    assert redirected == str(expected)
    assert expected.exists() and expected.is_dir()


@pytest.mark.fast
def test_ensure_log_dir_respects_project_dir_when_file_logging_disabled(
    monkeypatch, tmp_path
):
    """ReqID: LOG-06D — project redirection still applies when skipping filesystem writes."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "YES")
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))

    home_relative = os.path.join(str(Path.home()), "service", "logs")

    redirected = ensure_log_dir_exists(home_relative)

    assert redirected == home_relative
    redirected_path = Path(redirected)
    assert not redirected_path.exists()


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
        assert (
            relative_to_project.parts[-len(expected_suffix.parts) :]
            == expected_suffix.parts
        )
        assert (
            not configured_dir.exists()
        ), "Directory should not be created when file logging is off"

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


@pytest.mark.fast
def test_devsynth_logger_log_table_normalization(monkeypatch: pytest.MonkeyPatch):
    """ReqID: LOG-06E — table-driven inputs normalize extras and exceptions."""

    import src.devsynth.logging_setup as logging_setup_module

    wrapper = logging_setup_module.DevSynthLogger("devsynth.test.table")
    inner_logger = wrapper.logger
    original_log = inner_logger.log

    mock_log = MagicMock()
    inner_logger.log = mock_log

    sentinel = (RuntimeError, RuntimeError("sentinel"), None)
    monkeypatch.setattr(logging_setup_module.sys, "exc_info", lambda: sentinel)

    instance_exc = ValueError("instance-case")
    tuple_exc = (KeyError, KeyError("tuple-case"), None)

    scenarios = [
        {
            "label": "exception-instance",
            "exc_input": instance_exc,
            "extra_input": {"detail": "value", "name": "intruder", "lineno": 9},
            "stray_kwargs": {"context": "analysis", "lineno": 11},
            "expected_extra": {"detail": "value", "context": "analysis"},
        },
        {
            "label": "truthy-exc-info",
            "exc_input": True,
            "extra_input": None,
            "stray_kwargs": {"user": "alice", "process": 999, "correlation": "abc"},
            "expected_extra": {"user": "alice", "correlation": "abc"},
        },
        {
            "label": "tuple-exc-info",
            "exc_input": tuple_exc,
            "extra_input": {
                "custom": "value",
                "message": "intruder",
                "threadName": "drop",
            },
            "stray_kwargs": {"nested": {"feature": "present"}, "thread": 5},
            "expected_extra": {"custom": "value", "nested": {"feature": "present"}},
        },
    ]

    originals = []

    try:
        for scenario in scenarios:
            extra_input = scenario["extra_input"]
            if extra_input is not None:
                originals.append((scenario["label"], copy.deepcopy(extra_input)))

            wrapper._log(
                logging.WARNING,
                f"table-{scenario['label']}",
                extra=extra_input,
                exc_info=scenario["exc_input"],
                **scenario["stray_kwargs"],
            )
    finally:
        inner_logger.log = original_log
        inner_logger.handlers = []
        inner_logger.filters = []
        inner_logger.propagate = True

    assert mock_log.call_count == len(scenarios)

    for scenario, call in zip(scenarios, mock_log.call_args_list):
        (level, message, *_) = call.args
        assert level == logging.WARNING
        assert message == f"table-{scenario['label']}"

        log_kwargs = call.kwargs
        assert set(log_kwargs.keys()) == {"extra", "exc_info"}

        extra = log_kwargs["extra"]
        assert extra == scenario["expected_extra"]
        for reserved in (
            "name",
            "lineno",
            "process",
            "thread",
            "message",
            "threadName",
        ):
            assert reserved not in extra

        exc_info = log_kwargs["exc_info"]
        assert isinstance(exc_info, tuple)
        if scenario["label"] == "exception-instance":
            assert exc_info[0] is ValueError
            assert exc_info[1] is instance_exc
        elif scenario["label"] == "truthy-exc-info":
            assert exc_info is sentinel
        else:
            assert exc_info is tuple_exc

    for label, original in originals:
        scenario = next(item for item in scenarios if item["label"] == label)
        assert scenario["extra_input"] == original


@pytest.mark.fast
def test_devsynth_logger_log_does_not_mutate_extra_inputs():
    """ReqID: LOG-06C — Reserved-key filtering leaves caller extras intact."""

    wrapper = DevSynthLogger("devsynth.test.immutability")
    inner_logger = wrapper.logger
    original_log = inner_logger.log

    mock_log = MagicMock()
    inner_logger.log = mock_log

    try:
        original_extra = {"detail": "value", "name": "drop-me"}
        wrapper._log(
            logging.INFO,
            "msg",
            extra=original_extra,
            lineno=123,
            custom="kept",
            process=42,
        )
    finally:
        inner_logger.log = original_log
        inner_logger.handlers = []
        inner_logger.filters = []
        inner_logger.propagate = True

    mock_log.assert_called_once()
    kwargs = mock_log.call_args.kwargs
    assert set(kwargs.keys()) == {"extra"}
    assert kwargs["extra"] == {"detail": "value", "custom": "kept"}
    assert original_extra == {"detail": "value", "name": "drop-me"}


@pytest.mark.fast
def test_devsynth_logger_log_normalizes_truthy_exc_info(
    monkeypatch: pytest.MonkeyPatch,
):
    """ReqID: LOG-06D — ``exc_info`` coercion falls back to ``sys.exc_info`` when needed.

    Issue: issues/coverage-below-threshold.md
    """

    wrapper = DevSynthLogger("devsynth.test.excinfo")
    inner_logger = wrapper.logger
    original_log = inner_logger.log

    mock_log = MagicMock()
    inner_logger.log = mock_log

    import src.devsynth.logging_setup as logging_setup_module

    sentinel = (RuntimeError, RuntimeError("boom"), None)
    monkeypatch.setattr(logging_setup_module.sys, "exc_info", lambda: sentinel)

    try:
        wrapper._log(logging.ERROR, "truthy", exc_info=True)
        wrapper._log(logging.ERROR, "string", exc_info="boom")
    finally:
        inner_logger.log = original_log
        inner_logger.handlers = []
        inner_logger.filters = []
        inner_logger.propagate = True

    assert mock_log.call_count == 2
    truthy_kwargs = mock_log.call_args_list[0].kwargs
    string_kwargs = mock_log.call_args_list[1].kwargs
    assert truthy_kwargs["exc_info"] == sentinel
    assert string_kwargs["exc_info"] == sentinel


class _RecordCaptureHandler(logging.Handler):
    """Capture log records for direct inspection in tests."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial
        self.records.append(record)


@pytest.mark.fast
def test_configure_logging_console_only_uses_caplog(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    test_environment: dict[str, object],
) -> None:
    """configure_logging leaves only stream handlers and surfaces console output via caplog."""

    import src.devsynth.logging_setup as logging_setup_module

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    monkeypatch.setattr(logging_setup_module, "_logging_configured", False)
    monkeypatch.setattr(logging_setup_module, "_last_effective_config", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_dir", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_file", None)

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    caplog.set_level(logging.INFO)

    try:
        configure_logging(
            log_dir=str(test_environment["logs_dir"]),
            create_dir=False,
        )

        handlers = list(logging.getLogger().handlers)
        assert handlers
        assert all(not isinstance(handler, logging.FileHandler) for handler in handlers)
        assert any(isinstance(handler, logging.StreamHandler) for handler in handlers)

        root_logger = logging.getLogger()
        if caplog.handler not in root_logger.handlers:
            root_logger.addHandler(caplog.handler)
        root_logger.info("console-only sentinel")
        assert "console-only sentinel" in caplog.text
    finally:
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        for handler in original_handlers:
            logging.getLogger().addHandler(handler)

        for filt in logging.getLogger().filters[:]:
            logging.getLogger().removeFilter(filt)
        for filt in original_filters:
            logging.getLogger().addFilter(filt)

        logging.getLogger().setLevel(original_level)


@pytest.mark.fast
def test_redact_filter_masks_secret_tokens_via_caplog(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Secrets in DevSynthLogger output are redacted before reaching captured logs."""

    import src.devsynth.logging_setup as logging_setup_module

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    monkeypatch.setattr(logging_setup_module, "_logging_configured", False)
    monkeypatch.setattr(logging_setup_module, "_last_effective_config", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_dir", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_file", None)

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-987654321")
    caplog.set_level(logging.INFO)

    try:
        configure_logging(log_dir=str(tmp_path / "logs"), create_dir=False)

        root_logger = logging.getLogger()
        if caplog.handler not in root_logger.handlers:
            root_logger.addHandler(caplog.handler)

        logger = DevSynthLogger("tests.logging.redaction")
        logger.info("Token %s", "sk-secret-987654321")

        assert "tests.logging.redaction" in caplog.text
        assert "sk-secret-987654321" not in caplog.text
        assert "***REDACTED***" in caplog.text
    finally:
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        for handler in original_handlers:
            logging.getLogger().addHandler(handler)

        for filt in logging.getLogger().filters[:]:
            logging.getLogger().removeFilter(filt)
        for filt in original_filters:
            logging.getLogger().addFilter(filt)

        logging.getLogger().setLevel(original_level)


@pytest.mark.fast
def test_dev_synth_logger_handles_missing_log_file_path(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When the configured log file path is empty the logger falls back safely."""

    import src.devsynth.logging_setup as logging_setup_module

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    monkeypatch.setattr(logging_setup_module, "_logging_configured", False)
    monkeypatch.setattr(logging_setup_module, "_last_effective_config", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_dir", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_file", None)

    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    caplog.set_level(logging.INFO)

    try:
        configure_logging(
            log_dir=str(tmp_path / "logs"),
            log_file="",
            create_dir=True,
        )

        root_logger = logging.getLogger()
        if caplog.handler not in root_logger.handlers:
            root_logger.addHandler(caplog.handler)

        logger = DevSynthLogger("tests.logging.null-path")
        logger.info("null path sentinel")

        assert "null path sentinel" in caplog.text
    finally:
        current_logger = logging.getLogger()
        for handler in current_logger.handlers[:]:
            current_logger.removeHandler(handler)
            if handler not in original_handlers:
                try:
                    handler.close()
                except Exception:
                    pass
        for handler in original_handlers:
            current_logger.addHandler(handler)

        for filt in current_logger.filters[:]:
            current_logger.removeFilter(filt)
        for filt in original_filters:
            current_logger.addFilter(filt)

        current_logger.setLevel(original_level)


@pytest.mark.fast
def test_dev_synth_logger_emits_structured_extras_with_context(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Structured extras and request context propagate through DevSynthLogger._log."""

    import src.devsynth.logging_setup as logging_setup_module

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    monkeypatch.setattr(logging_setup_module, "_logging_configured", False)
    monkeypatch.setattr(logging_setup_module, "_last_effective_config", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_dir", None)
    monkeypatch.setattr(logging_setup_module, "_configured_log_file", None)

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    caplog.set_level(logging.INFO)

    try:
        configure_logging(create_dir=False)

        logger = DevSynthLogger("tests.logging.structured")
        capture = _RecordCaptureHandler()
        logger.logger.addHandler(capture)
        logger.logger.setLevel(logging.INFO)

        set_request_context("req-42", "phase-one")
        try:
            logger.info(
                "Processing batch",
                extra={"component": "runner"},
                task="sync",
            )
        finally:
            clear_request_context()
            logger.logger.removeHandler(capture)

        assert capture.records
        record = capture.records[-1]
        assert getattr(record, "component", None) == "runner"
        assert getattr(record, "task", None) == "sync"
        assert getattr(record, "request_id", None) == "req-42"
        assert getattr(record, "phase", None) == "phase-one"
    finally:
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        for handler in original_handlers:
            logging.getLogger().addHandler(handler)

        for filt in logging.getLogger().filters[:]:
            logging.getLogger().removeFilter(filt)
        for filt in original_filters:
            logging.getLogger().addFilter(filt)

        logging.getLogger().setLevel(original_level)
