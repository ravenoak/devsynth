"""Focused tests for config loader validation helpers."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

if "yaml" not in sys.modules:
    yaml_stub = types.ModuleType("yaml")

    def _safe_load(stream):
        data = stream.read() if hasattr(stream, "read") else stream
        if not data:
            return None
        return json.loads(data)

    yaml_stub.safe_load = _safe_load  # type: ignore[attr-defined]
    sys.modules["yaml"] = yaml_stub

try:  # pragma: no cover - prefer installed package
    from devsynth.core.config_loader import (
        _MAX_JSON_DEPTH,
        _coerce_core_config_data,
        _coerce_issue_provider_config,
        _coerce_json_object,
        _coerce_mvuu_config,
        _coerce_mvuu_issues,
        _is_directory_map,
        _load_toml,
        _load_yaml,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    REPO_ROOT = Path(__file__).resolve().parents[3]
    MODULE_NAME = "devsynth.core.config_loader"
    MODULE_PATH = REPO_ROOT / "src" / "devsynth" / "core" / "config_loader.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    _MAX_JSON_DEPTH = module._MAX_JSON_DEPTH
    _coerce_core_config_data = module._coerce_core_config_data
    _coerce_issue_provider_config = module._coerce_issue_provider_config
    _coerce_json_object = module._coerce_json_object
    _coerce_mvuu_config = module._coerce_mvuu_config
    _coerce_mvuu_issues = module._coerce_mvuu_issues
    _is_directory_map = module._is_directory_map
    _load_toml = module._load_toml
    _load_yaml = module._load_yaml


def _build_nested_value(levels: int) -> object:
    value: object = "terminal"
    for index in range(levels):
        value = {f"level_{index}": value}
    return value


@pytest.mark.fast
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            {"base_url": "https://api.example.com", "token": "secret"},
            {"base_url": "https://api.example.com", "token": "secret"},
        ),
        (
            {"base_url": "https://api.example.com", "token": 42, "extra": "ignored"},
            {"base_url": "https://api.example.com"},
        ),
        ({"token": "secret"}, {"token": "secret"}),
        ({"token": None}, None),
        ("not-a-mapping", None),
    ],
)
def test_coerce_issue_provider_config_filters_payloads(raw, expected):
    assert _coerce_issue_provider_config(raw) == expected


@pytest.mark.fast
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "github": {"base_url": "https://api.github.com", "token": "gho_123"},
                "jira": {"base_url": "https://jira.example.com", "token": "jira_456"},
            },
            {
                "github": {"base_url": "https://api.github.com", "token": "gho_123"},
                "jira": {"base_url": "https://jira.example.com", "token": "jira_456"},
            },
        ),
        (
            {
                "github": {"token": "gho_123"},
                "unexpected": {"token": "ignored"},
            },
            {"github": {"token": "gho_123"}},
        ),
        ({"github": {"base_url": 123}}, None),
        ("not-a-mapping", None),
    ],
)
def test_coerce_mvuu_issues_only_accepts_known_providers(payload, expected):
    assert _coerce_mvuu_issues(payload) == expected


@pytest.mark.fast
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "issues": {
                    "github": {"base_url": "https://api.github.com", "token": "gho_123"}
                }
            },
            {
                "issues": {
                    "github": {"base_url": "https://api.github.com", "token": "gho_123"}
                }
            },
        ),
        ({"issues": {"github": {"base_url": 123}}}, {}),
        ({"unexpected": "value"}, {}),
    ],
)
def test_coerce_mvuu_config_collapses_invalid_sections(payload, expected):
    assert _coerce_mvuu_config(payload) == expected


@pytest.mark.fast
@pytest.mark.parametrize(
    ("directories", "is_valid", "expected"),
    [
        (
            {"src": ["src"], "tests": ["tests"]},
            True,
            {
                "directories": {"src": ["src"], "tests": ["tests"]},
                "goals": None,
                "constraints": None,
                "priority": None,
            },
        ),
        (
            {"src": ["src", 1]},
            False,
            {"goals": None, "constraints": None, "priority": None},
        ),
        (
            {"src": "not-a-list"},
            False,
            {"goals": None, "constraints": None, "priority": None},
        ),
        (
            "not-a-mapping",
            False,
            {"goals": None, "constraints": None, "priority": None},
        ),
    ],
)
def test_directory_map_validation_and_coercion(directories, is_valid, expected):
    assert _is_directory_map(directories) is is_valid
    result = _coerce_core_config_data({"directories": directories})
    assert result == expected


@pytest.mark.fast
@pytest.mark.parametrize(
    ("levels", "should_succeed"),
    [
        (((_MAX_JSON_DEPTH - 1) // 2), True),
        (((_MAX_JSON_DEPTH - 1) // 2) + 1, False),
    ],
)
def test_coerce_json_object_enforces_depth_limit(levels, should_succeed):
    nested = {"root": _build_nested_value(levels)}
    result = _coerce_json_object(nested)
    if should_succeed:
        assert result == nested
        assert result is not nested
    else:
        assert result is None


@pytest.mark.fast
def test_load_yaml_returns_coerced_core_config_data(tmp_path):
    yaml_path = tmp_path / "project.yaml"
    yaml_path.write_text(
        json.dumps(
            {
                "project_root": "/workspace/project",
                "language": "python",
                "directories": {"src": ["src"], "docs": ["docs"]},
                "mvuu": {
                    "issues": {
                        "github": {
                            "base_url": "https://api.github.com",
                            "token": "secret",
                        },
                        "gitlab": {
                            "base_url": "https://gitlab.example.com",
                        },
                    }
                },
                "resources": {"pipelines": {"nightly": {"steps": ["lint"]}}},
            }
        ),
        encoding="utf-8",
    )

    result = _load_yaml(yaml_path)

    assert result == {
        "project_root": "/workspace/project",
        "language": "python",
        "directories": {"src": ["src"], "docs": ["docs"]},
        "resources": {"pipelines": {"nightly": {"steps": ["lint"]}}},
        "goals": None,
        "constraints": None,
        "priority": None,
        "mvuu": {
            "issues": {
                "github": {
                    "base_url": "https://api.github.com",
                    "token": "secret",
                }
            }
        },
    }


@pytest.mark.fast
def test_load_toml_returns_coerced_core_config_data(tmp_path):
    toml_path = tmp_path / "devsynth.toml"
    toml_path.write_text(
        "\n".join(
            [
                "[tool.devsynth]",
                "language = 'rust'",
                "directories = { source = ['src'], tests = ['tests'] }",
                "mvuu = { issues = { jira = { base_url = 'https://jira.example.com', token = 'jira_456', extra = 'ignore-me' } } }",
            ]
        ),
        encoding="utf-8",
    )

    result = _load_toml(toml_path)

    assert result == {
        "language": "rust",
        "directories": {"source": ["src"], "tests": ["tests"]},
        "goals": None,
        "constraints": None,
        "priority": None,
        "mvuu": {
            "issues": {
                "jira": {
                    "base_url": "https://jira.example.com",
                    "token": "jira_456",
                }
            }
        },
    }
