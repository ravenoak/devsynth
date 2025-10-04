# Restore strict typing for `devsynth.interface.output_formatter`

## Summary

The output formatter still exposes optional defaults and untyped table helpers,
triggering strict Optional and collection warnings. The override allows WebUI
contract updates to land before a broader formatter refactor.

## Tasks

- [ ] Remove implicit Optional defaults and align constructor signatures.
- [ ] Annotate intermediate collection variables and rendering helpers.
- [ ] Delete the override once mypy runs clean and update tracking docs.

## Evidence

- TODO `typing-interface-output-formatter` recorded in `pyproject.toml`.
