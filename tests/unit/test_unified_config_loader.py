import logging
from pathlib import Path
import yaml
import toml

from devsynth.config.unified_loader import UnifiedConfigLoader


def test_load_from_yaml(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.use_pyproject
    assert unified.path == cfg_dir / "devsynth.yml"
    assert unified.config.language == "python"


def test_load_from_pyproject(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth]\nlanguage = 'python'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject
    assert unified.path == toml_path
    assert unified.config.language == "python"


def test_save_and_exists(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".devsynth"
    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.exists()

    unified.set_language("python")
    save_path = unified.save()

    assert save_path == cfg_dir / "devsynth.yml"
    assert unified.exists()

    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.exists()
    save_path = unified.save()

    assert save_path == unified.path


def test_missing_files(tmp_path: Path) -> None:
    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.exists()
    assert unified.path == tmp_path / ".devsynth" / "devsynth.yml"


def test_version_mismatch_warning(tmp_path: Path, caplog) -> None:
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("version: '0.0'\n")

    caplog.set_level(logging.WARNING)
    UnifiedConfigLoader.load(tmp_path)

    assert any("version" in rec.message for rec in caplog.records)


def test_loader_save_function_yaml(tmp_path: Path) -> None:
    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language("go")
    path = UnifiedConfigLoader.save(cfg)
    data = yaml.safe_load(path.read_text())
    assert data["language"] == "go"


def test_loader_save_function_pyproject(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth]\n")

    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language("rust")
    path = UnifiedConfigLoader.save(cfg)
    data = toml.load(path)
    assert data["tool"]["devsynth"]["language"] == "rust"
