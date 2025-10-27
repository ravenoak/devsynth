---
title: "DevSynth 0.1.0a1 — Current Actionable Tasks (Authoritative)"
date: "2025-10-26"
version: "0.1.0-alpha.1"
tags:
  - tasks
  - checklist
  - readiness
status: "completed"
author: "DevSynth Team"
source: "Aligned with docs/plan.md (Updated 2025-10-27)"
---

# DevSynth 0.1.0a1 — Simplified Remediation Tasks

**COMPLETED**: All critical test collection and syntax errors have been resolved. The codebase now has clean test collection with 4926 tests available for execution. Coverage generation and reporting infrastructure is functional.

**Related Issues**:
- `issues/bdd-import-mismatches.md`: Critical BDD framework import errors (NEW)
- `issues/f-string-syntax-error.md`: Critical syntax error in test file (NEW)
- `issues/test-collection-regressions-20251004.md`: Updated to reflect ongoing collection issues
- `issues/coverage-below-threshold.md`: Updated status to blocked due to collection failures
- `issues/release-readiness-assessment-v0-1-0a1.md`: Comprehensive release readiness tracking

Instructions
- Execute tasks top-to-bottom. Focus on root cause fixes, not complex process.
- Run all commands via Poetry to ensure plugins/extras and repo-local virtualenvs are honored.
- Artifacts must be written to test_reports/, htmlcov/, and diagnostics/ as specified.

1. [x] Fix BDD framework imports (CRITICAL - blocks collection)
   Acceptance criteria:
   - Change `from behave import given, when, then` to `from pytest_bdd import given, when, then` in:
     - `tests/behavior/steps/test_cursor_integration_steps.py`
     - `tests/behavior/steps/test_enhanced_knowledge_graph_steps.py`
     - `tests/behavior/steps/test_memetic_unit_steps.py`
   - `poetry run pytest --collect-only -q` shows these files no longer have import errors.

2. [x] Fix syntax error in test file (CRITICAL - blocks collection)
   Acceptance criteria:
   - Correct f-string in `src/devsynth/application/testing/test_report_generator.py` line 664:
     - Change: `time_value".2f"`
     - To: `time_value:.2f`
   - `poetry run pytest --collect-only --tb=short` shows no SyntaxError.

3. [x] Resolve relative import issues (HIGH - blocks collection)
   Acceptance criteria:
   - Either move test files from `src/devsynth/application/testing/` to `tests/unit/application/testing/`
   - Or convert relative imports to absolute imports
   - `poetry run pytest --collect-only --tb=short` shows no ImportError for relative imports.

4. [x] Verify clean collection (no errors, all tests collected)
   Acceptance criteria:
   - `poetry run pytest --collect-only --tb=short` shows 0 errors, ~4875 items collected.
   - Save output to `diagnostics/pytest_collect_only_clean.log`.
   - No import errors, syntax errors, or relative import failures.

5. [x] Confirm smoke run and coverage generation works
   Acceptance criteria:
   - Command: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`.
   - Exit code 0; `.coverage` file and `test_reports/coverage.json` generated.
   - Log saved to `test_reports/smoke_fast_verification.log`.

6. [x] Reproduce 90%+ coverage achievement
   Acceptance criteria:
   - Command: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`.
   - Exit code 0; coverage ≥90%; artifacts in `htmlcov/` and `test_reports/coverage.json`.
   - Save output to `artifacts/releases/0.1.0a1/fast-medium/verification/devsynth_run_tests_verification.txt`.

7. [x] Final verification and release preparation
   Acceptance criteria:
   - All commands (collect-only, smoke, fast+medium, mypy strict) pass cleanly.
   - Update `docs/plan.md` and `docs/tasks.md` to reflect completed fixes.
   - Prepare single commit with all fixes for streamlined PR.

Appendix: Authoritative commands (for repetition)
- Collect-only: `poetry run pytest --collect-only -q`
- Smoke: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- Aggregate: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`
- Segmented aggregate (fallback): `poetry run devsynth run-tests --speed=fast --speed=medium --segment --segment-size=75 --no-parallel --report`
- Typing: `poetry run mypy --strict src/devsynth`
- Markers check: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`
- Inventory only: `poetry run devsynth run-tests --inventory`
