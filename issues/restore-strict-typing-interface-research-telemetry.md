# Restore strict typing for `devsynth.interface.research_telemetry`

## Summary

Research telemetry relies on dataclass factories that instantiate typed
payloads dynamically. The module will stay under an override until the
dataclasses are refactored into typed containers.

## Tasks

- [ ] Replace dynamic dataclass usage with static TypedDicts or dataclasses.
- [ ] Annotate signing helpers and payload aggregators.
- [ ] Remove the override and update typing relaxation documentation.

## Evidence

- TODO `typing-interface-research-telemetry` noted in `pyproject.toml`.
