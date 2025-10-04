# Restore strict typing for `devsynth.interface.nicegui_webui`

## Summary

The NiceGUI bridge mirrors the Streamlit API but lacks typed interfaces. The
module is temporarily ignored until NiceGUI adapters adopt the shared protocol
contracts.

## Tasks

- [ ] Replace unused `type: ignore` comments with explicit typings.
- [ ] Align progress and result handlers with `UXBridge` signatures.
- [ ] Remove the override and update the typing relaxation tracker.

## Evidence

- TODO `typing-interface-nicegui-webui` recorded in `pyproject.toml`.
