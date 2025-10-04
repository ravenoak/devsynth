# Restore strict typing for `devsynth.interface.enhanced_error_handler`

## Summary

The enhanced error handler builds layered suggestion tuples without explicit
type hints. Strict mypy currently flags operator mismatches, so the module is
temporarily excluded from the typed set.

## Tasks

- [ ] Introduce TypedDict/NamedTuple definitions for suggestion payloads.
- [ ] Annotate public helpers and internal combinators.
- [ ] Remove the `ignore_errors` override and update typing tracking docs.

## Evidence

- TODO marker `typing-interface-enhanced-error-handler` recorded in
  `pyproject.toml`.
