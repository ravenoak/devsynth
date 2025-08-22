# Release readiness for v0.1.0-alpha.1
Milestone: 0.1.0-alpha.1
Status: blocked
Priority: high
Dependencies: issues/verify-test-markers-script.md, issues/performance-and-scalability-testing.md, issues/additional-storage-backends.md, issues/devsynth-run-tests-command.md, docs/release/0.1.0-alpha.1.md

## Problem Statement
Prerequisites for the first alpha release remain incomplete. The development environment lacks an enforced virtualenv, release automation via `task` is unavailable, and slow tests and marker verification scripts fail or time out. These gaps block tagging `v0.1.0-alpha.1`.

## Action Plan
- Ensure Poetry-managed virtual environments are enabled and documented.
- Install and wire up `go-task` so `task release:prep` works in CI and locally.
- Fix failing slow tests or mark benchmarks as optional to keep the suite green.
- Optimize or stub `scripts/verify_test_markers.py` to finish within reasonable time.
- Re-run the full release checklist in `docs/release/0.1.0-alpha.1.md` once blockers are resolved.

## Progress
- 2025-08-20: Initial audit captured missing virtualenv, absent `task` command, slow-test failures, and stalled marker verification.
- 2025-08-21: Established a Poetry virtual environment and installed development extras; `poetry env info --path` now reports the expected path. Attempted `poetry run devsynth run-tests --speed=fast`, but the command stalled after an `LMStudioProvider` warning, and `scripts/verify_test_markers.py` still runs slowly and was halted after ~150 files.
- 2025-08-21: Re-ran release checklist; environment provisioning and `pip check` succeeded, but fast tests failed (missing `tests/tmp_speed_dummy.py`). Medium and slow test runs halted after `LMStudioProvider` warnings. `verify_test_markers.py` was interrupted, deployment tests failed coverage, `task release:prep` ended early, and `verify_release_state` reported missing tag `v0.1.0-alpha.1`.
- 2025-08-22: Archived virtualenv configuration dependency. `poetry run python scripts/verify_release_state.py` reports missing tag `v0.1.0-alpha.1`.
- 2025-08-22: Re-ran release checklist; `pip check` passed, `devsynth run-tests` for all speeds aborted with missing `LMStudioProvider`, `verify_test_markers.py` halted after collection error, deployment tests failed coverage, and `task release:prep` failed with a `TinyDBMemoryAdapter` TypeError.

## References
- docs/release/0.1.0-alpha.1.md
- issues/verify-test-markers-script.md
- issues/performance-and-scalability-testing.md
- issues/additional-storage-backends.md
- issues/devsynth-run-tests-command.md
