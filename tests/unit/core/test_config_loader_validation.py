"""Focused tests for config loader validation helpers."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from copy import deepcopy
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
        CoreConfig,
        _coerce_core_config_data,
        _coerce_issue_provider_config,
        _coerce_json_object,
        _coerce_mvuu_config,
        _coerce_mvuu_issues,
        _is_directory_map,
        _load_toml,
        _load_yaml,
        _parse_env,
        load_config,
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
    _parse_env = module._parse_env
    CoreConfig = module.CoreConfig
    load_config = module.load_config
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


@pytest.mark.fast
@pytest.mark.parametrize(
    ("env_values", "expected"),
    [
        pytest.param(
            {"DEVSYNTH_LANGUAGE": "rust"},
            {"language": "rust"},
            id="single_override",
        ),
        pytest.param(
            {
                "DEVSYNTH_PRIORITY": "p1",
                "DEVSYNTH_GOALS": "ship",
            },
            {"priority": "p1", "goals": "ship"},
            id="multiple_fields",
        ),
        pytest.param(
            {
                "DEVSYNTH_STRUCTURE": "monorepo",
                "UNRELATED": "ignore-me",
            },
            {"structure": "monorepo"},
            id="ignores_irrelevant_keys",
        ),
    ],
)
def test_parse_env_extracts_known_overrides(env_values, expected, monkeypatch):
    """Exercise env parsing; marked fast because it only touches in-memory state."""

    defaults = CoreConfig(project_root="/workspace/project")

    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    try:
        result = _parse_env(defaults)
    finally:
        for key in env_values:
            monkeypatch.delenv(key, raising=False)

    assert result == expected


@pytest.mark.fast
def test_load_config_merges_sources_without_mutating_resources(tmp_path, monkeypatch):
    """Ensure precedence order stays intact; filesystem work remains minimal and fast."""

    project_root = tmp_path / "project"
    project_root.mkdir(exist_ok=True)
    home_dir = tmp_path / "home"
    home_dir.mkdir(exist_ok=True)
    config_dir = home_dir / ".devsynth" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    global_payload = {
        "language": "typescript",
        "resources": {
            "pipelines": {"nightly": {"steps": ["lint"]}},
        },
        "mvuu": {
            "issues": {
                "github": {
                    "base_url": "https://api.github.com",
                    "token": "gho_global",
                }
            }
        },
    }
    (config_dir / "global_config.yaml").write_text(
        json.dumps(global_payload),
        encoding="utf-8",
    )

    project_dir = project_root / ".devsynth"
    project_dir.mkdir(exist_ok=True)
    project_payload = {
        "structure": "monorepo",
        "resources": {
            "pipelines": {"nightly": {"steps": ["test", "deploy"]}},
        },
    }
    (project_dir / "project.yaml").write_text(
        json.dumps(project_payload),
        encoding="utf-8",
    )

    mvuu_payload = {
        "issues": {
            "jira": {
                "base_url": "https://jira.example.com",
                "token": "jira_project",
            }
        }
    }
    (project_dir / "mvu.yml").write_text(json.dumps(mvuu_payload), encoding="utf-8")

    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("DEVSYNTH_LANGUAGE", "python-env")
    monkeypatch.setenv("DEVSYNTH_PRIORITY", "p0")

    expected_resources = deepcopy(project_payload["resources"])

    try:
        config = load_config(str(project_root))
        assert config.project_root == str(project_root)
        assert config.structure == "monorepo"
        assert config.language == "python-env"
        assert config.priority == "p0"
        assert config.mvuu == mvuu_payload
        assert config.resources == expected_resources
        assert config.resources is not expected_resources

        if config.resources is not None:
            config.resources["pipelines"]["nightly"]["steps"].append("mutated")

        config_again = load_config(str(project_root))
        assert config_again.resources == expected_resources
    finally:
        for key in ("DEVSYNTH_LANGUAGE", "DEVSYNTH_PRIORITY", "HOME"):
            monkeypatch.delenv(key, raising=False)


@pytest.mark.fast
@pytest.mark.parametrize(
    ("mvuu_payload", "expected"),
    [
        pytest.param(
            {
                "issues": {
                    "github": {
                        "base_url": "https://api.github.com",
                        "token": "gho_token",
                        "extra": "ignored",
                    }
                }
            },
            {
                "issues": {
                    "github": {
                        "base_url": "https://api.github.com",
                        "token": "gho_token",
                    }
                }
            },
            id="github_only",
        ),
        pytest.param(
            {
                "issues": {
                    "jira": {
                        "base_url": "https://jira.example.com",
                        "token": "jira_token",
                    }
                }
            },
            {
                "issues": {
                    "jira": {
                        "base_url": "https://jira.example.com",
                        "token": "jira_token",
                    }
                }
            },
            id="jira_only",
        ),
        pytest.param(
            {
                "issues": {
                    "github": {
                        "base_url": "https://api.github.com",
                        "token": "gho_both",
                    },
                    "jira": {
                        "base_url": "https://jira.example.com",
                        "token": "jira_both",
                    },
                }
            },
            {
                "issues": {
                    "github": {
                        "base_url": "https://api.github.com",
                        "token": "gho_both",
                    },
                    "jira": {
                        "base_url": "https://jira.example.com",
                        "token": "jira_both",
                    },
                }
            },
            id="both_providers",
        ),
    ],
)
def test_load_config_normalizes_mvuu_with_env_overrides(
    mvuu_payload, expected, tmp_path, monkeypatch
):
    """Exercise MVUU/env precedence; fast because fixtures only touch tmp_path files."""

    home_dir = tmp_path / "home"
    home_dir.mkdir(exist_ok=True)
    project_root = tmp_path / "workspace"
    project_root.mkdir(exist_ok=True)
    project_dir = project_root / ".devsynth"
    project_dir.mkdir(exist_ok=True)

    (project_dir / "project.yaml").write_text(
        json.dumps({"structure": "single_package"}),
        encoding="utf-8",
    )
    (project_dir / "mvu.yml").write_text(json.dumps(mvuu_payload), encoding="utf-8")

    monkeypatch.setenv("HOME", str(home_dir))

    env_values = {
        "DEVSYNTH_LANGUAGE": "env-lang",
        "DEVSYNTH_GOALS": "deliver",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    try:
        config = load_config(str(project_root))
        assert config.language == "env-lang"
        assert config.goals == "deliver"
        assert config.mvuu == expected
    finally:
        for key in (*env_values.keys(), "HOME"):
            monkeypatch.delenv(key, raising=False)
