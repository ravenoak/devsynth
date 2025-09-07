import io
import json
import logging
import os
from pathlib import Path

import pytest

from src.devsynth.logging_setup import (
    JSONFormatter,
    RedactSecretsFilter,
    RequestContextFilter,
    clear_request_context,
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
    assert data["exception"]["type"] == "ValueError"
    # Ensure traceback lines are included
    tb = data["exception"]["traceback"]
    assert isinstance(tb, list) and any("ValueError: boom" in line for line in tb)


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
