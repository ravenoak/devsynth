"""Tests for optional dependency behaviour in the config loader."""

from __future__ import annotations

import importlib.util
import io
import os
import sys
from pathlib import Path

import pytest

CONFIG_LOADER_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "devsynth"
    / "core"
    / "config_loader.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "devsynth.core.config_loader_under_test",
    CONFIG_LOADER_PATH,
)
assert _SPEC and _SPEC.loader, "Failed to locate config_loader module"
_config_loader = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, _config_loader)
_SPEC.loader.exec_module(_config_loader)

CoreConfig = _config_loader.CoreConfig
_dump_toml_mapping = _config_loader._dump_toml_mapping
_load_toml_mapping = _config_loader._load_toml_mapping
save_global_config = _config_loader.save_global_config

pytestmark = pytest.mark.fast


def _patch_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """Redirect ``os.path.expanduser`` to the provided home directory."""

    original_expanduser = os.path.expanduser

    def _expanduser(path: str) -> str:
        if path == "~":
            return str(home)
        return original_expanduser(path)

    monkeypatch.setattr(os.path, "expanduser", _expanduser)


def test_load_toml_mapping_requires_optional_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_load_toml_mapping raises when neither toml nor tomllib is available."""

    config_path = tmp_path / "config.toml"
    config_path.write_text("language = 'python'\n", encoding="utf-8")

    monkeypatch.setattr(_config_loader, "_toml_module", None)
    monkeypatch.setattr(_config_loader, "tomllib", None)

    with pytest.raises(RuntimeError, match="TOML parsing requires the 'toml' package"):
        _load_toml_mapping(config_path)


def test_dump_toml_mapping_requires_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_dump_toml_mapping raises when the optional toml package is missing."""

    monkeypatch.setattr(_config_loader, "_toml_module", None)

    with pytest.raises(
        RuntimeError, match="Writing TOML requires the optional 'toml' dependency"
    ):
        _dump_toml_mapping({}, io.StringIO())


def test_save_global_config_handles_missing_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """save_global_config fails for YAML without PyYAML but still writes TOML."""

    _patch_home(monkeypatch, tmp_path)
    monkeypatch.setattr(_config_loader, "yaml", None, raising=False)
    if getattr(_config_loader, "_toml_module", None) is None:

        class _TomlStub:
            @staticmethod
            def dump(data: dict, handle) -> None:  # pragma: no cover - trivial stub
                handle.write("[devsynth]\n")

        monkeypatch.setattr(_config_loader, "_toml_module", _TomlStub)

    config = CoreConfig(language="python")

    with pytest.raises(
        RuntimeError, match="PyYAML is required to write YAML configuration files"
    ):
        save_global_config(config, use_toml=False)

    toml_path = save_global_config(config, use_toml=True)
    assert toml_path.suffix == ".toml"
    assert toml_path.exists()
    assert toml_path.parent == tmp_path / ".devsynth" / "config"
