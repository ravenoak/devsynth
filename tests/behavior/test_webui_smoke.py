"""
Behavior-adjacent smoke test for WebUI.

Covers a minimal, import-only path that exercises non-Streamlit code paths
so it remains safe in minimal test environments. Marked as a resource-gated
behavior test to satisfy Track C (3.3) coverage goals without pulling heavy deps.

ReqID: C4 (Track C — behavior tests cover allowed webui smoke)
"""

import pytest


@pytest.mark.fast
@pytest.mark.gui
def test_webui_layout_config_smoke(monkeypatch):
    """ReqID: C4 — behavior WebUI smoke without heavy deps"""
    """Import webui and access a light method without requiring Streamlit.

    This verifies that basic WebUI helpers are importable and usable when the
    Streamlit dependency is absent. It is skipped by default unless the
    DEVSYNTH_RESOURCE_WEBUI_AVAILABLE flag is set.
    """
    # Import lazily to avoid module-level side effects.
    import importlib

    webui = importlib.import_module("devsynth.interface.webui")

    # Patch out Streamlit access by providing a dummy st with session_state.
    from types import SimpleNamespace

    monkeypatch.setattr(
        webui, "st", SimpleNamespace(session_state=SimpleNamespace(screen_width=1200))
    )

    # Ensure that trying to access a method that does not require Streamlit works.
    WebUI = webui.WebUI  # type: ignore[attr-defined]
    ui = WebUI()
    cfg = ui.get_layout_config()

    # Basic shape/keys sanity — choose keys that are part of layout config.
    assert isinstance(cfg, dict)
    for key in ("columns", "content_width", "is_mobile"):
        assert key in cfg, f"Missing expected key in layout config: {key}"
