"""Tests for JSON validation helpers used by the config loader."""

from __future__ import annotations

from pathlib import Path

import importlib.util
import json
import sys
import types

import pytest

# Provide a lightweight TOML shim for environments missing the optional dependency.
if "toml" not in sys.modules:  # pragma: no cover - defensive import guard
    toml_stub = types.ModuleType("toml")

    def _load(path: Path) -> dict[str, object]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _dump(data: dict[str, object], handle) -> None:
        json.dump(data, handle)

    toml_stub.load = _load  # type: ignore[attr-defined]
    toml_stub.dump = _dump  # type: ignore[attr-defined]
    sys.modules["toml"] = toml_stub


if "yaml" not in sys.modules:  # pragma: no cover - defensive import guard
    yaml_stub = types.ModuleType("yaml")

    def _safe_load(stream: object) -> object:
        if isinstance(stream, str):
            return json.loads(stream)
        return json.load(stream)

    def _safe_dump(data: object, handle) -> None:
        json.dump(data, handle)

    yaml_stub.safe_load = _safe_load  # type: ignore[attr-defined]
    yaml_stub.safe_dump = _safe_dump  # type: ignore[attr-defined]
    sys.modules["yaml"] = yaml_stub


MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "devsynth" / "core" / "config_loader.py"
)
spec = importlib.util.spec_from_file_location("test_config_loader_module", MODULE_PATH)
assert spec and spec.loader, "Failed to locate config_loader module for tests"
config_loader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = config_loader
spec.loader.exec_module(config_loader)

_MAX_JSON_DEPTH = config_loader._MAX_JSON_DEPTH
_is_json_object = config_loader._is_json_object
load_config = config_loader.load_config


@pytest.mark.fast
def test_load_config_handles_nested_resources(tmp_path: Path) -> None:
    """Nested JSON payloads should be preserved without recursion issues."""

    config_dir = tmp_path / ".devsynth"
    config_dir.mkdir()
    (config_dir / "project.yaml").write_text(
        json.dumps(
            {
                "resources": {
                    "pipeline": {
                        "steps": [
                            {
                                "name": "ingest",
                                "params": {
                                    "retries": 3,
                                    "thresholds": [0.8, 0.95],
                                    "metadata": {
                                        "tags": ["qa", "release"],
                                        "window": {"size": 5, "units": "minutes"},
                                    },
                                },
                            }
                        ]
                    }
                }
            }
        )
    )

    config = load_config(str(tmp_path))

    assert config.resources is not None
    params = config.resources["pipeline"]["steps"][0]["params"]
    assert params["retries"] == 3
    assert params["metadata"]["window"]["size"] == 5


@pytest.mark.fast
def test_environment_overrides_take_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment values should override file-based configuration settings."""

    config_dir = tmp_path / ".devsynth"
    config_dir.mkdir()
    (config_dir / "project.yaml").write_text(
        json.dumps(
            {
                "language": "python",
                "goals": "automate testing",
                "resources": {"feature_flags": {"nested": True}},
            }
        )
    )

    monkeypatch.setenv("DEVSYNTH_LANGUAGE", "rust")
    monkeypatch.setenv("DEVSYNTH_GOALS", "ship alpha build")

    config = load_config(str(tmp_path))

    assert config.language == "rust"
    assert config.goals == "ship alpha build"
    assert config.resources == {
        "feature_flags": {"nested": True}
    }, "Nested JSON resources should remain intact"


@pytest.mark.fast
def test_json_validation_limits_depth(tmp_path: Path) -> None:
    """Overly deep JSON structures are ignored to prevent recursive expansion."""

    deep_payload: dict[str, object] = {}
    current = deep_payload
    for index in range(_MAX_JSON_DEPTH + 2):
        next_layer: dict[str, object] = {}
        current[f"layer_{index}"] = next_layer
        current = next_layer

    assert not _is_json_object({"deep": deep_payload})

    config_dir = tmp_path / ".devsynth"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "project.yaml").write_text(
        json.dumps({"resources": {"deep": deep_payload}})
    )

    config = load_config(str(tmp_path))
    assert config.resources == {}, "Overly deep JSON should be ignored"
