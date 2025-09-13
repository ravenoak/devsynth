"""Property tests for WebUI WizardState invariants.

Issue: issues/webui-integration.md ReqID: WEBUI-001
"""

from types import ModuleType
from unittest.mock import patch

import pytest

from devsynth.interface.webui_state import WizardState


@pytest.fixture
def mocked_streamlit() -> ModuleType:
    st = ModuleType("streamlit")
    st.session_state = {}
    with patch("devsynth.interface.webui_state.st", st):
        yield st


@pytest.mark.property
@pytest.mark.medium
def test_go_to_step_bounds(mocked_streamlit: ModuleType) -> None:
    """go_to_step normalizes to the valid range.

    Issue: issues/webui-integration.md ReqID: WEBUI-001
    """
    state = WizardState("wizard", steps=5)
    state.go_to_step(7)
    assert state.get_current_step() == 5


@pytest.mark.property
@pytest.mark.medium
def test_next_step_converges_to_completion(mocked_streamlit: ModuleType) -> None:
    """Repeated next_step calls reach final step.

    Issue: issues/webui-integration.md ReqID: WEBUI-001
    """
    state = WizardState("wizard", steps=3)
    for _ in range(5):
        state.next_step()
    assert state.get_current_step() == 3
