# Streamlit WebUI — Headless Example

This example shows how to run the DevSynth WebUI in headless mode for CI or servers without a display.

Prerequisites
- Install the webui extra (Streamlit):
  poetry install --with dev --extras "webui"

Quick start
- Run the WebUI without opening a browser and force headless rendering:

```bash
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_SERVER_ADDRESS=127.0.0.1
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# Optionally suppress Streamlit opening a browser tab
export BROWSER=none

poetry run devsynth webui --browser=False --port 8501
```

Notes
- The CLI guards imports so other commands work even if Streamlit is not installed.
- Prefer --browser=False in headless environments; combine with STREAMLIT_SERVER_HEADLESS=true for reliability on Linux/macOS servers.
- For behavior tests, ensure tests are marked with @pytest.mark.gui and are excluded by default; run them only in a maintainer profile.
