"""Unit tests for the internal _parse_feature_options helper.

Covers edge cases to improve targeted coverage for run_tests_cmd module.
ReqID: C3 (coverage ≥90% goal - incremental step)
"""

import pytest

from devsynth.application.cli.commands.run_tests_cmd import _parse_feature_options


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_parse_feature_options_empty_list_returns_empty_dict():
    assert _parse_feature_options([]) == {}


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_parse_feature_options_single_name_defaults_true():
    result = _parse_feature_options(["experimental"])
    assert result == {"experimental": True}


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_parse_feature_options_name_equals_false_variants():
    # Ensure common false string variants are all handled as False when provided explicitly
    for val in ["false", "no", "0", "False", "NO", "0"]:
        result = _parse_feature_options([f"logging={val}"])
        assert result == {"logging": False}


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_parse_feature_options_name_equals_true_variants():
    for val in ["true", "yes", "on", "1", "TrUe", "YES"]:
        result = _parse_feature_options([f"feature_x={val}"])
        assert result == {"feature_x": True}
