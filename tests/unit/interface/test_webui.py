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

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.inspect_code_cmd",
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
        "devsynth.application.cli.commands.inspect_code_cmd.inspect_code_cmd",
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


def test_edrr_cycle_page(monkeypatch, stub_streamlit):
    edrr = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.edrr_cycle_cmd.edrr_cycle_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    module.edrr_cycle_cmd = edrr
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.edrr_cycle_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().edrr_cycle_page()
    edrr.assert_called_once()


def test_alignment_page(monkeypatch, stub_streamlit):
    align = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.align_cmd.align_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.align_cmd")
    module.align_cmd = align
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.align_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().alignment_page()
    align.assert_called_once()


def test_alignment_metrics_page(monkeypatch, stub_streamlit):
    metrics = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.alignment_metrics_cmd.alignment_metrics_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.alignment_metrics_cmd")
    module.alignment_metrics_cmd = metrics
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.alignment_metrics_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().alignment_metrics_page()
    metrics.assert_called_once()


def test_inspect_config_page(monkeypatch, stub_streamlit):
    inspect = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.inspect_config_cmd.inspect_config_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.inspect_config_cmd")
    module.inspect_config_cmd = inspect
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.inspect_config_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().inspect_config_page()
    inspect.assert_called_once()


def test_validate_manifest_page(monkeypatch, stub_streamlit):
    validate = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.validate_manifest_cmd.validate_manifest_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.validate_manifest_cmd")
    module.validate_manifest_cmd = validate
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.validate_manifest_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().validate_manifest_page()
    validate.assert_called_once()


def test_validate_metadata_page(monkeypatch, stub_streamlit):
    validate = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.validate_metadata_cmd.validate_metadata_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.validate_metadata_cmd")
    module.validate_metadata_cmd = validate
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.validate_metadata_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().validate_metadata_page()
    validate.assert_called_once()


def test_test_metrics_page(monkeypatch, stub_streamlit):
    metrics = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.test_metrics_cmd.test_metrics_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.test_metrics_cmd")
    module.test_metrics_cmd = metrics
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.test_metrics_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().test_metrics_page()
    metrics.assert_called_once()


def test_docs_generation_page(monkeypatch, stub_streamlit):
    generate = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.generate_docs_cmd.generate_docs_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.generate_docs_cmd")
    module.generate_docs_cmd = generate
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.generate_docs_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().docs_generation_page()
    generate.assert_called_once()


def test_ingestion_page(monkeypatch, stub_streamlit):
    ingest = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.ingest_cmd.ingest_cmd",
    )
    module = ModuleType("devsynth.application.cli.ingest_cmd")
    module.ingest_cmd = ingest
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.ingest_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().ingestion_page()
    ingest.assert_called_once()


def test_apispec_page(monkeypatch, stub_streamlit):
    apispec = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.apispec.apispec_cmd",
    )
    module = ModuleType("devsynth.application.cli.apispec")
    module.apispec_cmd = apispec
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.apispec",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().apispec_page()
    apispec.assert_called_once()


def test_doctor_page(monkeypatch, stub_streamlit):
    doctor = _patch_cmd(
        monkeypatch,
        "devsynth.application.cli.commands.doctor_cmd.doctor_cmd",
    )
    module = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    module.doctor_cmd = doctor
    module.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.doctor_cmd",
        module,
    )

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI().doctor_page()
    doctor.assert_called_once()


def test_run_method_renders_pages(monkeypatch, stub_streamlit):
    """Test that the run method renders the appropriate page based on navigation."""
    # Mock the page methods
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    webui_instance = WebUI()
    webui_instance.onboarding_page = MagicMock()
    webui_instance.requirements_page = MagicMock()
    webui_instance.analysis_page = MagicMock()
    webui_instance.synthesis_page = MagicMock()
    webui_instance.edrr_cycle_page = MagicMock()
    webui_instance.alignment_page = MagicMock()

    # Test different navigation options
    stub_streamlit.sidebar.radio = MagicMock(return_value="Onboarding")
    webui_instance.run()
    webui_instance.onboarding_page.assert_called_once()

    # Reset mocks and test another navigation option
    webui_instance.onboarding_page.reset_mock()
    stub_streamlit.sidebar.radio = MagicMock(return_value="Requirements")
    webui_instance.run()
    webui_instance.requirements_page.assert_called_once()
