# Restore strict typing for `devsynth.interface.webui_state`

## Summary

`webui_state` orchestrates Streamlit session persistence with many unannotated
helpers. The temporary typing override remains while the new Streamlit
protocols land.

## Tasks

- [ ] Add precise return and parameter annotations for the state helpers.
- [ ] Replace untyped `Callable` usages with typed generics.
- [ ] Remove the mypy override and document the change in
  `issues/typing_relaxations_tracking.md`.

## Evidence

- Referenced by TODO `typing-interface-webui-state` in `pyproject.toml`.
