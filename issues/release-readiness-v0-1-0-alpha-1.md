# Release readiness for v0.1.0-alpha.1
Milestone: 0.1.0-alpha.1
Status: open
Priority: high
Dependencies: issues/virtualenv-configuration.md, issues/verify-test-markers-script.md, issues/performance-and-scalability-testing.md, docs/release/0.1.0-alpha.1.md

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

## References
- docs/release/0.1.0-alpha.1.md
- issues/virtualenv-configuration.md
- issues/verify-test-markers-script.md
- issues/performance-and-scalability-testing.md
