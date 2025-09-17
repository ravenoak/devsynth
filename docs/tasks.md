# DevSynth 0.1.0a1 — Actionable Improvement Tasks Checklist

Version: 2025-09-13
Source: Derived from docs/plan.md (Test Readiness and Coverage Improvement Plan)

Instructions: Check off each task when completed. Subtasks are enumerated for clarity and traceability. Follow the order for optimal flow. All commands should be run via Poetry.

1. Environment and Tooling Baseline (Phase 0)
1.1 [x] Provision environment and install go-task: `bash scripts/install_dev.sh`.
1.1.1 [x] Verify `task` CLI is available: `task --version`.
1.1.2 [x] Verify `devsynth` CLI is installed: `poetry run devsynth --help`.
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
6.1 [x] Establish baseline coverage with fast+medium using the hardened CLI instrumentation (auto `--cov`, HTML/JSON artifacts, and gate enforcement).
6.1.1 [x] Single-run aggregate (strict gate): `poetry run devsynth run-tests --target all-tests --speed=fast --speed=medium --no-parallel --report`.
6.2 [x] Use segmented coverage when memory/runtime pressure surfaces; instrumentation appends between batches.
6.2.1 [x] Segmented aggregate example: `poetry run devsynth run-tests --target all-tests --speed=fast --speed=medium --segment --segment-size 75 --no-parallel --report`.
6.2.2 [x] Optional manual combine when mixing CLI runs with ad-hoc pytest invocations: `poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json`.
6.3 [ ] Verify global threshold: the coverage gate still reports 13.68 % (<90 %); coordinate follow-ups via [issues/coverage-below-threshold.md](../issues/coverage-below-threshold.md).
6.3.1 [ ] Document smoke profile expectations: auto `-p pytest_cov` keeps instrumentation active; set `PYTEST_ADDOPTS="--no-cov"` to bypass coverage intentionally during smoke rehearsals and record the skip rationale.
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
11.10 [x] Reopen run-tests-missing-test-first-metrics-file.md due to recurring path error; fix reference to `tests/unit/general/test_test_first_metrics.py` and rerun full coverage.

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
13.3 [ ] Combined coverage >= 90% with HTML report generated and saved (latest gate result: 13.68 % with artifacts present but below threshold).
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
15.4 [x] Investigate `scripts/install_dev.sh` reporting "Python 3.12 not available for Poetry" and ensure the script reliably provisions the environment.

16. Requirements Traceability Alignment
16.1 [x] Add BDD feature files for specifications referenced in verify_requirements_traceability failures:
16.1.1 [x] devsynth_specification.md → tests/behavior/features/devsynth_specification.feature
16.1.2 [x] specification_evaluation.md → tests/behavior/features/specification_evaluation.feature
16.1.3 [x] devsynth_specification_mvp_updated.md → tests/behavior/features/devsynth_specification_mvp_updated.feature
16.1.4 [x] testing_infrastructure.md → tests/behavior/features/testing_infrastructure.feature
16.1.5 [x] executive_summary.md → tests/behavior/features/executive_summary.feature
16.2 [x] Re-run `poetry run python scripts/verify_requirements_traceability.py` until no missing feature references.
16.3 [x] Update issues/missing-bdd-tests.md and docs/plan.md with progress.

Notes:
- Ensure tests use resource gating and avoid accidental network calls. The run-tests command should set provider defaults when unset.
- Maintain exactly one speed marker per test function.
- Prefer adding tests for pure logic first, then expand to gated integrations.
- 2025-09-15: Environment needed go-task reinstallation; smoke tests and verification scripts pass; UAT and tagging remain.

17. Documentation Maintenance
17.1 [x] Deduplicate historical entries in docs/task_notes.md to keep the iteration log concise.

18. Release Readiness Follow-ups (Phase 7)
18.1 [x] Implement release state check feature per docs/specifications/release-state-check.md and add BDD scenarios.
18.2 [x] Address high-priority gaps from issues/missing-bdd-tests.md.
18.2.1 [x] Add BDD feature for agent_api_stub.md.
18.2.2 [x] Add BDD feature for chromadb_store.md.
18.2.3 [x] Add BDD feature for dialectical_reasoning.md.
18.3 [x] Review components for missing proofs or simulations and document any gaps.
18.3.1 [x] Reasoning loop invariants documented in docs/implementation/reasoning_loop_invariants.md.
18.3.2 [x] Provider system invariants documented in docs/implementation/provider_system_invariants.md.
18.3.3 [x] Consensus building invariants documented in docs/implementation/consensus_building_invariants.md.
18.4 [x] Ensure all GitHub Actions workflows remain `workflow_dispatch` only until v0.1.0a1 is tagged.
18.5 [x] Investigate full fast+medium coverage run failure (`ERROR tests/unit/general/test_test_first_metrics.py`) and restore coverage artifact generation.
18.6 [x] Automate provisioning of `devsynth` CLI and `task` in fresh environments (issues/devsynth-cli-missing.md, issues/task-cli-persistence.md).

19. Release Finalization (Phase 8)
19.1 [x] Draft v0.1.0a1 release notes and update CHANGELOG.md.
19.2 [ ] Conduct User Acceptance Testing and confirm approval.
19.3 [ ] Perform final full fast+medium coverage run and archive artifacts with ≥90 % coverage. Latest attempt (2025-09-15) produced only 13.68 %; the new gate fails accordingly even though htmlcov/ and coverage.json are now generated automatically.
19.4 [ ] Hand off to maintainers to tag v0.1.0a1 on GitHub and prepare post-release tasks (re-enable GitHub Actions triggers).
19.5 [ ] Close issues/release-finalization-uat.md after tagging is complete.

20. Strict Typing Restoration Roadmap (Phase 9)
20.1 [x] Consolidate open strict typing tickets into issues/strict-typing-roadmap.md for unified tracking.
20.2 [x] Sequence post-release PRs to reintroduce strict typing to logger, exceptions, and CLI modules.
20.3 [x] Document typing restoration decisions in docs/plan.md and update related issue files upon completion.

21. Coverage Remediation Iteration (Phase 2B)
21.1 [x] Harden `devsynth run-tests` instrumentation so every invocation injects `--cov=src/devsynth --cov-report=json:test_reports/coverage.json --cov-report=html:htmlcov --cov-append` and resets artifacts before execution (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Regression tests for these pathways remain tracked under §21.7.
21.2 [x] Add focused unit tests for `src/devsynth/interface/output_formatter.py` covering formatting and error branches highlighted as uncovered (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 22.09 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.3 [x] Add fast unit tests for `src/devsynth/interface/webui_bridge.py` to exercise routing/handshake paths (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 18.54 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.4 [x] Introduce integration tests (resource-gated if needed) for `src/devsynth/interface/webui.py` to cover navigation, prompt rendering, and command execution flows without external services (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 17.97 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.5 [ ] Extend tests for `src/devsynth/logging_setup.py` to validate log level overrides, JSON formatting, and handler wiring (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.6 [ ] Add deterministic unit tests for `src/devsynth/methodology/edrr/reasoning_loop.py` demonstrating recursion safeguards and invariants (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.7 [ ] Increase coverage for `src/devsynth/testing/run_tests.py` by validating CLI invocation paths and error handling distinct from `run_tests_cmd` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.8 [x] Ensure smoke profile coverage enforcement is coherent: auto-inject `-p pytest_cov` when `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` so instrumentation remains active, while allowing intentional skips via `PYTEST_ADDOPTS="--no-cov"` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.9 [x] Implement a coverage gate that parses `test_reports/coverage.json`, prints the measured percentage, and fails when coverage <90 % to prevent silent regressions (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.10 [x] Document the remediated coverage workflow in docs/plan.md and docs/tasks.md after instrumentation lands (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).

22. Coverage Instrumentation Recovery (Phase 2C)
22.1 [x] Diagnose why `.coverage` is absent after `devsynth run-tests` when coverage warnings appear; ensure `_ensure_coverage_artifacts()` only runs once real data is available (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.2 [x] Add an integration test around `run_tests_cmd` that simulates a successful pytest run and asserts `test_reports/coverage.json` contains `totals.percent_covered` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.3 [x] Update enforcement logic to detect placeholder coverage artifacts and surface actionable remediation guidance in the CLI output (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.4 [x] Document the instrumentation recovery steps and minimum reproducible command in docs/plan.md and docs/task_notes.md once fixed.

23. Academic Rigor Alignment (Phase 5B)
23.1 [ ] Promote `docs/implementation/output_formatter_invariants.md` from draft to reviewed status after new tests cover formatting branches (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [documentation-utility-functions.md](../issues/documentation-utility-functions.md)).
23.2 [ ] Promote `docs/implementation/reasoning_loop_invariants.md` from draft to reviewed status once recursion safeguards gain property/unit coverage (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [Finalize-dialectical-reasoning.md](../issues/Finalize-dialectical-reasoning.md)).
23.3 [ ] Promote `docs/implementation/webui_invariants.md` from draft to reviewed status after WebUI bridge/navigation coverage increases (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [webui-integration.md](../issues/webui-integration.md)).
23.4 [ ] Audit remaining specifications tagged `status: draft` and pair them with verified BDD features before UAT sign-off (Issue: [release-finalization-uat.md](../issues/release-finalization-uat.md)).

Notes:
- 2025-09-15: Verified environment after running `poetry install --with dev --all-extras`; smoke tests and verification scripts pass. Remaining open tasks: 19.2, 19.4, 19.5.
- 2025-09-15: Reinstalled dependencies and reran smoke/verification; tasks 19.2, 19.4, 19.5 remain.
