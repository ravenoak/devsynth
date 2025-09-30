"""Unit tests for the run_pipeline CLI command helpers."""

from __future__ import annotations

import json

import pytest

from devsynth.application.cli.commands.run_pipeline_cmd import _parse_report


@pytest.mark.fast
def test_parse_report_returns_mapping() -> None:
    """Valid JSON objects are converted to typed pipeline reports."""

    payload = {"status": "ok", "count": 1}
    encoded = json.dumps(payload)

    parsed = _parse_report(encoded)

    assert isinstance(parsed, dict)
    assert parsed == payload


@pytest.mark.fast
def test_parse_report_invalid_json_returns_none() -> None:
    """Invalid JSON data falls back to ``None``."""

    assert _parse_report("{not-json}") is None


@pytest.mark.fast
def test_parse_report_non_mapping_returns_none() -> None:
    """Non-object JSON payloads are ignored."""

    encoded = json.dumps([1, 2, 3])

    result = _parse_report(encoded)

    assert result is None
