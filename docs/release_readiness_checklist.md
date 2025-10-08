# Release Readiness Checklist (0.1.0a1)

This checklist summarizes the acceptance criteria defined in docs/plan.md and provides a concise, verifiable list for maintainers to complete before tagging 0.1.0a1. Cross-reference: docs/plan.md §Acceptance Criteria and §Execution Matrix.

Acceptance Criteria (Exit for 0.1.0a1)
- All tests (unit, integration, behavior, resource-backed) pass in the maintainer full profile environment. Evidence: test_reports/ HTML + logs. Owner: Testing WG.
- scripts/verify_test_markers.py reports files_with_issues: 0 and zero speed/property violations; pytest.ini contains marker registrations. Evidence: test_markers_report.json. Owner: Testing WG.
- Coverage ≥90% enforced (DEVSYNTH_STRICT_COVERAGE=1 and DEVSYNTH_COV_FAIL_UNDER=90 or --cov-fail-under=90) with HTML report generated. Evidence: test_reports/htmlcov + coverage.json. Owner: Testing WG.
- Lint/format/type/security gates pass: Black, isort, Flake8, Mypy (strict), Bandit (excluding tests/), Safety. Evidence: diagnostics/*_gate.txt. Owner: Hygiene WG.
- devsynth doctor passes; diagnostics files show no missing optional deps in maintainer profile. Evidence: diagnostics/doctor.txt. Owner: Packaging/Docs WG.
- Documentation updated and consistent with CLI tooling and fixtures. Evidence: PR diffs and docs review. Owner: Docs WG.

Execution Matrix (to be run by maintainers)
- Inventory and marker hygiene
  - poetry run pytest --collect-only -q
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Full suite (segmented, no xdist for stability)
  - export DEVSYNTH_STRICT_COVERAGE=1; export DEVSYNTH_COV_FAIL_UNDER=90
  - poetry run devsynth run-tests --target all-tests --speed fast --speed medium --speed slow --no-parallel --segment --segment-size 50 --report
- Resource-enabled subsets
  - OpenAI: DEVSYNTH_OFFLINE=false DEVSYNTH_PROVIDER=openai OPENAI_API_KEY=... poetry run pytest -m "requires_resource('openai') and (fast or medium)"
  - LM Studio: DEVSYNTH_OFFLINE=false DEVSYNTH_PROVIDER=lmstudio DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true poetry run pytest -m "requires_resource('lmstudio') and (fast or medium)"
- Behavior/UI
  - Ensure webui extra installed (streamlit); run: poetry run pytest tests/behavior -m "not slow"
- Gates
  - poetry run black --check .
  - poetry run isort --check-only .
  - poetry run flake8 src/ tests/
  - poetry run mypy src/devsynth
  - poetry run bandit -r src/devsynth -x tests
  - poetry run safety check --full-report

Notes
- Keep GitHub Actions disabled until 0.1.0a1 tag (see docs/plan.md). Post-tag, enable low-throughput CI lanes as described.
- Prefer smoke mode and segmentation to reduce plugin interactions and stabilize long runs.
- Extras live in `[project.optional-dependencies]`; verify the latest
  `diagnostics/poetry_check_<timestamp>.log` shows clean resolution for the
  `docs`, `tests`, and release bundles before distributing artifacts.【F:pyproject.toml†L47-L116】【F:diagnostics/poetry_check_20251008T032324Z.log†L1-L3】
