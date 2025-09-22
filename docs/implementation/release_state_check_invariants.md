---
author: DevSynth Team
date: '2025-09-15'
last_reviewed: '2025-09-22'
status: published
tags:
- implementation
- invariants
title: Release State Check Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Release State Check Invariants
</div>

# Release State Check Invariants

This note details expected release states, their transitions, and proofs provided
by behavior-driven and unit tests.

## Expected States

- **draft** – release not yet published; no tag requirement.
- **published** – release published; requires a corresponding Git tag.

## Transitions and Checks

The `verify_release_state` script enforces audit cleanliness and tag
requirements before declaring success ([source](../../scripts/verify_release_state.py)).

- `draft` → `published` requires creating tag `v<version>`.
- Any state is blocked when `dialectical_audit.log` contains unresolved
  questions.

## Proofs

### Published without tag fails

BDD scenario demonstrates failure when a published release lacks its
corresponding tag ([feature](../../tests/behavior/features/release_state_check.feature)).
Unit tests mirror this behavior, asserting a non-zero exit code for a published
release missing its tag ([unit test](../../tests/unit/scripts/test_verify_release_state.py#L69-L76)).

### Draft release passes without tag

Draft releases succeed even without a tag ([feature](../../tests/behavior/features/release_state_check.feature#L11-L14), [unit test](../../tests/unit/scripts/test_verify_release_state.py#L59-L66)).

### Published release with tag succeeds

When the tag exists, verification succeeds ([unit test](../../tests/unit/scripts/test_verify_release_state.py#L79-L88)).

### Unresolved audit questions block release

Verification stops when the audit log has unanswered questions ([feature](../../tests/behavior/features/dialectical_audit_gating.feature#L6-L9)).

### Helper utilities remain deterministic

Regression tests now exercise the YAML parsing, tag lookup, and audit
sanitization helpers used by `verify_release_state`. Dedicated unit tests cover
front-matter parsing edge cases, direct tag existence checks, and audit log
validation (including malformed JSON and unresolved-question scenarios).【F:tests/unit/scripts/test_verify_release_state.py†L92-L145】

### Behavior suite evidence

The BDD harness now exercises both failure and success paths end-to-end.
`test_reports/release_state_check_bdd.log` captures the rerun executed with the
coverage threshold override used for targeted feature checks.【F:test_reports/release_state_check_bdd.log†L1-L20】

## References

- Specification: [docs/specifications/release-state-check.md](../specifications/release-state-check.md)
- BDD Features: [tests/behavior/features/release_state_check.feature](../../tests/behavior/features/release_state_check.feature), [tests/behavior/features/dialectical_audit_gating.feature](../../tests/behavior/features/dialectical_audit_gating.feature)
- Unit Tests: [tests/unit/scripts/test_verify_release_state.py](../../tests/unit/scripts/test_verify_release_state.py)
- Issue: [issues/release-state-check.md](../../issues/release-state-check.md)

## Coverage Signal and Outstanding Gaps (2025-09-22)

- Unit coverage via [`tests/unit/scripts/test_verify_release_state.py`](../../tests/unit/scripts/test_verify_release_state.py) exercises the success, failure, remediation, and helper branches of `scripts/verify_release_state.py`. A focused sweep limited to the `scripts/` namespace records 69.23 % line coverage for the verification script, confirming execution evidence for the invariants while highlighting unvisited fallback branches.【4ac8b5†L1-L8】
- Behavior coverage remains tracked through the dedicated BDD log, which documents the passing scenarios and their coverage context after restoring the release-state step module imports.【F:test_reports/release_state_check_bdd.log†L1-L20】
