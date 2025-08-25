---
name: Feature Flag Deprecation
about: Track deprecation and removal of a feature flag with migration guidance
title: '[DEPRECATION] Feature Flag: <NAME>'
labels: deprecation, feature-flag
assignees: ''
---

# Feature Flag Deprecation

- Flag name: `DEVSYNTH_FEATURE_<NAME>`
- Subsystem/area: <!-- e.g., provider, memory, webui, cli -->
- Current default: <!-- true/false -->
- First introduced in: <!-- version or PR link -->

## Rationale
Explain why the flag is being deprecated (e.g., superseded, unified behavior, security concerns).

## Deprecation Timeline
- Deprecation announced: <!-- yyyy-mm-dd -->
- Last version to support the flag: <!-- e.g., 0.1.x -->
- Planned removal version: <!-- e.g., 0.2.0 -->

## Impact and Migration
- Affected code paths/modules: <!-- list -->
- User-visible behavior change: <!-- description -->
- Migration steps:
  - <!-- Step 1 -->
  - <!-- Step 2 -->

## Validation
- Tests updated: <!-- links/notes -->
- Docs updated: <!-- PR/file paths -->

## Archival
- Add an entry under `docs/policies/feature_flags_archive/` with:
  - Flag name, dates, reason, replacement
  - Links to PRs and tests

## Rollback Plan
If issues arise, how to revert (e.g., reintroduce the flag, hotfix with env override, or revert PR)?
