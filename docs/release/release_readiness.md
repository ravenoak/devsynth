---
title: "Release Readiness Gates"
date: "2025-08-26"
version: "0.1.0a1"
status: "living"
author: "DevSynth Team"
last_reviewed: "2025-08-26"
---

# Release Readiness Gates

This document codifies the gating criteria for release preparation. It complements the Release Playbook (docs/release/release_playbook.md) and the stabilization plan (docs/plan.md).

## Test Targets
- PRs must pass: fast + medium targets (unit + key integrations) via `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`, with HTML/JSON coverage artifacts uploaded.【F:diagnostics/full_profile_coverage.txt†L1-L24】
- Pre-release branches or pre-tag checks must pass: full suite including slow.
- Smoke mode may be used for diagnosis, but final gates must run in normal mode without third-party plugin disablement.

## Determinism and Isolation
- Network must be disabled by default; all tests use provider stubs unless explicitly gated by resource flags.
- Deterministic seeds enforced (see tests/conftest.py fixtures), consistent timeouts, isolated tmp paths.

## Quality and Security
- Linting: black --check, isort --check-only, flake8.
- Typing: `poetry run task mypy:strict` (wrapper for `poetry run mypy --strict src/devsynth`) with documented, temporary relaxations only where noted in `pyproject.toml` and TODOs. Attach the most recent run output under `diagnostics/` (see `diagnostics/mypy_strict_2025-09-30_refresh.txt`).【F:diagnostics/mypy_strict_2025-09-30_refresh.txt†L1-L20】【F:diagnostics/mypy_strict_2025-09-30_refresh.txt†L850-L850】
- Security: bandit and safety (full report) must pass or have documented, justified suppressions.

## Marker Discipline
- Exactly one of @pytest.mark.fast|medium|slow per test function.
- Validate via: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`.

## Documentation
- mkdocs build must succeed.
- Broken links, anchors, and code fences fixed.
- Release notes updated: docs/release/0.1.0-alpha.1.md.

## Artifacts
- HTML test report(s) and `test_reports/coverage.json` with ≥90 % totals archived under `artifacts/releases/0.1.0a1/fast-medium/` using timestamped folders (see `diagnostics/full_profile_coverage.txt` for the canonical command set).【F:diagnostics/full_profile_coverage.txt†L1-L24】
- Marker report: test_markers_report.json.
- Security reports (Bandit, Safety) attached in CI.

## CI Workflows
- PR job: fast suite; upload HTML reports; marker report; lint, mypy, security checks.
- Nightly job: medium; weekly job: slow.
- Release jobs: dry-run on main; tag-triggered publish workflow.

## Exit Criteria (0.1.0a1)
- All above gates green.
- Release Playbook steps executed through dry-run.
- Documentation cross-links added and validated.
