---
author: AI Assistant
date: '2025-09-16'
status: active
tags:
- implementation
- invariants
title: WebUI Routing Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; WebUI Routing Invariants
</div>

# WebUI Routing Invariants

This note records behavioural guarantees for the Streamlit navigation router.

## Stable Default Selection

`Router.run` always falls back to its default entry when the stored selection is
missing or invalid, ensuring a deterministic landing page across reruns. Custom
defaults supplied at construction are honoured even when they are not the first
registered page.

```python
from devsynth.interface.webui.routing import Router
from unittest.mock import MagicMock

pages = {"Onboarding": MagicMock(), "Requirements": MagicMock()}
ui = MagicMock(streamlit=MagicMock())
ui.streamlit.session_state = {}
ui.streamlit.sidebar.radio.return_value = "Onboarding"

router = Router(ui, pages)
router.run()

assert pages["Onboarding"].called
```

The regression tests
[`test_router_resets_invalid_selection`](../../tests/unit/interface/test_webui_routing.py)
and
[`test_router_honors_explicit_default`](../../tests/unit/interface/test_webui_routing.py)
exercise this behaviour.

## Error Surfacing

Sidebar rendering failures and page execution errors are converted into visible
messages rather than propagating exceptions to Streamlit.

```python
router = Router(ui, {"Onboarding": MagicMock(side_effect=ValueError("kapow"))})
router.run()

assert ui.display_result.called_with("ERROR: kapow")
```

The protective logic is verified by
[`test_router_handles_sidebar_exception`](../../tests/unit/interface/test_webui_routing.py),
[`test_router_surfaces_page_exception`](../../tests/unit/interface/test_webui_routing.py),
and
[`test_router_reports_missing_page_handler`](../../tests/unit/interface/test_webui_routing.py).

## Invalid Selections Become User Feedback

If the sidebar returns a page name that is not registered the router renders a
clear error message instead of attempting to call a missing handler. This keeps
the UI responsive even when session state becomes corrupted.

## Session State Persistence

Every successful navigation run writes the selected page back to
`st.session_state.nav`, preserving continuity across reruns and other session
consumers.

```python
router = Router(ui, {"Onboarding": MagicMock(), "Synthesis": MagicMock()})
router.run()

assert ui.streamlit.session_state["nav"] in router.pages
```

[`tests/unit/interface/test_webui_routing.py::test_router_uses_session_state`](../../tests/unit/interface/test_webui_routing.py)
asserts this invariant by simulating successive user selections.

## References

- Tests: `tests/unit/interface/test_webui_routing.py`
- Specification: [docs/specifications/streamlit-webui-navigation.md](../specifications/streamlit-webui-navigation.md)
