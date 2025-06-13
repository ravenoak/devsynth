import importlib
from pathlib import Path

import devsynth.config.settings as settings_module
import devsynth.logging_setup as logging_setup_module


def test_ensure_path_exists_within_project_dir(tmp_path, monkeypatch):
    project_dir = tmp_path / "project"
    outside_dir = tmp_path / "outside"
    project_dir.mkdir(exist_ok=True)
    outside_dir.mkdir(exist_ok=True)

    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    settings = importlib.reload(settings_module)

    outside_path = outside_dir / "data"
    result = settings.ensure_path_exists(str(outside_path), create=True)
    assert str(project_dir) in result
    assert not outside_path.exists()

    relative_result = settings.ensure_path_exists("rel/data", create=True)
    assert Path(relative_result) == project_dir / "rel" / "data"


def test_configure_logging_within_project_dir(tmp_path, monkeypatch):
    project_dir = tmp_path / "project"
    outside_dir = tmp_path / "outside"
    project_dir.mkdir(exist_ok=True)
    outside_dir.mkdir(exist_ok=True)

    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    logging_setup = importlib.reload(logging_setup_module)

    log_dir = outside_dir / "logs"
    log_file = log_dir / "app.log"

    logging_setup.configure_logging(
        log_dir=str(log_dir), log_file=str(log_file), create_dir=False
    )

    assert str(project_dir) in logging_setup._configured_log_dir
    assert str(project_dir) in logging_setup._configured_log_file
    assert not log_dir.exists()
