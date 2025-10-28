"""Tests for the ``doctor`` CLI command."""

import importlib
import importlib.util
import sys
from pathlib import Path
from textwrap import dedent
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.memory_intensive]

# Create minimal stubs to avoid importing heavy dependencies when loading doctor_cmd
devsynth_pkg = ModuleType("devsynth")
devsynth_pkg.__path__ = []
testing_pkg = ModuleType("devsynth.testing")
testing_pkg.__path__ = []
run_tests_stub = ModuleType("devsynth.testing.run_tests")
run_tests_stub.run_tests = lambda *a, **k: (True, "")

logging_stub = ModuleType("devsynth.logging_setup")


class _DummyLogger:
    def __init__(self, *_args, **_kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self


DevSynthLogger = _DummyLogger
logging_stub.DevSynthLogger = DevSynthLogger
logging_stub.configure_logging = lambda *a, **k: None

config_stub = ModuleType("devsynth.core.config_loader")
config_stub.load_config = lambda *a, **k: SimpleNamespace()
config_stub._find_project_config = lambda path: None

cli_stub = ModuleType("devsynth.interface.cli")


class _Bridge:
    def print(self, *args, **kwargs):
        pass


cli_stub.CLIUXBridge = _Bridge

ux_stub = ModuleType("devsynth.interface.ux_bridge")
ux_stub.UXBridge = object

app_pkg = ModuleType("devsynth.application")
app_pkg.__path__ = []
cli_pkg = ModuleType("devsynth.application.cli")
cli_pkg.__path__ = []
commands_pkg = ModuleType("devsynth.application.cli.commands")
commands_pkg.__path__ = []
cli_commands_stub = ModuleType("devsynth.application.cli.cli_commands")
cli_commands_stub._check_services = lambda bridge: True
utils_stub = ModuleType("devsynth.application.cli.utils")
utils_stub._check_services = lambda bridge: True
align_stub = ModuleType("devsynth.application.cli.commands.align_cmd")
align_stub.check_alignment = lambda *a, **k: []
align_stub.display_issues = lambda *a, **k: None


def _load_doctor_cmd():
    """Load the doctor_cmd module with required stubs."""
    with patch.dict(
        sys.modules,
        {
            "devsynth": devsynth_pkg,
            "devsynth.testing": testing_pkg,
            "devsynth.testing.run_tests": run_tests_stub,
            "devsynth.logging_setup": logging_stub,
            "devsynth.core.config_loader": config_stub,
            "devsynth.interface.cli": cli_stub,
            "devsynth.interface.ux_bridge": ux_stub,
            "devsynth.application": app_pkg,
            "devsynth.application.cli": cli_pkg,
            "devsynth.application.cli.commands": commands_pkg,
            "devsynth.application.cli.cli_commands": cli_commands_stub,
            "devsynth.application.cli.utils": utils_stub,
            "devsynth.application.cli.commands.align_cmd": align_stub,
        },
    ):
        spec = importlib.util.spec_from_file_location(
            "devsynth.application.cli.commands.doctor_cmd",
            Path(__file__).parents[4]
            / "src"
            / "devsynth"
            / "application"
            / "cli"
            / "commands"
            / "doctor_cmd.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
    return module


doctor_cmd = _load_doctor_cmd()


@pytest.mark.medium
def _patch_validation_loader():
    """Return a context manager providing a stub validation module."""
    stub = ModuleType("validate_config")
    stub.CONFIG_SCHEMA = {}
    stub.load_config = lambda path: {}
    stub.validate_config = lambda data, schema: []
    stub.validate_environment_variables = lambda data: []
    stub.check_config_consistency = lambda configs: []

    class _Loader:
        def exec_module(self, module):
            pass

    return patch.multiple(
        doctor_cmd.importlib.util,
        spec_from_file_location=lambda name, location: importlib.machinery.ModuleSpec(
            name, _Loader()
        ),
        module_from_spec=lambda spec: stub,
    )


@pytest.mark.medium
def test_doctor_cmd_old_python_and_missing_env_warn_succeeds(monkeypatch):
    """Missing configs, old Python and absent API keys should trigger warnings.

    ReqID: N/A"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 10, 0))
    cfg = SimpleNamespace()
    cfg.exists = lambda: False
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd("config")
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "No project configuration found" in output
        assert "Python 3.12 or higher" in output
        assert "Missing environment variables" in output


VALID_CONFIG = dedent(
    '\n    application:\n      name: App\n      version: "1.0"\n    logging:\n      level: INFO\n      format: "%(message)s"\n    memory:\n      default_store: kuzu\n      stores:\n        chromadb:\n          enabled: true\n        kuzu: {}\n        faiss:\n          enabled: false\n    llm:\n      default_provider: openai\n      providers:\n        openai:\n          enabled: true\n    agents:\n      max_agents: 1\n      default_timeout: 1\n    edrr:\n      enabled: false\n      default_phase: expand\n    security:\n      input_validation: true\n    performance: {}\n    features:\n      wsde_collaboration: false\n    '
)


@pytest.mark.medium
def test_doctor_cmd_success_is_valid(tmp_path, monkeypatch):
    """When everything is valid, a success message should be printed.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.cli_commands", cli_commands_stub
    )
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)
    # Create expected project directories to avoid warnings
    for name in ("src", "tests", "docs"):
        (tmp_path / name).mkdir()
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd, "_find_project_config", return_value=tmp_path),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "All configuration files are valid" in output


@pytest.mark.medium
def test_doctor_cmd_invalid_config_is_valid(tmp_path, monkeypatch):
    """Invalid configuration should result in warnings being printed.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    (config_dir / "default.yml").write_text("application: {name: App}\n")
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Configuration issues detected" in output


@pytest.mark.parametrize("missing", ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
@pytest.mark.medium
def test_doctor_cmd_missing_env_vars_succeeds(monkeypatch, missing):
    """Doctor warns about whichever API key is absent.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    monkeypatch.delenv(missing)
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd("config")
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert missing in output


@pytest.mark.medium
def test_doctor_cmd_warns_missing_optional_feature_pkg_succeeds(monkeypatch, tmp_path):
    """Warn when enabled features require missing optional packages.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    cfg.features = {"wsde_collaboration": True}
    cfg.memory_store_type = "memory"
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == "langgraph":
            return None
        return real_find(name, *args, **kwargs)

    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd.importlib.util, "find_spec", side_effect=fake_find),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "langgraph" in output


@pytest.mark.parametrize(
    "store_type,pkg", [("chromadb", "chromadb"), ("tinydb", "tinydb")]
)
@pytest.mark.medium
def test_doctor_cmd_warns_missing_memory_store_pkg_succeeds(
    monkeypatch, tmp_path, store_type, pkg
):
    """Warn and exit when memory store backends lack required packages.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    cfg.features = {}
    cfg.memory_store_type = store_type
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == pkg:
            return None
        return real_find(name, *args, **kwargs)

    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd.importlib.util, "find_spec", side_effect=fake_find),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
        pytest.raises(SystemExit) as exc,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
    assert exc.value.code == 1
    output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
    assert pkg in output


@pytest.mark.medium
def test_doctor_cmd_warns_missing_uvicorn_succeeds(monkeypatch, tmp_path):
    """Warn when uvicorn is not installed.

    ReqID: N/A"""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    cfg.features = {}
    cfg.memory_store_type = "memory"
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name == "uvicorn":
            return None
        return real_find(name, *args, **kwargs)

    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd.importlib.util, "find_spec", side_effect=fake_find),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "uvicorn" in output


@pytest.mark.medium
def test_check_cmd_alias_succeeds(monkeypatch):
    """The ``check`` alias should delegate to ``doctor_cmd``.


    ReqID: N/A"""
    from devsynth.application.cli.cli_commands import check_cmd

    with patch(
        "devsynth.application.cli.commands.diagnostics_cmds.doctor_cmd"
    ) as mock_doc:
        check_cmd("config")
        mock_doc.assert_called_once_with(config_dir="config", quick=False)


@pytest.mark.medium
def test_doctor_cmd_invokes_service_check(monkeypatch):
    """doctor_cmd should invoke _check_services."""
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    chk = MagicMock(return_value=True)
    monkeypatch.setattr(doctor_cmd, "_check_services", chk)
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print"),
    ):
        doctor_cmd.doctor_cmd("config")
        chk.assert_called_once_with(doctor_cmd.bridge)


@pytest.mark.medium
def test_doctor_cmd_warns_missing_required_dependency(monkeypatch, tmp_path):
    """Warn when core dependencies are missing."""

    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    (config_dir / "default.yml").write_text("application: {name: App}\n")
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    real_find = doctor_cmd.importlib.util.find_spec

    def fake_find(name, *a, **kw):
        if name == "pytest":
            return None
        return real_find(name, *a, **kw)

    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd.importlib.util, "find_spec", side_effect=fake_find),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "Missing dependencies: pytest" in output


@pytest.mark.medium
def test_doctor_cmd_reports_missing_directories(monkeypatch, tmp_path):
    """Warn when expected directories are absent."""

    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    (config_dir / "default.yml").write_text("application: {name: App}\n")
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    monkeypatch.setattr(doctor_cmd.Path, "cwd", lambda: tmp_path)
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "Missing expected directories" in output


@pytest.mark.medium
def test_doctor_cmd_quick_tests_failure_warns(monkeypatch, tmp_path):
    """Quick checks should run alignment and unit tests and report failures."""

    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    (config_dir / "default.yml").write_text("application: {name: App}\n")
    cfg = SimpleNamespace()
    cfg.exists = lambda: True
    fake_issues = [{"type": "test", "file": "f", "message": "m"}]
    with (
        _patch_validation_loader(),
        patch.object(doctor_cmd, "load_config", return_value=cfg),
        patch.object(
            doctor_cmd.align_cmd, "check_alignment", return_value=fake_issues
        ) as mock_align,
        patch.object(doctor_cmd.align_cmd, "display_issues") as mock_display,
        patch.object(doctor_cmd, "run_tests", return_value=(False, "")) as mock_run,
        patch.object(doctor_cmd.bridge, "print") as mock_print,
    ):
        doctor_cmd.doctor_cmd(str(config_dir), quick=True)
        mock_align.assert_called_once()
        mock_display.assert_called_once_with(fake_issues, bridge=doctor_cmd.bridge)
        mock_run.assert_called_once_with("unit-tests")
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "Unit tests failed" in output
