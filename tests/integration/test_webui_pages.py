import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock
import pytest
from tests.integration.test_webui_setup import _setup_streamlit


@pytest.fixture
def webui_env(monkeypatch):
    st = _setup_streamlit(monkeypatch)
    st.form_submit_button = MagicMock(return_value=True)
    st.number_input = MagicMock(return_value=30)
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    for name in ["numpy", "responses", "networkx", "requests"]:
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    commands = {
        "edrr_cycle_page": (
            "devsynth.application.cli.commands.edrr_cycle_cmd",
            "edrr_cycle_cmd",
        ),
        "alignment_page": ("devsynth.application.cli.commands.align_cmd", "align_cmd"),
        "alignment_metrics_page": (
            "devsynth.application.cli.commands.alignment_metrics_cmd",
            "alignment_metrics_cmd",
        ),
        "inspect_config_page": (
            "devsynth.application.cli.commands.inspect_config_cmd",
            "inspect_config_cmd",
        ),
        "validate_manifest_page": (
            "devsynth.application.cli.commands.validate_manifest_cmd",
            "validate_manifest_cmd",
        ),
        "validate_metadata_page": (
            "devsynth.application.cli.commands.validate_metadata_cmd",
            "validate_metadata_cmd",
        ),
        "test_metrics_page": (
            "devsynth.application.cli.commands.test_metrics_cmd",
            "test_metrics_cmd",
        ),
        "docs_generation_page": (
            "devsynth.application.cli.commands.generate_docs_cmd",
            "generate_docs_cmd",
        ),
        "ingestion_page": ("devsynth.application.cli.ingest_cmd", "ingest_cmd"),
        "apispec_page": ("devsynth.application.cli.apispec", "apispec_cmd"),
        "refactor_page": ("devsynth.application.cli.cli_commands", "refactor_cmd"),
        "webapp_page": ("devsynth.application.cli.cli_commands", "webapp_cmd"),
        "serve_page": ("devsynth.application.cli.cli_commands", "serve_cmd"),
        "dbschema_page": ("devsynth.application.cli.cli_commands", "dbschema_cmd"),
    }
    all_cmds = [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "enable_feature_cmd",
        "gather_cmd",
        "config_app",
        "inspect_cmd",
        "webapp_cmd",
        "webui_cmd",
        "dbschema_cmd",
        "check_cmd",
        "refactor_cmd",
        "serve_cmd",
    ]
    mocks = {}
    for _, (module_path, func_name) in commands.items():
        module = ModuleType(module_path)
        module.bridge = None
        func = MagicMock()
        setattr(module, func_name, func)
        monkeypatch.setitem(sys.modules, module_path, module)
        mocks[func_name] = func
    for name in all_cmds:
        mocks.setdefault(name, MagicMock())
    cli_cmds = ModuleType("devsynth.application.cli.cli_commands")
    for name, func in mocks.items():
        setattr(cli_cmds, name, func)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.cli_commands", cli_cmds)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return webui.WebUI(), mocks


def test_webui_pages_invoke_commands_succeeds(webui_env):
    """Test that webui pages invoke commands succeeds.

    ReqID: N/A"""
    bridge, mocks = webui_env
    bridge.edrr_cycle_page()
    assert mocks["edrr_cycle_cmd"].called
    bridge.alignment_page()
    assert mocks["align_cmd"].called
    bridge.alignment_metrics_page()
    assert mocks["alignment_metrics_cmd"].called
    bridge.inspect_config_page()
    assert mocks["inspect_config_cmd"].called
    bridge.validate_manifest_page()
    assert mocks["validate_manifest_cmd"].called
    bridge.validate_metadata_page()
    assert mocks["validate_metadata_cmd"].called
    bridge.test_metrics_page()
    assert mocks["test_metrics_cmd"].called
    bridge.docs_generation_page()
    assert mocks["generate_docs_cmd"].called
    bridge.ingestion_page()
    assert mocks["ingest_cmd"].called
    bridge.apispec_page()
    assert mocks["apispec_cmd"].called
