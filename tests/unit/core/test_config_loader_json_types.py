"""Focused tests for JSON handling in the config loader."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from textwrap import dedent

import pytest

if "yaml" not in sys.modules:
    yaml_stub = types.ModuleType("yaml")

    def _safe_load(stream):
        data = stream.read() if hasattr(stream, "read") else stream
        if not data:
            return None
        return json.loads(data)

    def _safe_dump(value, handle) -> None:
        text = json.dumps(value)
        if hasattr(handle, "write"):
            handle.write(text)
        else:  # pragma: no cover - defensive fallback
            raise TypeError("safe_dump expects a writable handle")

    yaml_stub.safe_load = _safe_load  # type: ignore[attr-defined]
    yaml_stub.safe_dump = _safe_dump  # type: ignore[attr-defined]
    sys.modules["yaml"] = yaml_stub


try:  # pragma: no cover - prefer real package if available
    from devsynth.core.config_loader import _MAX_JSON_DEPTH, CoreConfig, load_config
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    REPO_ROOT = Path(__file__).resolve().parents[3]
    MODULE_NAME = "devsynth.core.config_loader"
    MODULE_PATH = REPO_ROOT / "src" / "devsynth" / "core" / "config_loader.py"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise
    if "devsynth" not in sys.modules:
        pkg = types.ModuleType("devsynth")
        pkg.__path__ = [str(REPO_ROOT / "src" / "devsynth")]  # type: ignore[attr-defined]
        sys.modules["devsynth"] = pkg
    if "devsynth.core" not in sys.modules:
        core_pkg = types.ModuleType("devsynth.core")
        core_pkg.__path__ = [str(REPO_ROOT / "src" / "devsynth" / "core")]  # type: ignore[attr-defined]
        sys.modules["devsynth.core"] = core_pkg
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    CoreConfig = module.CoreConfig
    _MAX_JSON_DEPTH = module._MAX_JSON_DEPTH
    load_config = module.load_config


@pytest.mark.fast
def test_load_config_supports_nested_json_resources(tmp_path: Path) -> None:
    """The loader should accept nested JSON-compatible structures."""

    project_dir = tmp_path / "project"
    config_dir = project_dir / ".devsynth"
    config_dir.mkdir(parents=True, exist_ok=True)

    project_file = project_dir / "devsynth.toml"
    project_file.write_text(
        dedent(
            """
            [devsynth]
            resources = { simple = "value", number = 42, boolean = true }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = load_config(str(project_dir))

    assert cfg.resources == {"simple": "value", "number": 42, "boolean": True}


@pytest.mark.fast
def test_environment_override_preserves_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment overrides should not mutate nested resources."""

    project_dir = tmp_path / "project"
    config_dir = project_dir / ".devsynth"
    config_dir.mkdir(parents=True, exist_ok=True)

    project_file = project_dir / "devsynth.toml"
    project_file.write_text(
        dedent(
            """
            [devsynth]
            language = "python"
            resources = { simple = "test" }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DEVSYNTH_LANGUAGE", "go")

    cfg = load_config(str(project_dir))

    assert cfg.language == "go"
    assert cfg.resources == {"simple": "test"}


@pytest.mark.fast
def test_core_config_rejects_excessively_deep_resources() -> None:
    """CoreConfig should guard against runaway recursion depth."""

    too_deep: dict[str, object] = {}
    current: dict[str, object] = too_deep
    for _ in range(_MAX_JSON_DEPTH + 2):
        next_layer: dict[str, object] = {}
        current["branch"] = next_layer
        current = next_layer
    current["terminal"] = "ok"

    with pytest.raises(ValueError):
        CoreConfig(resources={"root": too_deep})
