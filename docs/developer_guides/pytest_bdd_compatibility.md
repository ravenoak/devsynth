---
author: DevSynth Team
date: "2025-08-26"
status: active
version: "0.1.0a1"
---
# pytest-bdd Compatibility Notes (v8.1.0)

This guide documents DevSynth's expectations and compatibility notes for `pytest-bdd` version 8.1.0. It complements the CLI messaging and testing guidelines in project guidelines and the stabilization plan in docs/plan.md.

## Supported version
- We validate against `pytest-bdd==8.1.0`.

## Conventions
- Feature files live under the base directory configured in `pytest.ini` (key: `bdd_features_base_dir`).
- Step definitions should import from `pytest_bdd` using the v8+ API:
  ```python
  from pytest_bdd import given, when, then, scenario, parsers
  ```
- Prefer explicit `@scenario` decorators or `scenarios(<dir>)` helper targeting the configured features directory.
- Keep step function names descriptive and avoid collisions across modules; use parsers for parameters.

## Collection and isolation
- Behavior tests must run in isolation consistent with the rest of the suite:
  - No network (use `disable_network`), no writes outside tmp paths.
  - Use deterministic seeds and stable time fixtures where applicable.
- In smoke mode, third-party plugins (including `pytest-bdd`) may be disabled; ensure behavior tests used in smoke paths avoid plugin-specific features unless necessary.

## Running
- Collect-only:
  - poetry run pytest --collect-only -q tests/behavior/
- Targeted execution:
  - poetry run pytest tests/behavior -k "feature_name"

## Troubleshooting
- If steps are not discovered, verify `pytest.ini` contains the correct `bdd_features_base_dir` and that step modules are imported.
- Ensure decorators import from `pytest_bdd` (not legacy `pytest_bdd.steps` modules).
- When upgrading `pytest-bdd`, review deprecations and run behavior tests in smoke and normal modes.

## References
- project guidelines (Testing discipline)
- docs/plan.md (Stabilization priorities)
- docs/user_guides/cli_command_reference.md (CLI messaging principles)
