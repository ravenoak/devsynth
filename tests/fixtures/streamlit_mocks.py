from types import ModuleType
from unittest.mock import MagicMock


class DummyContext:
    """Simple context manager used for streamlit forms/spinners."""

    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


def make_streamlit_mock(submitted: bool = True) -> ModuleType:
    """Return a mocked ``streamlit`` module with common APIs used in WebUI."""
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0

    st.header = MagicMock()
    st.subheader = MagicMock()
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.number_input = MagicMock(return_value=30)
    st.toggle = MagicMock(return_value=False)
    st.radio = MagicMock(return_value="choice")
    st.button = MagicMock(return_value=False)
    st.form_submit_button = MagicMock(return_value=submitted)
    st.expander = lambda *_a, **_k: DummyContext(submitted)
    st.form = lambda *_a, **_k: DummyContext(submitted)
    st.spinner = lambda *_a, **_k: DummyContext(submitted)
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
    st.code = MagicMock()
    st.error = MagicMock()
    st.info = MagicMock()
    st.success = MagicMock()
    st.warning = MagicMock()
    st.set_page_config = MagicMock()
    st.empty = MagicMock(
        return_value=MagicMock(markdown=MagicMock(), empty=MagicMock())
    )
    st.container = lambda *_a, **_k: DummyContext(submitted)
    st.components = ModuleType("components")
    st.components.v1 = ModuleType("v1")
    st.components.v1.html = MagicMock()

    sidebar = MagicMock()
    sidebar.title = MagicMock()
    sidebar.markdown = MagicMock()
    sidebar.radio = MagicMock(return_value="Onboarding")
    sidebar.button = MagicMock(return_value=False)
    sidebar.selectbox = MagicMock(return_value="test")
    sidebar.checkbox = MagicMock(return_value=False)
    sidebar.text_input = MagicMock(return_value="test")
    sidebar.text_area = MagicMock(return_value="test")
    sidebar.expander = lambda *_a, **_k: DummyContext(submitted)
    st.sidebar = sidebar

    return st
