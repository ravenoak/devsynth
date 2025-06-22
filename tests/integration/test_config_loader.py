import logging
from devsynth.config.loader import ConfigModel, load_config, save_config


def test_load_and_save_yaml_config(tmp_path):
    cfg = ConfigModel(project_root=str(tmp_path), features={"test_flag": True})
    path = save_config(cfg, path=str(tmp_path))
    assert path.name == "devsynth.yml"

    loaded = load_config(tmp_path)
    assert loaded.features == {"test_flag": True}
    assert loaded.version == ConfigModel.version


def test_load_and_save_pyproject_config(tmp_path):
    cfg = ConfigModel(project_root=str(tmp_path), features={"test_flag": True})
    path = save_config(cfg, use_pyproject=True, path=str(tmp_path))
    assert path.name == "pyproject.toml"

    loaded = load_config(tmp_path)
    assert loaded.features == {"test_flag": True}
    assert loaded.version == ConfigModel.version


def test_version_mismatch_warning_yaml(tmp_path, caplog):
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "devsynth.yml").write_text("version: '0.0'\n")

    caplog.set_level(logging.WARNING)
    load_config(tmp_path)
    assert any("version" in rec.message for rec in caplog.records)


def test_version_mismatch_warning_pyproject(tmp_path, caplog):
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nversion='0.0'\n")

    caplog.set_level(logging.WARNING)
    load_config(tmp_path)
    assert any("version" in rec.message for rec in caplog.records)
