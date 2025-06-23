import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


class DummyForm:
    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture(autouse=True)
def stub_streamlit(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.header = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm(True)
    st.form = lambda *_a, **_k: DummyForm(True)
    st.form_submit_button = MagicMock(return_value=True)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
    st.spinner = DummyForm
    st.divider = MagicMock()
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=lambda *a, **k: False),
            MagicMock(button=lambda *a, **k: False),
        )
    )
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
        "doctor_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.analyze_code_cmd")
    analyze_stub.analyze_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.analyze_code_cmd",
        analyze_stub,
    )

    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_stub.doctor_cmd = MagicMock()
    doctor_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.doctor_cmd",
        doctor_stub,
    )
    cli_stub.doctor_cmd = doctor_stub.doctor_cmd
    yield st


def _patch_cmd(monkeypatch, path):
    module_name, attr = path.rsplit(".", 1)
    mod = sys.modules[module_name]
    func = MagicMock()
    setattr(mod, attr, func)
    return func


def test_onboarding_calls_init(monkeypatch, stub_streamlit):
    init = _patch_cmd(monkeypatch, "devsynth.application.cli.init_cmd")
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().onboarding_page()
    init.assert_called_once()


def test_requirements_calls_spec(monkeypatch, stub_streamlit):
    spec = _patch_cmd(monkeypatch, "devsynth.application.cli.spec_cmd")
    inspect = _patch_cmd(monkeypatch, "devsynth.application.cli.inspect_cmd")
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().requirements_page()
    assert spec.called
    assert inspect.called


def test_analysis_calls_analyze(monkeypatch, stub_streamlit):
    analyze = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.analyze_code_cmd.analyze_code_cmd",
    )
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().analysis_page()
    analyze.assert_called_once()


def test_synthesis_buttons(monkeypatch, stub_streamlit):
    test_cmd = _patch_cmd(monkeypatch, "devsynth.application.cli.test_cmd")
    code_cmd = _patch_cmd(monkeypatch, "devsynth.application.cli.code_cmd")
    run_cmd = _patch_cmd(monkeypatch, "devsynth.application.cli.run_pipeline_cmd")
    stub_streamlit.button = MagicMock(side_effect=[False, False])
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().synthesis_page()
    test_cmd.assert_called_once()
    code_cmd.assert_not_called()
    run_cmd.assert_not_called()


def test_config_update(monkeypatch, stub_streamlit):
    cfg = _patch_cmd(monkeypatch, "devsynth.application.cli.config_cmd")
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().config_page()
    assert cfg.called


def test_diagnostics_runs_doctor(monkeypatch, stub_streamlit):
    doc = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.doctor_cmd.doctor_cmd",
    )
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().diagnostics_page()
    doc.assert_called_once()
