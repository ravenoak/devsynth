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

## References
- `docs/tasks.md` item 10.1
- `.github/workflows/ci.yml`
