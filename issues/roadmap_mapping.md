# Issues to Plan Track Mapping (0.1.0a1)

This document maps open issues and references to the stabilization Tracks A–D as defined in docs/plan.md and docs/tasks.md. It also notes deferrals to 0.1.0a2 with brief justifications.

- Track A — Test harness stabilization and marker enforcement
  - Related references: issues/devsynth-run-tests-hangs.md (A6–A7 cache/selector hardening). Status: addressed in 1.8; keep monitoring. Deferral: none.
  - Critical recommendations follow-up: issues/Critical-recommendations-follow-up.md touches A1–A5. Status: addressed in parts; further improvements possible post-release.

- Track B — Provider/backends determinism
  - OpenAI/LM Studio opt-in gating: covered by tests and env defaults. Any provider credential issues should be tracked under a new issue if observed.
  - Retrieval backends gating smoke: documented and validated. No deferrals.

- Track C — Coverage and flakiness
  - Coverage below target in some modules: create targeted sub-issues per module if <80% after baseline. Deferred raising to ≥90% if not achieved in 0.1.0a1, moved to 0.1.0a2 with justification: “non-critical modules and error branches; prioritize stability first.”
  - Flaky cases log: docs/analysis/flaky_case_log.md informs C5/C6. New flakes should create issues referencing this track.

- Track D — Documentation, diagnostics, release gating
  - Testing guide specifics (D2): This iteration updates coverage commands and resource flags sections. Remaining consolidation tasks may defer minor doc consistency cleanups to 0.1.0a2.
  - CI workflows (D6–D7): To be finalized post-release. Deferral justified by low throughput requirement and limited maintainer time pre-tag.

Maintenance notes
- Keep this mapping updated when closing or opening issues; link PRs and commits with track IDs (e.g., A6, B3, C1, D2) in titles or descriptions.
- Cross-reference: docs/plan.md and docs/tasks.md.
