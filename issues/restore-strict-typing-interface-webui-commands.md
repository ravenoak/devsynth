# Restore strict typing for `devsynth.interface.webui.commands`

## Summary

The WebUI command mixin still binds CLI functions dynamically, so strict typing
flags incompatible assignments. The override remains until the command registry
adopts typed callables.

## Tasks

- [ ] Model command registry entries with typed `Protocol`s.
- [ ] Annotate `_handle_command_errors` and helper methods.
- [ ] Remove the override and refresh the typing relaxation log.

## Evidence

- TODO `typing-interface-webui-commands` recorded in `pyproject.toml`.
