# DevSynth 0.1.0a1 — Actionable Improvement Tasks Checklist

Version: 2025-10-08
Source: Derived from docs/plan.md (Test Readiness and Coverage Improvement Plan)

Instructions: Check off each task when completed. Subtasks are enumerated for clarity and traceability. Follow the order for optimal flow. All commands should be run via Poetry.

1. Environment and Tooling Baseline (Phase 0)
1.1 [x] Install dependencies with full maintainer extras: `poetry install --with dev --all-extras`.
1.2 [x] Activate Poetry shell: `poetry shell`.
1.3 [x] Run quick sanity checks: `poetry run devsynth doctor`, `poetry run pytest --collect-only -q`.
1.4 [x] Validate marker discipline: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`.
1.5 [x] Capture reproducibility diagnostics under diagnostics/:
1.5.1 [x] `poetry run python -V | tee diagnostics/python_version.txt`
1.5.2 [x] `poetry --version | tee diagnostics/poetry_version.txt`
1.5.3 [x] `poetry run pip freeze | tee diagnostics/pip_freeze.txt`
1.5.4 [x] `poetry run devsynth doctor | tee diagnostics/doctor_run.txt`
1.5.5 [x] `date -u '+%Y-%m-%dT%H:%M:%SZ' | tee diagnostics/run_timestamp_utc.txt`
1.6 [x] Investigate `poetry install --with dev --all-extras` hanging on `nvidia/__init__.py` (Issue: [poetry-install-nvidia-loop.md](../issues/poetry-install-nvidia-loop.md)).
1.7 [x] Resolve scripts/codex_setup.sh version mismatch (project 0.1.0a1 vs expected 0.1.0-alpha.1).
1.8 [x] Ensure `devsynth` CLI entry point is installed; run `poetry install --with dev --all-extras` if missing.
1.9 [x] Ensure `task` CLI is available on the PATH: run `task --version`; if missing, run `bash scripts/install_dev.sh` and add `$HOME/.local/bin` to PATH (Issue: [task-cli-missing.md](../issues/task-cli-missing.md)).

2. [x] Property Tests Remediation (Phase 1)
2.1 [x] Fix Hypothesis misuse in tests/property/test_requirements_consensus_properties.py:
2.1.1 [x] Remove any example() calls at definition time; use @example decorators properly with @given.
2.1.2 [x] Ensure strategies are provided only via @given and hypothesis.strategies.
2.2 [x] Resolve AttributeError for _DummyTeam._improve_clarity:
2.2.1 [x] Preferred: Update tests to target a public API that internally triggers clarity improvement (e.g., team.improve_clarity(requirement)).
2.2.2 [x] Alternative: Implement a no-op or minimally semantic _improve_clarity on the Dummy test double to satisfy the expected interface (tests/helpers/dummies.py or equivalent).
2.3 [x] Ensure each property test has exactly one speed marker plus @pytest.mark.property.
2.4 [x] Re-run property tests: `DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/ -q` and confirm 0 failures.
2.5 [x] Add/adjust fixtures as needed to keep property tests isolated and deterministic.
2.6 [x] Resolve property marker advisories in tests/property/test_reasoning_loop_properties.py (Issue: property-marker-advisories-in-reasoning-loop-tests.md).
2.6.1 [x] Refine scripts/verify_test_markers.py to ignore nested Hypothesis helper functions or mark the helpers explicitly; re-run `verify_test_markers.py` to confirm 0 property_violations.

3. Coverage Uplift — CLI run_tests_cmd Hotspot (Phase 2)
3.1 [x] Add or extend unit tests for src/devsynth/application/cli/commands/run_tests_cmd.py to cover the following branches/behaviors:
3.1.1 [x] Smoke mode sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1.
3.1.2 [x] --no-parallel maps to pytest-xdist `-n0`.
3.1.3 [x] Inventory mode writes the inventory file and exits with correct code.
3.1.4 [x] Marker ANDing logic builds the correct pytest -m expression.
3.1.5 [x] --segment and --segment-size produce batched execution.
3.1.6 [x] --maxfail propagates correctly to pytest.
3.1.7 [x] --feature name[=true|false] sets DEVSYNTH_FEATURE_<NAME> env vars.
3.1.8 [x] Provider defaults applied when unset (DEVSYNTH_PROVIDER=stub, DEVSYNTH_OFFLINE=true, LM Studio unavailable).
3.1.9 [x] Invalid marker expression errors cleanly with non-zero exit code.
3.1.10 [x] Nonexistent target exits with error and helpful message.
3.2 [x] Ensure tests validate Typer exit codes, environment side effects, and avoid external network calls.
3.3 [x] Achieve >90% coverage for run_tests_cmd.py (verify via coverage report).

4. Coverage Uplift — Adapters and Stores (Phase 2)
4.1 [x] Identify pure-Python logic in adapters/stores (e.g., serialization/transforms) and add fast unit tests not requiring backends.
4.2 [x] For backend integrations (tinydb, duckdb, chromadb, faiss, kuzu):
4.2.1 [x] Add resource-gated tests using @pytest.mark.requires_resource("<NAME>").
4.2.2 [x] Implement minimal smoke coverage (import + basic op) when DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true.
4.2.3 [x] Document in tests how to enable each backend locally.

5. Coverage Uplift — UX Bridge and Logging (Phase 2)
5.1 [x] Add unit tests for non-interactive flows in CLI UX bridge components.
5.2 [x] Validate logging levels and branches are covered (e.g., warnings on invalid options, info on report generation).

6. Coverage Execution and Aggregation (Phase 2)
6.1 [x] Establish baseline coverage with fast+medium, no parallel: `poetry run devsynth run-tests --report --speed=fast --speed=medium --no-parallel`.
6.2 [x] If needed, run segmented coverage and combine:
6.2.1 [x] `poetry run devsynth run-tests --speed=fast --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_fast_1.log`
6.2.2 [x] `poetry run devsynth run-tests --speed=medium --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_medium_1.log`
6.2.3 [x] `poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json`
6.3 [x] Verify global threshold: ensure combined coverage >=90% with pytest.ini fail-under.
6.3.1 [x] Investigate missing coverage data after smoke run; ensure coverage is captured before threshold validation.
6.4 [x] Save logs to test_reports/ and artifacts to htmlcov/ and coverage.json.

7. Behavior and Integration Completeness (Phase 3)
7.1 [x] Ensure behavior tests cover CLI examples: unit fast no-parallel, report generation, smoke mode.
7.2 [x] Add scenarios for feature flags and segmented runs if missing.
7.3 [x] Review ingestion and metrics integrations to avoid external dependencies by default; expand fixtures to simulate inputs.
7.4 [x] Verify metrics consistency via assertions in integration tests.
7.5 [x] Audit missing BDD tests and link gaps in issues/missing-bdd-tests.md.

8. Non-functional Quality Gates (Phase 4)
8.1 [x] Black formatting check: `poetry run black --check .` – PASS.
8.2 [x] isort check: `poetry run isort --check-only .` – PASS.
8.3 [x] Flake8 lint: `poetry run flake8 src/ tests/` – FAIL (lint errors persist across tests).
8.4 [x] Bandit security scan: `poetry run bandit -r src/devsynth -x tests` – 158 low issues.
8.5 [x] Safety vulnerabilities: `poetry run safety check --full-report` – no known vulnerabilities.
8.6 [x] Mypy strict typing: `poetry run mypy src/devsynth` – missing `typer` type hints.
8.7 [x] Added targeted override for `devsynth.cli` in pyproject.toml with TODO until stubs exist.

9. Documentation and Developer Workflow (Phase 5)
9.1 [x] Update docs/user_guides/cli_command_reference.md with any new CLI options or clarified behaviors.
9.2 [x] Document maintainer setup and how to enable resource-gated backends locally (extras + env flags).
9.3 [x] Summarize provider defaults and offline behavior in README.md and docs.
9.4 [x] Add guidance to always aggregate coverage for readiness claims, avoiding narrow subset runs.

10. Release Preparation and CI/CD Strategy (Phase 6)
10.1 [x] Keep GitHub Actions disabled until 0.1.0a1 is tagged.
10.2 [x] After release, enable low-throughput workflows with concurrency control:
10.2.1 [x] Add smoke job (fast, --no-parallel, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1).
10.2.2 [x] Add unit+integration job (fast+medium) without xdist.
10.2.3 [x] Add typing+lint job (mypy/flake8/black/isort/bandit/safety).
10.3 [x] Configure caching for Poetry, pip, and .pytest_cache per plan.
10.4 [x] Upload artifacts on failures: test_reports/, htmlcov/, coverage.json, diagnostics/doctor_run.txt.

11. Issue Tracker Alignment and Traceability
11.1 [x] Generate an issues list: `ls -1 issues/ | tee diagnostics/issues_list.txt`.
11.2 [x] Grep for readiness-related tickets: `grep -R "readiness\|coverage\|tests\|run-tests" -n issues/ | tee diagnostics/issues_grep_readiness.txt`.
11.3 [x] Cross-reference behavior features with related issues: `grep -R "Related issue:" -n tests/behavior/ | tee diagnostics/behavior_related_issues.txt`.
11.4 [x] When adding/updating tests, include issue filename in test docstrings (e.g., "ReqID: FR-09; Issue: issues/<file>.md").
11.5 [x] Add behavior tests asserting presence of ReqID tags in docstrings for a representative subset; provide a small validation tool if needed.
11.6 [x] Audit typing_relaxations_tracking.md and schedule restorations in Phase 4 (issue links added).
11.7 [x] Closed redundant typing tickets: methodology-sprint, domain-models-requirement, adapters-requirements.
11.8 [x] Resolved run-tests missing test_first_metrics file; see test_reports/test_first_metrics.log (Issue: [run-tests-missing-test-first-metrics-file.md](../issues/run-tests-missing-test-first-metrics-file.md)).
11.9 [x] Guardrails suite resolved; see [flake8-violations.md](../issues/flake8-violations.md) and [bandit-findings.md](../issues/bandit-findings.md).
11.9.1 [x] Regenerate flake8 report and resolve E501/F401 in tests/unit/testing/test_run_tests_module.py and related files (Issue: [flake8-violations.md](../issues/flake8-violations.md)).
11.9.2 [x] Review bandit scan (158 low, 0 medium) and address or justify findings (Issue: [bandit-findings.md](../issues/bandit-findings.md)).

12. Risk Management and Mitigations
12.1 [x] Document minimal smoke coverage expectations for optional backends (macOS/Windows) and how to enable:
12.1.1 [x] TinyDB — `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`; import TinyDB, insert a document, and read it back.
12.1.2 [x] DuckDB — `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true`; connect in memory, create a table, insert a row, and select it.
12.1.3 [x] ChromaDB — `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true`; start an ephemeral client, add a document with an embedding, and query by vector.
12.1.4 [x] FAISS — `DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true`; build an `IndexFlatL2`, add a vector, and perform a nearest-neighbor search.
12.1.5 [x] Kuzu — `DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true`; open a temporary database, create a node table, insert a record, and retrieve it.
12.2 [x] Default smoke mode guidance in docs to reduce plugin-related flakiness; ensure CLI reflects PYTEST_DISABLE_PLUGIN_AUTOLOAD behavior.
12.3 [x] Provide a "coverage-only" profile or documented command to standardize local coverage runs.

13. Acceptance Criteria Validation
13.1 [x] All unit, integration, and behavior tests pass locally using documented commands.
13.2 [x] Property tests pass under `DEVSYNTH_PROPERTY_TESTING=true` with exactly one speed marker per function.
13.3 [x] Combined coverage >= 90% with HTML report generated and saved.
13.4 [x] Lint, type, and security gates pass with documented exceptions (if any).
13.5 [x] Docs updated: maintainer setup, CLI reference, provider defaults, resource flags, coverage guidance.
13.6 [x] Known environment warnings in doctor.txt triaged and documented as non-blocking by default.

14. Maintainer Quick Actions (for convenience; optional but recommended)
14.1 [x] Run smoke sanity: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and save to test_reports/smoke_fast.log.
14.2 [x] Full fast+medium with HTML report: `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` and archive artifacts.
14.3 [x] Property tests (opt-in): `DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/`.
14.4 [x] Marker discipline report regeneration: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`.

15. Environment Setup Reliability
15.1 [x] Document that fresh environments may lack the `task` CLI and instruct maintainers to run `bash scripts/install_dev.sh`.
15.2 [x] Evaluate caching or automatic installation to ensure `task` persists across sessions.
15.3 [x] Document go-task installation and persistence strategy in plan and task notes.

Notes:
- Ensure tests use resource gating and avoid accidental network calls. The run-tests command should set provider defaults when unset.
- Maintain exactly one speed marker per test function.
- Prefer adding tests for pure logic first, then expand to gated integrations.
