"""Tests for exception logging utilities."""

import logging

import pytest

from devsynth.exceptions import DevSynthError, log_exception


@pytest.mark.fast
def test_log_exception_emits_error(caplog):
    """log_exception records the error message.

    ReqID: FR-97"""
    err = DevSynthError("boom")
    with caplog.at_level(logging.ERROR):
        log_exception(err)
    assert "boom" in caplog.text
