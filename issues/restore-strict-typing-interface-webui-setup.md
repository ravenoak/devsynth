# Restore strict typing for `devsynth.interface.webui_setup`

## Summary

The WebUI setup helpers still rely on runtime module assignments guarded by
`type: ignore`. Strict typing is postponed until the setup utilities adopt the
shared Streamlit protocols.

## Tasks

- [ ] Replace the `type: ignore` shim with typed factories.
- [ ] Annotate setup helpers and exports with precise types.
- [ ] Remove the override and update the typing relaxation log.

## Evidence

- TODO `typing-interface-webui-setup` recorded in `pyproject.toml`.
