# Restore strict typing for `devsynth.interface.cli`

## Summary

The CLI bridge maintains runtime dictionaries without type hints, preventing
strict typing. The override will be removed after annotating progress tracking
and command dispatch structures.

## Tasks

- [ ] Annotate CLI state maps and timing fields.
- [ ] Align progress helpers with the typed `ProgressIndicator` contract.
- [ ] Remove the override and update `issues/typing_relaxations_tracking.md`.

## Evidence

- TODO `typing-interface-cli` noted in `pyproject.toml`.
