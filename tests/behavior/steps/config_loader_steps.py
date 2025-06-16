"""Step definitions for configuration loader feature."""

import os
from pathlib import Path
from pytest_bdd import given, when, then, scenarios, parsers

import pytest
from devsynth.config.loader import load_config

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


@when('the configuration loader runs')
def run_loader(context):
    context['config'] = load_config()


@then(parsers.parse('the configuration should have the key "{key}" set to "{value}"'))
def check_value(context, key, value):
    assert getattr(context['config'], key) == value
