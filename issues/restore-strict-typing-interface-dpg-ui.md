# Restore strict typing for `devsynth.interface.dpg_ui`

## Summary

The DearPyGUI UI wrappers import optional dependencies without stubs and bind
CLI commands dynamically. The override will stay until the UI adopts the typed
bridge protocols or the optional dependency ships stubs.

## Tasks

- [ ] Provide stub files or Protocols for DearPyGUI.
- [ ] Annotate binding helpers and ensure `_bind` enforces callable contracts.
- [ ] Remove the override and update the typing relaxation tracker.

## Evidence

- TODO `typing-interface-dpg-ui` documented in `pyproject.toml`.
