# Issue 121: LM Studio mock service for deterministic tests

Milestone: 0.1.0-alpha.1

Tests referencing the LM Studio provider currently rely on the optional
`lmstudio` package and a running LM Studio server. When these are absent,
warnings are emitted and some integration tests cannot run, reducing
confidence in related code paths.

## Steps to reproduce
1. Ensure `lmstudio` is not installed.
2. Run `poetry run pytest tests/integration/general/test_lmstudio_provider.py`.
3. Observe that the module is skipped entirely due to missing dependency.

## Suggested improvement
Create a lightweight mock or HTTP stub of the LM Studio API so tests can
exercise provider logic without requiring the real service. When the real
service is available, keep resource markers so those tests can run against
it.

## Progress
- Documented best practices for mocking optional services in
  `docs/developer_guides/testing.md`.
- Running `tests/integration/general/test_lmstudio_provider.py` with `lmstudio` absent skips all tests and triggers coverage failure (`FAIL Required test coverage of 8% not reached`).
- Status: open
