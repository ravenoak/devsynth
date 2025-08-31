import importlib

import pytest

pytestmark = [pytest.mark.no_network, pytest.mark.gui]


@pytest.mark.medium
def test_mvuu_dashboard_entrypoint_loads():
    # Dashboard uses streamlit; skip when not installed
    pytest.importorskip("streamlit")
    mod = importlib.import_module(
        "devsynth.application.cli.commands.mvuu_dashboard_cmd"
    )
    func = getattr(mod, "mvuu_dashboard_cmd", None)
    assert callable(func)
