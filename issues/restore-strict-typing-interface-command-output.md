# Restore strict typing for `devsynth.interface.command_output`

## Summary

`command_output` pipes formatter results through untyped branches, so strict
mypy cannot yet validate the API surface.

## Tasks

- [ ] Type the `format_command_output` entry point and supporting helpers.
- [ ] Align formatter integration with the typed sanitizer utilities.
- [ ] Remove the override and update typing tracking notes.

## Evidence

- TODO `typing-interface-command-output` documented in `pyproject.toml`.
