"""Option parsing helpers for :mod:`devsynth.testing.run_tests`."""

from __future__ import annotations

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_parse_pytest_addopts_handles_balanced_and_unbalanced_quotes() -> None:
    """Balanced strings use :mod:`shlex` while malformed ones fallback to split."""

    tokens = rt._parse_pytest_addopts("-k 'alpha beta' --maxfail=1")
    assert tokens == ["-k", "alpha beta", "--maxfail=1"]

    fallback = rt._parse_pytest_addopts('--flag "unterminated')
    assert fallback == ["--flag", '"unterminated']

    assert rt._parse_pytest_addopts(None) == []
    assert rt._parse_pytest_addopts("   ") == []


@pytest.mark.fast
def test_addopts_has_plugin_detects_split_and_concatenated_forms() -> None:
    """Both ``-p plugin`` and ``-pplugin`` should be recognized."""

    tokens = ["-p", "pytest_cov", "-pno:cov", "--maxfail=1"]
    assert rt._addopts_has_plugin(tokens, "pytest_cov") is True
    assert rt._addopts_has_plugin(tokens, "no:cov") is True
    assert rt._addopts_has_plugin(tokens, "missing") is False


@pytest.mark.fast
def test_coverage_plugin_disabled_detects_common_overrides() -> None:
    """Explicit disables should prevent pytest-cov from being injected."""

    assert rt._coverage_plugin_disabled(["--no-cov"]) is True
    assert rt._coverage_plugin_disabled(["-p", "no:cov"]) is True
    assert rt._coverage_plugin_disabled(["-pno:pytest_cov"]) is True
    assert rt._coverage_plugin_disabled(["-k", "test_something"]) is False
