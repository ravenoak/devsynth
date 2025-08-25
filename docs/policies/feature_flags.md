# Feature Flags Policy

This document defines how DevSynth introduces, manages, deprecates, and removes feature flags.
It complements the guidelines in .junie/guidelines.md and the CLI contract implemented by
`devsynth run-tests --feature name[=true|false]` (maps to `DEVSYNTH_FEATURE_<NAME>`).

Goals
- Provide safe rollout and rollback mechanisms for risky changes.
- Keep the codebase maintainable by deprecating and removing stale flags.
- Offer clear migration guidance to users.

Naming
- All feature flags must use the `DEVSYNTH_FEATURE_<NAME>` format.
- Use uppercase snake case for `<NAME>`; keep names concise and scoped (e.g., `PROVIDER_V2`, `EDRR_FRAMEWORK`).

Lifecycle
1. Propose
   - Open an issue describing the new flag, scope, and default.
   - Add tests demonstrating both enabled/disabled behaviors where applicable.
2. Introduce
   - Default to the safest behavior for existing users.
   - Document the flag in CLI/user docs and, if applicable, in `docs/validation/optional_feature_matrix.md`.
3. Stabilize
   - Gather feedback; ensure observability hooks and guardrails are in place.
4. Deprecate
   - When a flag has served its purpose or unified behavior is preferred, start deprecation:
     - Create an issue using the template: `.github/ISSUE_TEMPLATE/feature_flag_deprecation.md`.
     - Announce timeline (last supported version, planned removal version).
     - Add deprecation notes to docs and changelog entries.
5. Remove
   - Remove all code paths gated solely by the flag.
   - Migrate defaults; update tests and docs.
   - Archive the flag entry under `docs/policies/feature_flags_archive/` with rationale and dates.

Operational Notes
- CLI mapping: `--feature name=true|false` sets `DEVSYNTH_FEATURE_<NAME>` for the test process (see tests covering this behavior).
- Environment overrides: `DEVSYNTH_FEATURE_<NAME>=true|false` respected by config loaders and CLI.
- Risk and rollback procedures are described in `docs/roadmap/risk_and_rollback.md`.

Archival
- For each removed flag, add a markdown file under `docs/policies/feature_flags_archive/` named `<name>.md` with:
  - Flag name and purpose
  - Dates: introduced, deprecated, removed
  - Replacement or unified behavior
  - Links to PRs, issues, and tests

Compliance
- New/changed flags should be referenced in PR descriptions and linked to the relevant issue.
- Tests must cover both states unless the flag is purely configuration routing without code paths.
