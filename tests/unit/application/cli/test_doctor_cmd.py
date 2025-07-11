"""Tests for the ``doctor`` CLI command."""
from textwrap import dedent
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
import importlib.util
import pytest
spec = importlib.util.spec_from_file_location('doctor_cmd', Path(__file__).
    parents[4] / 'src' / 'devsynth' / 'application' / 'cli' / 'commands' /
    'doctor_cmd.py')
doctor_cmd = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(doctor_cmd)


def _patch_validation_loader():
    """Return a context manager patching ``spec_from_file_location`` for the script."""
    real_spec = doctor_cmd.importlib.util.spec_from_file_location

    def fake_spec(name, location, *args, **kwargs):
        path = Path(__file__).parents[4] / 'scripts' / 'validate_config.py'
        return real_spec(name, path, *args, **kwargs)
    return patch.object(doctor_cmd.importlib.util,
        'spec_from_file_location', side_effect=fake_spec)


def test_doctor_cmd_old_python_and_missing_env_warn_succeeds(monkeypatch):
    """Missing configs, old Python and absent API keys should trigger warnings.

ReqID: N/A"""
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 10, 0))
    cfg = SimpleNamespace()
    cfg.exists = lambda : False
    with _patch_validation_loader(), patch.object(doctor_cmd, 'load_config',
        return_value=cfg), patch.object(doctor_cmd.bridge, 'print'
        ) as mock_print:
        doctor_cmd.doctor_cmd('config')
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert 'No project configuration found' in output
        assert 'Python 3.12 or higher' in output
        assert 'Missing environment variables' in output


VALID_CONFIG = dedent(
    """
    application:
      name: App
      version: "1.0"
    logging:
      level: INFO
      format: "%(message)s"
    memory:
      default_store: kuzu
      stores:
        chromadb:
          enabled: true
        kuzu: {}
        faiss:
          enabled: false
    llm:
      default_provider: openai
      providers:
        openai:
          enabled: true
    agents:
      max_agents: 1
      default_timeout: 1
    edrr:
      enabled: false
      default_phase: expand
    security:
      input_validation: true
    performance: {}
    features:
      wsde_collaboration: false
    """
    )


def test_doctor_cmd_success_is_valid(tmp_path, monkeypatch):
    """When everything is valid, a success message should be printed.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    config_dir = tmp_path / 'cfg'
    config_dir.mkdir()
    for env in ['default', 'development', 'testing', 'staging', 'production']:
        (config_dir / f'{env}.yml').write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    with _patch_validation_loader(), patch.object(doctor_cmd, 'load_config',
        return_value=cfg), patch.object(doctor_cmd.bridge, 'print'
        ) as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert 'All configuration files are valid' in output


def test_doctor_cmd_invalid_config_is_valid(tmp_path, monkeypatch):
    """Invalid configuration should result in warnings being printed.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    config_dir = tmp_path / 'cfg'
    config_dir.mkdir()
    (config_dir / 'default.yml').write_text('application: {name: App}\n')
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    with _patch_validation_loader(), patch.object(doctor_cmd, 'load_config',
        return_value=cfg), patch.object(doctor_cmd.bridge, 'print'
        ) as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert 'Configuration issues detected' in output


@pytest.mark.parametrize('missing', ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY'])
def test_doctor_cmd_missing_env_vars_succeeds(monkeypatch, missing):
    """Doctor warns about whichever API key is absent.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    monkeypatch.delenv(missing)
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    with _patch_validation_loader(), patch.object(doctor_cmd, 'load_config',
        return_value=cfg), patch.object(doctor_cmd.bridge, 'print'
        ) as mock_print:
        doctor_cmd.doctor_cmd('config')
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert missing in output


def test_doctor_cmd_warns_missing_optional_feature_pkg_succeeds(monkeypatch,
    tmp_path):
    """Warn when enabled features require missing optional packages.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    config_dir = tmp_path / 'cfg'
    config_dir.mkdir()
    for env in ['default', 'development', 'testing', 'staging', 'production']:
        (config_dir / f'{env}.yml').write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    cfg.features = {'wsde_collaboration': True}
    cfg.memory_store_type = 'memory'
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == 'langgraph':
            return None
        return real_find(name, *args, **kwargs)
    with _patch_validation_loader(), patch.object(doctor_cmd.importlib.util,
        'find_spec', side_effect=fake_find), patch.object(doctor_cmd,
        'load_config', return_value=cfg), patch.object(doctor_cmd.bridge,
        'print') as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert 'langgraph' in output


@pytest.mark.parametrize('store_type,pkg', [('chromadb', 'chromadb'), (
    'tinydb', 'tinydb')])
def test_doctor_cmd_warns_missing_memory_store_pkg_succeeds(monkeypatch,
    tmp_path, store_type, pkg):
    """Warn and exit when memory store backends lack required packages.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    config_dir = tmp_path / 'cfg'
    config_dir.mkdir()
    for env in ['default', 'development', 'testing', 'staging', 'production']:
        (config_dir / f'{env}.yml').write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    cfg.features = {}
    cfg.memory_store_type = store_type
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == pkg:
            return None
        return real_find(name, *args, **kwargs)
    with _patch_validation_loader(), patch.object(doctor_cmd.importlib.util,
        'find_spec', side_effect=fake_find), patch.object(doctor_cmd,
        'load_config', return_value=cfg), patch.object(doctor_cmd.bridge,
        'print') as mock_print, pytest.raises(SystemExit) as exc:
        doctor_cmd.doctor_cmd(str(config_dir))
    assert exc.value.code == 1
    output = ''.join(str(call.args[0]) for call in mock_print.call_args_list)
    assert pkg in output


def test_doctor_cmd_warns_missing_uvicorn_succeeds(monkeypatch, tmp_path):
    """Warn when uvicorn is not installed.

ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, 'version_info', (3, 11, 0))
    monkeypatch.setenv('OPENAI_API_KEY', '1')
    monkeypatch.setenv('ANTHROPIC_API_KEY', '1')
    config_dir = tmp_path / 'cfg'
    config_dir.mkdir()
    for env in ['default', 'development', 'testing', 'staging', 'production']:
        (config_dir / f'{env}.yml').write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda : True
    cfg.features = {}
    cfg.memory_store_type = 'memory'
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == 'uvicorn':
            return None
        return real_find(name, *args, **kwargs)
    with _patch_validation_loader(), patch.object(doctor_cmd.importlib.util,
        'find_spec', side_effect=fake_find), patch.object(doctor_cmd,
        'load_config', return_value=cfg), patch.object(doctor_cmd.bridge,
        'print') as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = ''.join(str(call.args[0]) for call in mock_print.
            call_args_list)
        assert 'uvicorn' in output


def test_check_cmd_alias_succeeds(monkeypatch):
    """The ``check`` alias should delegate to ``doctor_cmd``.

ReqID: N/A"""
    from devsynth.application.cli.cli_commands import check_cmd
    with patch('devsynth.application.cli.cli_commands.doctor_cmd') as mock_doc:
        check_cmd('config')
        mock_doc.assert_called_once_with('config')
