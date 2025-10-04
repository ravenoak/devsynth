# Restore strict typing for `devsynth.interface.webui.rendering`

## Summary

The bulk WebUI renderer remains largely untyped; the new
`rendering_simulation` module covers typed progress simulations, but the legacy
UI mixins still require a broader annotation sweep.

## Tasks

- [ ] Introduce typed mixins or protocols for the remaining WebUI pages.
- [ ] Annotate helper functions and CLI bridge interactions.
- [ ] Remove the `ignore_errors` override once mypy runs clean and update the
  typing relaxation tracker.

## Evidence

- TODO `typing-interface-webui-rendering` noted in `pyproject.toml`.
