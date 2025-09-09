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

## References
- `docs/tasks.md` item 10.1
- `.github/workflows/ci.yml`
