"""Step definitions for configuration loader feature."""

import os
from pathlib import Path
from pytest_bdd import given, when, then, scenarios, parsers

import pytest
from devsynth.config.loader import load_config, save_config, ConfigModel

scenarios('../features/config_loader.feature')


@pytest.fixture
def context():
    return {}


@given('a project with a devsynth.yml file')
def project_with_yaml(tmp_path, monkeypatch):
    dev_dir = tmp_path / '.devsynth'
    dev_dir.mkdir()
    (dev_dir / 'devsynth.yml').write_text('language: python\n')
    monkeypatch.chdir(tmp_path)


@given('a project with a pyproject.toml containing a [tool.devsynth] section')
def project_with_toml(tmp_path, monkeypatch):
    (tmp_path / 'pyproject.toml').write_text('[tool.devsynth]\nlanguage = "python"\n')
    monkeypatch.chdir(tmp_path)


@given('an empty project directory')
def empty_project_dir(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    context['root'] = tmp_path


@when('I save a default configuration')
def save_default_config(context):
    cfg = ConfigModel(project_root=str(context['root']))
    context['cfg_path'] = save_config(cfg, path=str(context['root']))


@then('a devsynth.yml file should be created')
def check_cfg_created(context):
    assert context['cfg_path'].exists()


@when('the configuration loader runs')
def run_loader(context):
    context['config'] = load_config()


@then(parsers.parse('the configuration should have the key "{key}" set to "{value}"'))
def check_value(context, key, value):
    assert getattr(context['config'], key) == value
