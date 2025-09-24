import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, mock_open, patch

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Provide a mocked streamlit module for tests."""
    st = _mock_streamlit()
    # Ensure deterministic inputs for the requirements page
    st.text_input = MagicMock(return_value="requirements.md")
    st.text_area = MagicMock(return_value="desc")
    st.form_submit_button = MagicMock(return_value=False)
    st.button = MagicMock(return_value=False)

    def _columns(n: int):
        return tuple(MagicMock(button=MagicMock(return_value=False)) for _ in range(n))

    st.columns = MagicMock(side_effect=_columns)
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def mock_spec_cmd(monkeypatch):
    """Stub out CLI commands used by the requirements page."""
    spec_cmd = MagicMock()
    inspect_cmd = MagicMock()
    init_cmd = MagicMock()
    cli_module = ModuleType("devsynth.application.cli")
    cli_module.spec_cmd = spec_cmd
    cli_module.inspect_cmd = inspect_cmd
    cli_module.init_cmd = init_cmd
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    return spec_cmd


@pytest.mark.medium
def test_requirements_page_succeeds(mock_streamlit, mock_spec_cmd, monkeypatch):
    """requirements_page renders and invokes spec_cmd on submission."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    import devsynth.interface.webui.commands as commands

    importlib.reload(commands)
    import devsynth.interface.webui.rendering as rendering
    from devsynth.interface.webui import WebUI

    monkeypatch.setattr(
        "devsynth.application.cli.spec_cmd", mock_spec_cmd, raising=False
    )
    monkeypatch.setattr(commands, "spec_cmd", mock_spec_cmd, raising=False)
    monkeypatch.setattr(webui, "spec_cmd", mock_spec_cmd, raising=False)
    monkeypatch.setattr(rendering, "spec_cmd", mock_spec_cmd, raising=False)

    ui = WebUI()
    with (
        patch.object(WebUI, "_requirements_wizard"),
        patch.object(WebUI, "_gather_wizard"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        ui.requirements_page()

    mock_streamlit.header.assert_any_call("Requirements Gathering")

    mock_streamlit.form_submit_button.return_value = True
    with (
        patch.object(WebUI, "_requirements_wizard"),
        patch.object(WebUI, "_gather_wizard"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        ui.requirements_page()

    assert mock_spec_cmd.called


@pytest.mark.medium
def test_requirements_wizard_succeeds(mock_streamlit):
    """The requirements wizard advances steps and saves state."""

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    st = mock_streamlit
    st.text_input.return_value = "Title"
    st.text_area.return_value = "Description"
    st.selectbox.side_effect = ["functional", "medium"]

    ui = WebUI()

    # Advance to step 2
    col1 = MagicMock(button=MagicMock(return_value=False))
    col2 = MagicMock(button=MagicMock(return_value=True))
    col3 = MagicMock(button=MagicMock(return_value=False))
    st.columns.side_effect = None
    st.columns.return_value = (col1, col2, col3)
    ui._requirements_wizard()
    assert st.session_state["requirements_wizard_current_step"] == 2

    # Jump to final step and save
    st.columns.return_value = (
        MagicMock(button=MagicMock(return_value=False)),
        MagicMock(button=MagicMock(return_value=True)),
        MagicMock(button=MagicMock(return_value=False)),
    )
    st.session_state["requirements_wizard_current_step"] = 5
    st.text_area.return_value = "c1,c2"
    m = mock_open()
    with patch("builtins.open", m):
        result = ui._requirements_wizard()

    assert isinstance(result, dict)
    assert st.session_state["requirements_wizard_current_step"] == 1
