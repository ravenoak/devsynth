"""Logging invariants for handler wiring, redaction, and context switching."""

from __future__ import annotations

import importlib
import json
import logging
from collections.abc import Iterator, Mapping
from pathlib import Path
from types import ModuleType
from collections.abc import Sequence

import pytest


@pytest.fixture()
def reloaded_logging_setup() -> Iterator[ModuleType]:
    """Reload :mod:`devsynth.logging_setup` with a pristine root logger."""

    import devsynth.logging_setup as logging_setup

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_filters = list(root_logger.filters)
    original_level = root_logger.level

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # pragma: no cover - defensive guard
            pass
    for filt in root_logger.filters[:]:
        root_logger.removeFilter(filt)

    reloaded = importlib.reload(logging_setup)

    try:
        yield reloaded
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:  # pragma: no cover - defensive guard
                pass
        for handler in original_handlers:
            root_logger.addHandler(handler)
        for filt in original_filters:
            root_logger.addFilter(filt)
        root_logger.setLevel(original_level)
        importlib.reload(logging_setup)


def _file_handlers() -> Sequence[logging.FileHandler]:
    root_logger = logging.getLogger()
    return [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
    ]


@pytest.mark.fast
def test_configure_logging_is_idempotent_for_handlers(
    reloaded_logging_setup: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-INV-01 — Handler wiring remains stable across repeated config."""

    logging_setup = reloaded_logging_setup

    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DEVSYNTH_LOG_FILENAME", "cli.jsonl")
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)

    logging_setup.configure_logging()
    initial_handlers = tuple(_file_handlers())
    assert len(initial_handlers) == 1
    initial_path = Path(initial_handlers[0].baseFilename)
    assert initial_path.name == "cli.jsonl"

    logging_setup.configure_logging()
    repeated_handlers = tuple(_file_handlers())
    assert repeated_handlers == initial_handlers
    assert Path(logging_setup.get_log_file()) == initial_path


@pytest.mark.fast
def test_redact_secrets_filter_masks_known_tokens(
    reloaded_logging_setup: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-INV-02 — Redaction filter masks secrets in messages and extras."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-example1234567890")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret-abcdef")

    logging_setup = reloaded_logging_setup
    filt = logging_setup.RedactSecretsFilter()

    record = logging.LogRecord(
        name="devsynth.tests.redaction",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="Token sk-example1234567890 should be redacted",
        args=(),
        exc_info=None,
    )
    record.extra = {"api_key": "anthropic-secret-abcdef"}

    assert filt.filter(record)
    assert "sk-example1234567890" not in record.msg
    assert "***REDACTED***7890" in record.msg
    assert record.extra["api_key"].startswith("***REDACTED***")
    assert record.extra["api_key"].endswith("cdef")


@pytest.mark.fast
def test_redact_secrets_filter_redacts_payload_and_details(
    reloaded_logging_setup: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-INV-02b — Payload and detail extras are scrubbed."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-example987654321")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret-654321")

    logging_setup = reloaded_logging_setup
    filt = logging_setup.RedactSecretsFilter()

    record = logging.LogRecord(
        name="devsynth.tests.payload",
        level=logging.WARNING,
        pathname=__file__,
        lineno=0,
        msg="Token sk-example987654321 and anthropic-secret-654321",
        args=("anthropic-secret-654321",),
        exc_info=None,
    )
    record.payload = {"token": "sk-example987654321"}
    record.details = {"nested": "anthropic-secret-654321"}
    record.extra = {"note": "sk-example987654321"}

    assert filt.filter(record)
    assert "***REDACTED***4321" in record.msg
    assert record.args[0].startswith("***REDACTED***")
    assert record.payload["token"].startswith("***REDACTED***")
    assert record.details["nested"].startswith("***REDACTED***")
    assert record.extra["note"].startswith("***REDACTED***")


@pytest.mark.fast
def test_redact_secrets_filter_survives_mapping_errors(
    reloaded_logging_setup: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-INV-02c — Redaction errors never break logging."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-errormap1234")
    logging_setup = reloaded_logging_setup
    filt = logging_setup.RedactSecretsFilter()

    class ExplosiveMapping(Mapping[str, str]):
        def __iter__(self):  # pragma: no cover - unused iteration branch
            return iter(())

        def __len__(self) -> int:  # pragma: no cover - not queried
            return 1

        def __getitem__(self, key: str) -> str:  # pragma: no cover - not queried
            raise KeyError(key)

        def items(self):  # noqa: D401 - mimic Mapping API
            raise RuntimeError("explode")

    record = logging.LogRecord(
        name="devsynth.tests.payload",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="sk-errormap1234",
        args=(),
        exc_info=None,
    )
    record.extra = ExplosiveMapping()

    assert filt.filter(record)
    assert record.msg.endswith("1234")


@pytest.mark.fast
def test_cli_to_test_context_switch_updates_log_destination(
    reloaded_logging_setup: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: LOG-INV-03 — Switching contexts rewires file handlers deterministically."""

    logging_setup = reloaded_logging_setup

    cli_dir = tmp_path / "cli"
    monkeypatch.setenv("DEVSYNTH_LOG_DIR", str(cli_dir))
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)
    monkeypatch.delenv("DEVSYNTH_NO_FILE_LOGGING", raising=False)

    logging_setup.configure_logging()
    cli_handlers = tuple(_file_handlers())
    assert len(cli_handlers) == 1
    cli_path = Path(cli_handlers[0].baseFilename)
    assert cli_path.is_relative_to(cli_dir)

    project_dir = tmp_path / "project"
    project_dir.mkdir(exist_ok=True)
    monkeypatch.delenv("DEVSYNTH_LOG_DIR", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))

    logging_setup.configure_logging()
    test_handlers = tuple(_file_handlers())
    assert len(test_handlers) == 1
    test_path = Path(test_handlers[0].baseFilename)
    assert test_path.is_relative_to(project_dir)
    assert test_path != cli_path
    assert Path(logging_setup.get_log_file()) == test_path


@pytest.mark.fast
def test_json_formatter_includes_structured_extras(
    reloaded_logging_setup: ModuleType,
) -> None:
    """ReqID: LOG-INV-04 — Structured extras persist in JSON payloads."""

    logging_setup = reloaded_logging_setup
    formatter = logging_setup.JSONFormatter()

    record = logging.LogRecord(
        name="devsynth.tests.json",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Structured payload",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    record.phase = "rendering"
    record.details = {"hint": "ok"}
    record.payload = {"status": "success"}
    record.caller_module = "expected.module"
    record.caller_function = "expected_func"
    record.caller_line = 99

    output = formatter.format(record)
    payload = json.loads(output)

    assert payload["request_id"] == "req-123"
    assert payload["phase"] == "rendering"
    assert payload["details"] == {"hint": "ok"}
    assert payload["payload"] == {"status": "success"}
    assert payload["module"] == "expected.module"
    assert payload["function"] == "expected_func"
    assert payload["line"] == 99
