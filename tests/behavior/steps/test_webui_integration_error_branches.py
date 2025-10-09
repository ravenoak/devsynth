from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, then, when

pytestmark = [pytest.mark.fast]


def _make_slot() -> MagicMock:
    slot = MagicMock()
    slot.markdown = MagicMock()
    slot.info = MagicMock()
    slot.empty = MagicMock()
    return slot


def _make_context(name: str) -> MagicMock:
    context = MagicMock(name=f"{name}_context")
    context.__enter__.return_value = context
    context.__exit__.return_value = False
    context.markdown = MagicMock()
    context.progress = MagicMock(return_value=MagicMock(progress=MagicMock()))
    context.success = MagicMock()
    return context


def _build_streamlit_stub() -> ModuleType:
    stub = ModuleType("streamlit")
    stub.session_state = {}
    stub.sidebar = ModuleType("sidebar")
    stub.sidebar.radio = MagicMock(return_value="Onboarding")
    stub.sidebar.title = MagicMock()
    stub.sidebar.markdown = MagicMock()
    stub.header = MagicMock()
    stub.subheader = MagicMock()
    stub.subheader = MagicMock()
    stub.markdown = MagicMock()
    stub.write = MagicMock()
    stub.error = MagicMock()
    stub.warning = MagicMock()
    stub.success = MagicMock()
    stub.info = MagicMock()
    stub.empty = MagicMock(side_effect=_make_slot)
    stub.progress = MagicMock(return_value=MagicMock(progress=MagicMock()))
    stub.expander = MagicMock(side_effect=lambda *_: _make_context("expander"))
    stub.code = MagicMock()
    stub.container = MagicMock(side_effect=lambda: _make_context("container"))
    stub.components = SimpleNamespace(v1=SimpleNamespace(html=MagicMock()))
    stub.set_page_config = MagicMock()
    return stub


@pytest.fixture
def webui_error_context(monkeypatch):
    st_mock = _build_streamlit_stub()
    monkeypatch.setitem(sys.modules, "streamlit", st_mock)
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())

    security_pkg = ModuleType("devsynth.security")
    validation_stub = ModuleType("devsynth.security.validation")
    validation_stub.parse_bool_env = lambda _name, default=True: default
    sanitization_stub = ModuleType("devsynth.security.sanitization")
    sanitization_stub.sanitize_input = lambda text: text
    monkeypatch.setitem(sys.modules, "devsynth.security", security_pkg)
    monkeypatch.setitem(sys.modules, "devsynth.security.validation", validation_stub)
    monkeypatch.setitem(
        sys.modules, "devsynth.security.sanitization", sanitization_stub
    )
    security_pkg.validation = validation_stub
    security_pkg.sanitization = sanitization_stub

    config_stub = ModuleType("devsynth.config")
    config_stub.load_project_config = MagicMock(return_value={})
    config_stub.save_config = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.config", config_stub)
    monkeypatch.setitem(sys.modules, "yaml", MagicMock())

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    ui = webui.WebUI()
    return {"ui": ui, "st": webui.st, "module": webui}


@given("a WebUI instance with sanitized stubs")
def given_webui_instance(webui_error_context):
    return webui_error_context


@when('the WebUI reports "File not found: config.yaml"')
def when_webui_reports_missing_file(webui_error_context):
    ui = webui_error_context["ui"]
    ui.display_result(
        "ERROR: File not found: config.yaml",
        highlight=False,
        message_type="error",
    )


@then("the WebUI should surface suggestions and documentation links")
def then_webui_surfaces_guidance(webui_error_context):
    st = webui_error_context["st"]

    markdown_payloads = [call.args[0] for call in st.markdown.call_args_list]
    assert any("**Suggestions:**" in text for text in markdown_payloads)
    assert any(
        "Check that the file path is correct" in text for text in markdown_payloads
    )
    assert any("**Documentation:**" in text for text in markdown_payloads)
    assert any("File Handling Guide" in text for text in markdown_payloads)


@then("the WebUI should log the error banner")
def then_webui_logs_error(webui_error_context):
    module = webui_error_context["module"]
    st = webui_error_context["st"]
    sanitized = module.sanitize_output("ERROR: File not found: config.yaml")
    st.error.assert_called_with(sanitized)
