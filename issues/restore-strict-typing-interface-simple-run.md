# Restore strict typing for `devsynth.interface.simple_run`

## Summary

`simple_run` stitches together CLI runners and still returns loosely typed JSON
payloads. Strict typing is deferred until the response contract is stabilized.

## Tasks

- [ ] Introduce a TypedDict for the command response payload.
- [ ] Annotate helper functions and ensure `None` handling is explicit.
- [ ] Remove the override and update the typing relaxation log.

## Evidence

- TODO `typing-interface-simple-run` recorded in `pyproject.toml`.
