# Re-enable GitHub Actions triggers post-v0.1.0a1
Milestone: 0.1.0a1
Status: open
Priority: medium
Dependencies: docs/tasks.md item 10.1

## Problem Statement
All workflows currently rely on manual `workflow_dispatch` triggers to comply with policy. After tagging `v0.1.0a1`, push, pull_request, and scheduled triggers must be restored so CI runs automatically.

## Action Plan
1. **Pre-tag posture** – Keep every workflow `workflow_dispatch`-only until maintainers record smoke, strict typing, and fast+medium green evidence inside `issues/release-finalization-uat.md`; this guards against accidental automation before the gates stay green.【F:issues/release-finalization-uat.md†L1-L120】
2. **Draft post-tag PR** – Prepare a maintainer PR that (a) restores `push`/`pull_request` triggers for default-branch commits and release branches, (b) re-enables the nightly `schedule`, and (c) documents the change in `AGENTS.md` and `docs/tasks.md`. The PR description must reference the latest knowledge-graph IDs from the strict typing and fast+medium runs (`QualityGate=c54c967d-6a97-4c68-a7df-237a609fd53e`, `TestRun=3ec7408d-1201-4456-8104-ee1b504342cc`, `ReleaseEvidence={9f4bf6fc-4826-4ff6-8aa2-24c5e6396b37,e3208765-a9f9-4293-9a1d-bbd3726552af}`, and `QualityGate=QG-20251012-FASTMED`, `TestRun=TR-20251012-FASTMED`, `ReleaseEvidence=RE-20251012-FASTMED`).【F:diagnostics/mypy_strict_20251005T035128Z.log†L1-L17】【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/devsynth_run_tests_fast_medium_20251012T164512Z.txt†L1-L12】
   - Draft diff staged under `artifacts/pr_drafts/re-enable-workflows-post-v0-1-0a1.patch` to accelerate PR creation once the tag is ready.【F:artifacts/pr_drafts/re-enable-workflows-post-v0-1-0a1.patch†L1-L19】
3. **Maintainer approval checkpoint** – Merge the PR only after the Release Coordination Board and QA/Engineering confirm readiness inside the UAT tracking issues, then flip the triggers from dispatch-only to automatic. Capture the approval timestamps in the PR body for audit traceability.【F:issues/alpha-release-readiness-assessment.md†L1-L96】【F:docs/release/0.1.0-alpha.1.md†L70-L86】
4. **Post-merge verification** – Re-run CI via manual dispatch once, then confirm that `push`, `pull_request`, and `schedule` events fire as expected before closing this issue. Update the release execution plan with the verification results.【F:docs/release/0.1.0-alpha.1.md†L70-L118】

## Status update (2025-10-09)
- Maintainer checklist captured in docs/release/0.1.0-alpha.1.md includes this follow-up. Draft diff archived at `artifacts/pr_drafts/re-enable-workflows-post-v0-1-0a1.patch`; PR will open immediately after smoke/logging regressions are cleared, `poetry install` succeeds, and maintainers confirm the tag, per issues/release-finalization-uat.md coordination notes.【F:docs/release/0.1.0-alpha.1.md†L70-L118】【F:issues/release-finalization-uat.md†L49-L136】【F:artifacts/pr_drafts/re-enable-workflows-post-v0-1-0a1.patch†L1-L19】

## References
- `docs/tasks.md` item 10.1
- `.github/workflows/ci.yml`
