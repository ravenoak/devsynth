"""Unit tests for MemoryErrorLogger."""

import pytest

from devsynth.application.memory.error_logger import MemoryErrorLogger


@pytest.mark.fast
def test_log_error_enforces_max_errors():
    """Logging beyond `max_errors` retains only the most recent entries.

    ReqID: MEM-ERR-LOG-001"""
    logger = MemoryErrorLogger(max_errors=5, persist_errors=False)
    for i in range(7):
        try:
            raise ValueError(f"error {i}")
        except ValueError as exc:  # pragma: no cover - we expect the exception
            logger.log_error("op", f"adapter{i}", exc)

    assert len(logger.errors) == 5
    assert logger.errors[0]["error_message"] == "error 2"


@pytest.mark.fast
def test_persist_errors_respects_toggle(tmp_path):
    """Errors persist to disk only when enabled.

    ReqID: MEM-ERR-LOG-002"""
    log_dir = tmp_path / "logs"
    logger = MemoryErrorLogger(max_errors=5, log_dir=str(log_dir), persist_errors=True)
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:  # pragma: no cover
        logger.log_error("store", "adapter", exc)
    assert len(list(log_dir.iterdir())) == 1

    log_dir2 = tmp_path / "no_persist"
    logger = MemoryErrorLogger(
        max_errors=5, log_dir=str(log_dir2), persist_errors=False
    )
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:  # pragma: no cover
        logger.log_error("store", "adapter", exc)
    assert not log_dir2.exists()


@pytest.mark.fast
def test_get_recent_errors_and_summary():
    """Filtering and summaries reflect logged error details.

    ReqID: MEM-ERR-LOG-003"""
    logger = MemoryErrorLogger(max_errors=10, persist_errors=False)

    try:
        raise ValueError("v1")
    except ValueError as exc:  # pragma: no cover
        logger.log_error("store", "adapter1", exc)

    try:
        raise KeyError("missing")
    except KeyError as exc:  # pragma: no cover
        logger.log_error("retrieve", "adapter1", exc)

    try:
        raise ValueError("v2")
    except ValueError as exc:  # pragma: no cover
        logger.log_error("store", "adapter2", exc)

    assert len(logger.get_recent_errors(operation="store")) == 2
    assert len(logger.get_recent_errors(adapter_name="adapter1")) == 2
    assert len(logger.get_recent_errors(error_type="ValueError")) == 2

    summary = logger.get_error_summary()
    assert summary["total_errors"] == 3
    assert summary["by_adapter"] == {"adapter1": 2, "adapter2": 1}
    assert summary["by_operation"] == {"store": 2, "retrieve": 1}
    assert summary["by_error_type"] == {"ValueError": 2, "KeyError": 1}
