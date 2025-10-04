# Restore strict typing for `devsynth.interface.agentapi_enhanced`

## Summary

Enhanced agent API handlers wrap additional telemetry logic but still treat
Pydantic models as untyped. The override persists until typed models and status
helpers are in place.

## Tasks

- [ ] Provide typed wrappers for status codes and response builders.
- [ ] Annotate enhanced endpoint handlers with concrete response types.
- [ ] Remove the override and update typing relaxations tracking.

## Evidence

- TODO `typing-interface-agentapi-enhanced` captured in `pyproject.toml`.
