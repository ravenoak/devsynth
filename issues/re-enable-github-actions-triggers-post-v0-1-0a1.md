# Re-enable GitHub Actions triggers post-v0.1.0a1
Milestone: 0.1.0a1
Status: open
Priority: medium
Dependencies: docs/tasks.md item 10.1

## Problem Statement
All workflows currently rely on manual `workflow_dispatch` triggers to comply with policy. After tagging `v0.1.0a1`, push, pull_request, and scheduled triggers must be restored so CI runs automatically.

## Action Plan
- Reinstate `push` and `pull_request` triggers in `.github/workflows/ci.yml` and related workflows.
- Add a `schedule` trigger for the nightly job.
- Verify concurrency groups and cache keys operate under the restored triggers.
- Update `AGENTS.md` and `docs/tasks.md` once triggers are re-enabled.

## Status update (2025-10-04)
- Maintainer checklist captured in docs/release/0.1.0-alpha.1.md includes this follow-up. Post-tag PR will be opened immediately after smoke/logging regressions are cleared and maintainers confirm the tag, per issues/release-finalization-uat.md maintainer coordination notes.【F:docs/release/0.1.0-alpha.1.md†L60-L118】【F:issues/release-finalization-uat.md†L49-L60】

## Status update (2025-10-06)
- Post-tag branch prepared: all workflows now restore `push`/`pull_request` triggers, nightly suites regain their scheduled runs, and documentation (`AGENTS.md`, `.github/workflows/README.md`, `docs/tasks.md`) reflects the hand-off instructions. Merge immediately after `v0.1.0a1` is tagged.【F:.github/workflows/ci.yml†L1-L17】【F:.github/workflows/nightly_tests.yml†L1-L14】【F:.github/workflows/nightly_medium.yml†L1-L14】【F:.github/workflows/nightly_slow_tests.yml†L1-L14】【F:AGENTS.md†L6-L21】【F:docs/tasks.md†L379-L390】【F:.github/workflows/README.md†L1-L10】

## References
- `docs/tasks.md` item 10.1
- `.github/workflows/ci.yml`
