# Restore strict typing for `devsynth.interface.progress_utils`

## Summary

Progress utilities expose context managers and Protocols that currently violate
strict variance requirements. The override remains while the helpers are
rewritten using ParamSpec-aware signatures.

## Tasks

- [ ] Refactor `ProgressManager` generics to satisfy variance checks.
- [ ] Annotate context manager factories with precise iterator returns.
- [ ] Remove the override and log the update in typing tracking docs.

## Evidence

- TODO `typing-interface-progress-utils` is documented in `pyproject.toml`.
