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
- Memory regression guard: `poetry run python -m pytest tests/unit/application/memory -m "fast and not integration" --cov=src/devsynth/application/memory --cov-report=json:test_reports/coverage_memory.json` keeps the strict memory slice under watch; capture and archive the latest run output alongside other diagnostics.【F:diagnostics/pytest_memory_typed_targets_20250930T024540Z.txt†L1-L12】

## Determinism and Isolation
- Network must be disabled by default; all tests use provider stubs unless explicitly gated by resource flags.
- Deterministic seeds enforced (see tests/conftest.py fixtures), consistent timeouts, isolated tmp paths.

## Quality and Security
- Linting: black --check, isort --check-only, flake8.
- Typing: `poetry run task mypy:strict` (wrapper for `poetry run mypy --strict src/devsynth`) with documented, temporary relaxations only where noted in `pyproject.toml` and TODOs. Attach the most recent run output under `diagnostics/` (see `diagnostics/mypy_strict_2025-09-30_refresh.txt`).【F:diagnostics/mypy_strict_2025-09-30_refresh.txt†L1-L20】【F:diagnostics/mypy_strict_2025-09-30_refresh.txt†L850-L850】
- Memory stack strict typing: `poetry run mypy --strict src/devsynth/application/memory` must remain clean to keep the graduated stack within
  release tolerances; archive each run under `diagnostics/` to preserve the evidence trail.【F:diagnostics/mypy_strict_application_memory_20250930T024614Z.txt†L1-L200】
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
- Marker report: test_markers_report.json (latest transcript: `diagnostics/verify_test_markers_20250930T024603Z.txt`).【F:diagnostics/verify_test_markers_20250930T024603Z.txt†L1-L1】
- Memory coverage artifact: `test_reports/coverage_memory.json` produced by the targeted memory regression guard when it runs cleanly.【F:diagnostics/pytest_memory_typed_targets_20250930T024540Z.txt†L1-L12】
- Security reports (Bandit, Safety) attached in CI.

## CI Workflows
- PR job: fast suite; upload HTML reports; marker report; lint, mypy, security checks.
- Nightly job: medium; weekly job: slow.
- Release jobs: dry-run on main; tag-triggered publish workflow.

## Exit Criteria (0.1.0a1)
- All above gates green.
- Release Playbook steps executed through dry-run.
- Documentation cross-links added and validated.
