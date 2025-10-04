# Restore strict typing for `devsynth.interface.ux_bridge`

## Summary

`UXBridge` exposes sanitizer and progress protocols but still relies on
fallback implementations guarded by `type: ignore` comments. The module remains
unchecked until the optional dependency shims are typed.

## Tasks

- [ ] Remove the legacy `type: ignore` markers in the sanitization fallback.
- [ ] Annotate abstract methods and concrete progress helpers.
- [ ] Remove the mypy override and capture evidence in
  `issues/typing_relaxations_tracking.md`.

## Evidence

- TODO reference `typing-interface-ux-bridge` recorded in `pyproject.toml`.
