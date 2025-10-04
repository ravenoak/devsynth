# Restore strict typing for `devsynth.interface.agentapi_models`

## Summary

The Pydantic response models under `devsynth.interface.agentapi_models` still
rely on dynamic BaseModel contracts, so the strict mypy gate cannot type-check
them without additional stubs. The module now uses a temporary `ignore_errors`
override so WebUI work can proceed.

## Tasks

- [ ] Replace runtime `BaseModel` imports with typed aliases or stubs.
- [ ] Annotate the request/response dataclasses and helper factories.
- [ ] Remove the mypy override and update `issues/typing_relaxations_tracking.md`.

## Evidence

- Tracking added in `pyproject.toml` via TODO `typing-interface-agentapi-models`.
