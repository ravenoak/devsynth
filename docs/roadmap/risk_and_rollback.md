---
author: DevSynth Team
date: "2025-08-25"
status: draft
version: "0.1.0"
---
# Risk and Rollback Plan

This document defines a lightweight, actionable rollback strategy for critical features and releases. It aligns with:
- .junie/guidelines.md (safety, clarity, determinism)
- docs/plan.md (stabilization priorities)
- docs/roadmap/release_plan.md (release cadence and gating)

## Objectives
- Minimize mean-time-to-recovery (MTTR) for regressions.
- Ensure changes are reversible with clear procedures.
- Keep user impact low by preferring toggles and safe defaults.

## Principles
- Feature flags for risky or cross-cutting features; default to off until proven stable.
- Backward-compatible migrations; provide down-migrations or no-op fallbacks.
- Observability-first: logs and metrics sufficient to detect and triage issues quickly.
- Offline/deterministic defaults in CI to avoid environment-induced flakiness.

## Rollback Triggers
- CI breakages on protected branches (lint, type, unit fast, or coverage gate failures).
- Security findings rated high by Bandit/Safety.
- User-visible regressions (CLI errors, incorrect exit codes, loss of data).
- Non-deterministic behavior detected by smoke or marker discipline checks.

## Rollback Mechanisms
1. Git Revert
   - Use `git revert` for merge commits that introduced regressions.
   - Prefer atomic PRs to simplify revert scope.
2. Feature Flag Disable
   - Disable via `--feature name=false` or environment `DEVSYNTH_FEATURE_<NAME>=false`.
   - Ensure safe defaults when disabled (no network, stub providers).
3. Version Pin/Unpin
   - Pin problematic transitive dependencies via constraints file or pyproject hotfix PR.
4. Workflow Toggle
   - Temporarily disable unstable CI jobs while investigating, keeping core gates active.

## Procedure Checklist (Operational)
- Identify culprit: link CI run, test report, coverage diff.
- Decide path: revert commit vs flag off vs hotfix.
- Communicate: add a comment to the originating issue/PR with rollback rationale and next steps.
- Verify: re-run smoke matrix and unit fast path; ensure green before closing.

## Data and Config Safety
- Never migrate or delete user data without an export path.
- Keep configuration changes backward-compatible; add schema version and map old -> new.

## Testing Hooks
- Smoke matrix (Linux/macOS; minimal vs targeted extras) must stay green.
- `devsynth run-tests --smoke --speed=fast --no-parallel` used to validate quick recovery.

## Examples
- Risky provider change: ship behind `DEVSYNTH_FEATURE_PROVIDER_V2`; default to false. Roll back by toggling the flag.
- Breaking CLI option: revert the PR; add deprecation notice for the next attempt.

## Ownership
- Release manager (rotation) coordinates rollbacks.
- Code owners provide module-specific remediation guidance.

## Change Log
- Track rollbacks in CHANGELOG under a dedicated section with links to PRs/issues.
