# Restore strict typing for `devsynth.interface.dpg_bridge`

## Summary

The DearPyGUI bridge uses optional imports and untyped globals that confuse
strict mypy. The override persists until the bridge is annotated or retired.

## Tasks

- [ ] Add typed handles for DearPyGUI widgets.
- [ ] Remove unused `type: ignore` annotations.
- [ ] Remove the override and document the change in the typing tracker.

## Evidence

- TODO `typing-interface-dpg-bridge` recorded in `pyproject.toml`.
