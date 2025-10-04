# Restore strict typing for `devsynth.interface.webui_bridge`

## Summary

`webui_bridge` coordinates Streamlit progress indicators with numerous
attribute mutations. The module remains under an override until the new
Streamlit protocols are fully adopted.

## Tasks

- [ ] Replace `type: ignore` annotations with concrete types.
- [ ] Annotate progress indicator state transitions and bridge helpers.
- [ ] Remove the override and update `issues/typing_relaxations_tracking.md`.

## Evidence

- TODO `typing-interface-webui-bridge` captured in `pyproject.toml`.
