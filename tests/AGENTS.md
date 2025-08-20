# AGENTS.md

This directory summarizes test-specific guidance. For general contribution, environment, and policy information, see the repository [root AGENTS.md](../AGENTS.md).

- honor all policies under `../docs/policies/` and resolve `dialectical_audit.log` before submitting a PR;
- update this file when testing workflows change.

## Test isolation

`tests/conftest.py` defines an autouse `global_test_isolation` fixture that resets environment variables, the working directory, and logging for each test. Avoid setting environment variables at import time; use `monkeypatch.setenv()` or set them inside the test body.

## Speed markers

`tests/conftest_extensions.py` provides `fast`, `medium`, and `slow` markers. Each test must include exactly one speed marker; unmarked tests default to `medium`. Combine speed markers with context markers like `memory_intensive` when appropriate. Update markers when requirements shift.

Run tests for a specific speed category:

```bash
poetry run devsynth run-tests --speed=<fast|medium|slow>
```

## Marker verification

Verify that tests use the required speed markers:

```bash
poetry run python scripts/verify_test_markers.py
```
