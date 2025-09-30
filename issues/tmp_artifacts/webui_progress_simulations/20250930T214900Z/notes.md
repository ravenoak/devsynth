# Focused Coverage — WebUI Progress Simulations

- **Command:** `poetry run pytest tests/unit/interface/test_webui_simulations_fast.py --maxfail=1`
- **Modules:** `src/devsynth/interface/webui.py`, `src/devsynth/interface/webui/rendering.py`, `src/devsynth/interface/webui_bridge.py`
- **Highlights:** streamlit stub drives `_UIProgress`, rendering summary simulations, wizard clamps, and sanitized error channels without importing the real dependency.
