import importlib

import pytest

pytestmark = [pytest.mark.no_network, pytest.mark.gui]


@pytest.mark.medium
def test_webui_module_import_smoke_no_side_effects():
    pytest.importorskip("streamlit")
    mod = importlib.import_module("devsynth.interface.webui")
    assert mod is not None
