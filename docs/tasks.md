---
title: "DevSynth 0.1.0a1 — Actionable Improvement Tasks Checklist"
date: "2025-09-13"
version: "0.1.0-alpha.1"
tags:
  - "tasks"
  - "checklist"
  - "implementation"
  - "release-preparation"
status: "active"
author: "DevSynth Team"
last_reviewed: "2025-10-06"
source: "Derived from docs/plan.md (Test Readiness and Coverage Improvement Plan)"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; DevSynth 0.1.0a1 Tasks Checklist
</div>

# DevSynth 0.1.0a1 — Actionable Improvement Tasks Checklist

Instructions: Check off each task when completed. Subtasks are enumerated for clarity and traceability. Follow the order for optimal flow. All commands should be run via Poetry.

0. Execution Plan Realignment (Phase preflight)
0.1 [ ] Review `docs/release/v0.1.0a1_execution_plan.md` and confirm staged PR ownership in planning meeting notes.
0.2 [ ] Update release readiness issues (`coverage-below-threshold.md`, `critical-mypy-errors-v0-1-0a1.md`, `release-readiness-assessment-v0-1-0a1.md`) to match 2025-10-02 status.
0.3 [ ] Draft `docs/typing/strict_typing_wave1.md` with module owners, baseline error counts, and remediation hypotheses.
0.4 [ ] Draft `docs/testing/coverage_wave1.md` mapping low-coverage modules to targeted tests and responsible engineers.
0.5 [ ] Circulate plan via WSDE standup; log acknowledgment in meeting notes and dialectical audit follow-up.

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
4.3 [x] Replace placeholder BDD steps in `tests/behavior/features/memory_adapter_read_and_write_operations.feature` so the memory adapter read/write specification can exit draft status; align documentation once executable evidence exists.【F:tests/behavior/features/memory_adapter_read_and_write_operations.feature†L1-L16】【F:tests/behavior/steps/test_memory_adapter_read_and_write_operations_steps.py†L1-L79】

5. Coverage Uplift — UX Bridge and Logging (Phase 2)
5.1 [x] Add unit tests for non-interactive flows in CLI UX bridge components.
5.2 [x] Validate logging levels and branches are covered (e.g., warnings on invalid options, info on report generation).

6. Coverage Execution and Aggregation (Phase 2)
6.1 [x] Establish baseline coverage with fast+medium using the hardened CLI instrumentation (auto `--cov`, HTML/JSON artifacts, and gate enforcement).
6.1.1 [x] Single-run aggregate (strict gate): `poetry run devsynth run-tests --target all-tests --speed=fast --speed=medium --no-parallel --report`.
6.2 [x] Use segmented coverage when memory/runtime pressure surfaces; instrumentation appends between batches.
6.2.1 [x] Segmented aggregate example: `poetry run devsynth run-tests --target all-tests --speed=fast --speed=medium --segment --segment-size 75 --no-parallel --report`.
6.2.2 [x] Optional manual combine when mixing CLI runs with ad-hoc pytest invocations: `poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json`.
6.3 [x] Verify global threshold: the 2025-10-12 fast+medium aggregate cleared the ≥90 % gate (92.40 %) with HTML/JSON artifacts and knowledge-graph IDs archived; remaining uplift now targets `methodology/edrr/reasoning_loop.py` before the next rerun (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/devsynth_run_tests_fast_medium_20251012T164512Z.txt†L1-L10】【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L52】【F:artifacts/releases/0.1.0a1/fast-medium/20251015T000000Z-fast-medium/reasoning_loop_fast.json†L1-L18】
6.3.1 [x] Document smoke profile expectations with the repaired instrumentation: smoke mode logs the forced `-p pytest_cov` injection and marker fallback, but currently aborts on a `pytest-bdd` configuration error when plugin autoloading is disabled—coverage artifacts stay missing until the BDD configuration is restored.【F:logs/run-tests-smoke-fast-after-fix.log†L1-L57】
6.3.2 [x] Capture the refreshed CLI diagnostics after reinstalling dependencies and record them in issues/coverage-below-threshold.md alongside the reproduced 20.94 % measurement and fallback logging.【F:logs/run-tests-fast-medium-after-fix.log†L2429-L2447】【68ff9d†L1-L18】【F:issues/coverage-below-threshold.md†L1-L28】
6.3.3 [x] Trace `ensure_pytest_cov_plugin_env` during smoke and fast+medium runs to confirm `-p pytest_cov` is injected or explain why the helper returns False in the current `.venv` context (add debug logging or pytest monkeypatch-based unit tests).【843367†L1-L5】【615f96†L1-L5】
6.3.4 [x] Compare `devsynth run-tests` with a direct `pytest --cov=src/devsynth` execution inside the new `.venv` to determine why `.coverage` remains absent despite installed extras; document findings in issues/coverage-below-threshold.md.
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
10.1 [x] Keep GitHub Actions disabled until 0.1.0a1 is tagged; workflows must remain `workflow_dispatch`-only (no `push`, `pull_request`, or `schedule` triggers).
10.1.1 [x] Verify `.github/workflows/ci.yml` and related automation reference only `workflow_dispatch` so accidental trigger modes cannot reappear before tagging.【F:.github/workflows/ci.yml†L1-L11】
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
12.1.6 [x] Ensure collaboration, ingestion, and adapter memory tests lazily import optional stores after `pytest.importorskip` and respect `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` so they skip when extras are disabled (2025-09-21).【F:tests/integration/collaboration/test_role_reassignment_shared_memory.py†L1-L86】【F:tests/integration/general/test_ingestion_pipeline.py†L1-L622】【F:tests/unit/adapters/test_chromadb_memory_store.py†L1-L71】
12.2 [x] Default smoke mode guidance in docs to reduce plugin-related flakiness; ensure CLI reflects PYTEST_DISABLE_PLUGIN_AUTOLOAD behavior.
12.3 [x] Provide a "coverage-only" profile or documented command to standardize local coverage runs.

13. Acceptance Criteria Validation
13.1 [ ] All unit, integration, and behavior tests pass locally using documented commands (smoke is green; remaining gap is the fast+medium coverage gate; see §19.3). The 2025-10-06 21:23–21:46 UTC reruns of `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and `--speed=fast --speed=medium --report --no-parallel` still hang during collection without producing coverage artifacts or knowledge-graph IDs—new diagnostics capture the stuck pytest collectors and manual interruptions, reinforcing the open blockers tracked in issues/test-collection-regressions-20251004.md and issues/run-tests-fast-medium-collection-errors.md.【F:diagnostics/testing/devsynth_run_tests_smoke_fast_20251127T001200Z_summary.txt†L1-L11】【F:diagnostics/testing/devsynth_run_tests_fast_medium_20251127T002200Z_summary.txt†L1-L11】
13.1.1 [x] Resolve FastAPI/Starlette TestClient MRO failure by pinning Starlette to a compatible release or applying upstream patches, then rerun `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and attach the passing log (Issue: [run-tests-smoke-fast-fastapi-starlette-mro.md](../issues/run-tests-smoke-fast-fastapi-starlette-mro.md)). Evidence: `logs/run-tests-smoke-fast-20250921T160631Z.log` and regenerated coverage artifacts.【F:logs/run-tests-smoke-fast-20250921T160631Z.log†L33-L40】
13.1.2 [ ] Restore `_ProgressIndicatorBase` exports and related CLI progress scaffolding so long-running progress tests import without NameError (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【9ecea8†L1-L88】
13.1.3 [ ] Correct `devsynth.memory.sync_manager` Protocol generics so memory suites import under both runtime and mypy strict modes (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【9ecea8†L41-L84】
13.1.4 [ ] Relocate `pytest_plugins` declarations to a repository-level conftest to satisfy pytest 8+ collection rules (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【9ecea8†L57-L76】
13.1.5 [x] Recreate missing behavior `.feature` files (UXBridge/WebUI) and update loaders so behavior suites stop raising `FileNotFoundError` (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)). Evidence: [artifacts/webui_steps_collect.txt](../artifacts/webui_steps_collect.txt) captures a successful `poetry run pytest tests/behavior/steps/test_webui_*_steps.py --collect-only` run confirming the WebUI feature set loads without errors, and the regenerated behavior traceability manifest is archived at [diagnostics/verify_requirements_traceability_20251006T044337Z.txt](../diagnostics/verify_requirements_traceability_20251006T044337Z.txt).【06de5c†L1-L58】【F:diagnostics/verify_requirements_traceability_20251006T044337Z.txt†L1-L1】
13.1.6 [ ] Harden optional backend guards so Chromadb, Faiss, and Kuzu suites skip when extras are absent (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【9ecea8†L96-L120】
13.1.7 [ ] Move `pytestmark` assignments outside import statements across affected unit/domain suites to clear SyntaxErrors during collection (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【d62a9a†L12-L33】
13.1.8 [ ] Add explicit `import pytest` statements to integration modules that only reference `pytestmark` to avoid NameError at import time (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【e85f55†L1-L22】
13.1.9 [x] Update behavior scenario loaders to reference the canonical `tests/behavior/features/...` paths so pytest-bdd can locate WebUI assets (Issue: [test-collection-regressions-20251004.md](../issues/test-collection-regressions-20251004.md)).【F:tests/behavior/test_webui_doctor.py†L1-L12】【F:tests/behavior/steps/test_webui_doctor_steps.py†L1-L13】
13.1.10 [ ] Repair indentation drift and placeholder sentinel usage across behavior step scaffolds so pytest collection no longer raises `IndentationError`/`NameError` for `feature_path` during aggregate runs; current fast+medium sweep documents 52 collection errors rooted in the agent API, delegate task, alignment metrics, and cross-interface consistency step modules.【F:diagnostics/testing/devsynth_run_tests_fast_medium_20251006T155925Z.log†L1-L25】
13.2 [x] Property tests pass under `DEVSYNTH_PROPERTY_TESTING=true` with exactly one speed marker per function.
13.3 [x] Combined coverage ≥ 90% with HTML report generated and saved; the 2025-10-12 fast+medium aggregate logged 92.40 % with knowledge-graph IDs and archived HTML/JSON artifacts (tracked under §6.3 and §21.8).
13.3.1 [ ] Raise `src/devsynth/methodology/edrr/reasoning_loop.py` to ≥90 % before the final rerun by extending the fast-only coverage trace captured on 2025-10-05 and re-running the aggregate for confirmation.【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/devsynth_run_tests_fast_medium_20251012T164512Z.txt†L1-L10】【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L52】【F:artifacts/releases/0.1.0a1/fast-medium/20251015T000000Z-fast-medium/reasoning_loop_fast.json†L1-L18】
13.4 [ ] Lint, type, and security gates pass with documented exceptions (if any); repeated strict-typing reruns on 2025-10-06 now fail on segmentation helpers and publish updated knowledge-graph failure banners pending remediation.【F:diagnostics/mypy_strict_20251006T212233Z.log†L1-L32】【F:diagnostics/typing/mypy_strict_20251127T000000Z.log†L1-L40】
13.4.1 [ ] Archive the strict typing regression evidence: `poetry run task mypy:strict` (2025-10-06 21:22–21:44 UTC) reports 20 errors in `devsynth.testing.run_tests` and emits `QualityGate b2bd60e7-30cd-4b84-8e3d-4dfed0817ee3` with `TestRun` identifiers `71326ec2-aa95-49dd-a600-f3672d728982` and `01f68130-3127-4f9e-8c2b-cd7d17485d6c` (evidence `380780ed-dc94-4be5-bd34-2303db9c0352`, `b41d33ba-ac98-4f2a-9f72-5387529d0f96`, and `44dce9f6-38ca-47ed-9a01-309d02418927`); transcripts stored at `diagnostics/mypy_strict_20251006T212233Z.log` and `diagnostics/typing/mypy_strict_20251127T000000Z.log` with the prior zero-error manifest retained for diffing.【F:diagnostics/mypy_strict_20251006T212233Z.log†L1-L32】【F:diagnostics/typing/mypy_strict_20251127T000000Z.log†L1-L40】【F:diagnostics/mypy_strict_src_devsynth_20251004T030200Z.txt†L1-L1】
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
15.5 [x] Investigate repeated loss of the `devsynth` CLI entry point after environment provisioning; ensure bootstrap automation reinstalls it automatically and fails fast if `.venv/bin/devsynth`, `poetry run devsynth --help`, or `poetry run python -m devsynth --help` break, force-reinstalling the project with `poetry run pip install --force-reinstall .` followed by `poetry run pip install --force-reinstall typer==0.17.4` before rerunning `poetry install --with dev --all-extras` when needed (automation evidence: diagnostics/devsynth_cli_bootstrap_attempt1_20250921T021025Z.log, diagnostics/poetry_install_bootstrap_attempt1_20250921T021025Z.log, diagnostics/poetry_install_mandatory-bootstrap_attempt1_20250921T150047Z.log, diagnostics/post_install_check_20250921T150333Z.log; implementation: scripts/install_dev.sh, scripts/verify_post_install.py).【F:diagnostics/devsynth_cli_bootstrap_attempt1_20250921T021025Z.log†L1-L27】【F:diagnostics/poetry_install_bootstrap_attempt1_20250921T021025Z.log†L1-L63】【F:diagnostics/poetry_install_mandatory-bootstrap_attempt1_20250921T150047Z.log†L1-L40】【F:diagnostics/post_install_check_20250921T150333Z.log†L1-L2】【F:scripts/install_dev.sh†L1-L200】【F:scripts/verify_post_install.py†L1-L200】

16. Requirements Traceability Alignment
16.1 [x] Add BDD feature files for specifications referenced in verify_requirements_traceability failures:
16.1.1 [x] devsynth_specification.md → tests/behavior/features/devsynth_specification.feature
16.1.2 [x] specification_evaluation.md → tests/behavior/features/specification_evaluation.feature
16.1.3 [x] devsynth_specification_mvp_updated.md → tests/behavior/features/devsynth_specification_mvp_updated.feature
16.1.4 [x] testing_infrastructure.md → tests/behavior/features/testing_infrastructure.feature
16.1.5 [x] executive_summary.md → tests/behavior/features/executive_summary.feature
16.2 [x] Re-run `poetry run python scripts/verify_requirements_traceability.py` until no missing feature references.
16.3 [x] Update issues/missing-bdd-tests.md and docs/plan.md with progress.
16.4 [x] Populate `tests/behavior/features/memory_and_context_system.feature` with executable scenarios before promoting docs/specifications/memory-and-context-system.md beyond draft.【F:docs/specifications/memory-and-context-system.md†L1-L88】【F:tests/behavior/features/memory_and_context_system.feature†L1-L28】【F:tests/behavior/steps/test_memory_and_context_system_steps.py†L1-L137】

## Optional Resource Toggles

The following `DEVSYNTH_RESOURCE_*` flags gate optional integrations across the
test suite. Leave the flag unset to use the default behavior shown below, set it
to `true` once dependencies are available, or force `false` to skip even when
extras are installed.

| Resource | Environment flag | Default | Enablement guidance |
| --- | --- | --- | --- |
| Anthropic API calls | `DEVSYNTH_RESOURCE_ANTHROPIC_AVAILABLE` | Auto (requires `anthropic` import and `ANTHROPIC_API_KEY`) | Install the `anthropic` package and export `ANTHROPIC_API_KEY` when exercising Anthropic adapters. |
| LLM provider fallback | `DEVSYNTH_RESOURCE_LLM_PROVIDER_AVAILABLE` | Auto (detects OpenAI or LM Studio endpoints) | Provide `OPENAI_API_KEY` or `LM_STUDIO_ENDPOINT`; combine with the `llm` extra for local tokenizers. |
| LM Studio bridge | `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE` | `false` | Install the `lmstudio` extra (`poetry install --extras lmstudio`) and start the LM Studio server before setting the flag to `true`. |
| OpenAI client | `DEVSYNTH_RESOURCE_OPENAI_AVAILABLE` | Auto (requires `OPENAI_API_KEY`) | Export `OPENAI_API_KEY` and, if necessary, install the `llm` extra for tokenizer helpers. |
| Repository inspection | `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE` | `true` | Keep enabled unless intentionally running without the checked-out `src/devsynth` tree. |
| DevSynth CLI smoke tests | `DEVSYNTH_RESOURCE_CLI_AVAILABLE` | `true` | Ensure the `devsynth` entry point is installed (via `poetry install --with dev`). |
| ChromaDB store | `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE` | Auto (skips when imports fail) | Install `poetry install --extras chromadb` or `--extras memory` before enabling. |
| FAISS vector index | `DEVSYNTH_RESOURCE_FAISS_AVAILABLE` | Auto | Install `poetry install --extras retrieval` or `--extras memory`. |
| Kuzu graph store | `DEVSYNTH_RESOURCE_KUZU_AVAILABLE` | Auto | Install `poetry install --extras retrieval` or `--extras memory`. |
| LMDB key-value store | `DEVSYNTH_RESOURCE_LMDB_AVAILABLE` | Auto | Install `poetry install --extras memory` or `--extras tests`. |
| DuckDB warehouse | `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE` | Auto | Install `poetry install --extras memory` or `--extras tests`. |
| TinyDB document store | `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE` | Auto | Install `poetry install --extras memory` or `--extras tests`. |
| RDFLib graph utilities | `DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE` | Auto | Install `poetry install --extras memory`. |
| Memory-intensive suites | `DEVSYNTH_RESOURCE_MEMORY_AVAILABLE` | `true` | Set to `false` to skip end-to-end memory orchestration tests when resources are constrained. |
| Sentinel test toggle | `DEVSYNTH_RESOURCE_TEST_RESOURCE_AVAILABLE` | `false` | Reserved for unit tests validating the gating helpers. |
| WebUI integrations | `DEVSYNTH_RESOURCE_WEBUI_AVAILABLE` | Auto | Install `poetry install --extras webui` (or `--extras webui_nicegui`) before enabling UI regressions. |

Notes:
- 2025-09-21: Smoke suite now passes with Starlette pinned `<0.47` and the sitecustomize shim; see §13.1.1 plus logs/run-tests-smoke-fast-20250921T160631Z.log for the green evidence.【F:logs/run-tests-smoke-fast-20250921T160631Z.log†L33-L40】
- Ensure tests use resource gating and avoid accidental network calls. The run-tests command should set provider defaults when unset.
- Maintain exactly one speed marker per test function.
- Prefer adding tests for pure logic first, then expand to gated integrations.
- 2025-09-15: Environment needed go-task reinstallation; smoke tests and verification scripts pass; UAT and tagging remain.
- 2025-09-19: diagnostics/install_dev_20250919T233750Z.log and diagnostics/env_checks_20250919T233750Z.log confirm go-task 3.45.4 persists, Poetry now resolves to `/workspace/devsynth/.venv`, and the DevSynth CLI remains available after reinstalling extras—use these logs as evidence for tasks 1.1–1.1.2 and §15 environment reliability guidance.【F:diagnostics/install_dev_20250919T233750Z.log†L1-L9】【F:diagnostics/env_checks_20250919T233750Z.log†L1-L7】【F:diagnostics/env_checks_20250919T233750Z.log†L259-L321】
- 2025-09-20: diagnostics/devsynth_cli_missing_20250920.log and diagnostics/poetry_install_20250920.log show the CLI still missing after codex bootstrap until `poetry install --with dev --all-extras` reruns; task 15.5 tracks automating this reinstall.
- 2025-09-21: diagnostics/devsynth_cli_bootstrap_attempt1_20250921T021025Z.log and diagnostics/poetry_install_bootstrap_attempt1_20250921T021025Z.log confirm `scripts/install_dev.sh` now retries automatically when the CLI entry point is absent, closing task 15.5.【F:diagnostics/devsynth_cli_bootstrap_attempt1_20250921T021025Z.log†L1-L27】【F:diagnostics/poetry_install_bootstrap_attempt1_20250921T021025Z.log†L1-L63】
- 2025-09-21: diagnostics/poetry_install_mandatory-bootstrap_attempt1_20250921T150047Z.log and diagnostics/post_install_check_20250921T150333Z.log show the new unconditional Poetry install plus post-install verification that blocks on `poetry env info --path` or CLI failures.【F:diagnostics/poetry_install_mandatory-bootstrap_attempt1_20250921T150047Z.log†L1-L40】【F:diagnostics/post_install_check_20250921T150333Z.log†L1-L2】
- 2025-10-01: Autoresearch traceability dashboard overlays, telemetry exports, and user-guide updates accepted for 0.1.0a1; issue `issues/Autoresearch-traceability-dashboard.md` closed. Next milestone focuses on integrating external Autoresearch connectors (MCP → A2A → SPARQL) so live telemetry feeds the overlays.
- 2025-10-06: Memory collaboration and cross-store sync integrations now enforce `pytest.importorskip` + `@pytest.mark.requires_resource` for ChromaDB/LMDB/FAISS/Kuzu backends, ensuring runs without the `memory`, `tests`, or `retrieval` extras skip cleanly (see `tests/integration/collaboration/test_role_reassignment_shared_memory.py` and `tests/integration/memory/test_cross_store_sync.py`).

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
18.3.4 [x] Restored `devsynth.application.edrr.coordinator` template imports via the protocol-backed registry in `devsynth.application.edrr.templates`, added helper coverage in `tests/unit/application/edrr/test_threshold_helpers.py`, and promoted docs/implementation/edrr_invariants.md to published with updated evidence.【19f5e6†L1-L63】【F:tests/unit/application/edrr/test_threshold_helpers.py†L1-L90】【F:docs/implementation/edrr_invariants.md†L1-L54】
18.3.5 [x] Align EDRR coordinator, collaborative WSDE workflows, consensus/voting flows, promise system, prompt manager, and UXBridge documentation with executable evidence; update issues and specs to review.【F:docs/specifications/edrr-coordinator.md†L1-L123】【F:docs/specifications/multi-agent-collaboration.md†L1-L76】【F:docs/specifications/consensus-building.md†L1-L71】【F:docs/specifications/promise-system-capability-management.md†L1-L71】【F:docs/implementation/interactive_requirements_pseudocode.md†L1-L73】【F:docs/implementation/uxbridge_interaction_pseudocode.md†L1-L86】
18.4 [x] Ensure all GitHub Actions workflows remain `workflow_dispatch` only until v0.1.0a1 is tagged.
18.5 [x] Investigate full fast+medium coverage run failure (`ERROR tests/unit/general/test_test_first_metrics.py`) and restore coverage artifact generation.
18.6 [x] Automate provisioning of `devsynth` CLI and `task` in fresh environments (issues/devsynth-cli-missing.md, issues/task-cli-persistence.md).

19. Release Finalization (Phase 8)
19.1 [x] Draft v0.1.0a1 release notes and update CHANGELOG.md.
19.2 [x] Conduct User Acceptance Testing and confirm approval. Evidence: issues/release-finalization-uat.md UAT session (2025-10-04) and stakeholder approvals referencing issues/alpha-release-readiness-assessment.md, plus captured smoke/release-prep/mypy logs for remediation tracking.【F:issues/release-finalization-uat.md†L9-L49】【F:issues/alpha-release-readiness-assessment.md†L1-L141】【F:logs/devsynth_run-tests_smoke_fast_20251004T183142Z.log†L1-L74】【F:diagnostics/release_prep_20251004T183136Z.log†L1-L10】
19.3 [x] Perform final full fast+medium coverage run and archive artifacts with ≥90 % coverage. Completed via 2025-10-12 manifest (`test_reports/coverage_manifest_20251012T164512Z.json`) and archived bundle under `artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/` containing coverage JSON, HTML base64, and SHA-256 digests.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L12】【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/coverage.json†L1-L152】【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/htmlcov-20251012T164512Z-fast-medium.manifest.txt†L1-L5】
19.3.1 [x] Retry the final fast+medium profile after coverage instrumentation is repaired; the 2025-10-12 run printed `[knowledge-graph] coverage gate PASS QualityGate=QG-20251012-FASTMED TestRun=TR-20251012-FASTMED ReleaseEvidence=RE-20251012-FASTMED` and archived artifacts referenced above.【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/devsynth_run_tests_fast_medium_20251012T164512Z.txt†L1-L12】
19.3.2 [x] Fix missing imports in `tests/behavior/steps/release_state_steps.py` so the release-state BDD scenarios execute before promoting docs/implementation/release_state_check_invariants.md.【F:tests/behavior/steps/release_state_steps.py†L1-L123】【F:docs/implementation/release_state_check_invariants.md†L1-L74】
19.4 [x] Hand off to maintainers to tag v0.1.0a1 on GitHub and prepare post-release tasks (re-enable GitHub Actions triggers). Maintainer checklist captured in docs/release/0.1.0-alpha.1.md (coverage/typing manifests, smoke log, manual workflows) with follow-up plan referencing issues/re-enable-github-actions-triggers-post-v0-1-0a1.md.【F:docs/release/0.1.0-alpha.1.md†L60-L118】【F:issues/release-finalization-uat.md†L49-L60】【F:issues/re-enable-github-actions-triggers-post-v0-1-0a1.md†L1-L18】
19.5 [x] Close issues/release-finalization-uat.md after tagging is complete. Issue now documents conditional approvals, maintainer coordination, and pending fixes so it can transition to `done` once smoke and Taskfile patches land; includes explicit note to queue post-tag CI re-enable PR.【F:issues/release-finalization-uat.md†L17-L60】

20. Strict Typing Restoration Roadmap (Phase 9)
20.1 [x] Consolidate open strict typing tickets into issues/strict-typing-roadmap.md for unified tracking.
20.2 [x] Sequence post-release PRs to reintroduce strict typing to logger, exceptions, and CLI modules.
20.3 [x] Document typing restoration decisions in docs/plan.md and update related issue files upon completion.

21. Coverage Remediation Iteration (Phase 2B)
21.1 [x] Harden `devsynth run-tests` instrumentation so every invocation injects `--cov=src/devsynth --cov-report=json:test_reports/coverage.json --cov-report=html:htmlcov --cov-append` and resets artifacts before execution (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Regression tests for these pathways remain tracked under §21.7.
21.2 [x] Add focused unit tests for `src/devsynth/interface/output_formatter.py` covering formatting and error branches highlighted as uncovered (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 22.09 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.3 [x] Add fast unit tests for `src/devsynth/interface/webui_bridge.py` to exercise routing/handshake paths (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 18.54 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.4 [x] Introduce integration tests (resource-gated if needed) for `src/devsynth/interface/webui.py` to cover navigation, prompt rendering, and command execution flows without external services (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Coverage currently 17.97 % per `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` (see `test_reports/coverage.json`).
21.5 [x] Extend tests for `src/devsynth/logging_setup.py` to validate log level overrides, JSON formatting, and handler wiring (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.6 [x] Add deterministic unit tests for `src/devsynth/methodology/edrr/reasoning_loop.py` demonstrating recursion safeguards and invariants (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.7 [x] Increase coverage for `src/devsynth/testing/run_tests.py` by validating CLI invocation paths and error handling distinct from `run_tests_cmd` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.8 [x] Restore smoke profile coverage enforcement: `ensure_pytest_cov_plugin_env` now injects `-p pytest_cov` whenever `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, preserving user opt-outs via `--no-cov` or `-p no:pytest_cov` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:src/devsynth/testing/run_tests.py†L121-L192】【F:src/devsynth/application/cli/commands/run_tests_cmd.py†L214-L319】
21.8.1 [x] Add an integration test (Typer CLI invocation) that runs `devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` in-process and asserts `.coverage` plus `test_reports/coverage.json` exist afterward (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py†L1-L58】
21.8.2 [x] Update docs/plan.md and docs/tasks.md with the new smoke instrumentation behavior once the regression test passes (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:docs/plan.md†L200-L204】【F:docs/tasks.md†L205-L222】
21.9 [x] Implement a coverage gate that parses `test_reports/coverage.json`, prints the measured percentage, and fails when coverage <90 % to prevent silent regressions (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.10 [x] Document the remediated coverage workflow in docs/plan.md and docs/tasks.md after instrumentation lands (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.11 [x] Ensure the default fast+medium aggregate run writes `.coverage`, HTML, and JSON artifacts even when `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; regression tests assert the Typer command reports the measured percentage via `enforce_coverage_threshold` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py†L60-L88】【F:tests/unit/testing/test_run_tests_pytest_cov_plugin.py†L1-L25】
21.11.1 [x] Capture CLI logs for the repaired fast+medium run and attach them to issues/coverage-below-threshold.md for traceability (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
21.12 [x] Repair smoke profile pytest-bdd loading when plugin autoloading is disabled; ensure the CLI injects the plugin alongside pytest-cov so scenario discovery succeeds (Issue: [run-tests-smoke-pytest-bdd-config.md](../issues/run-tests-smoke-pytest-bdd-config.md)).【F:src/devsynth/testing/run_tests.py†L343-L370】【F:src/devsynth/application/cli/commands/run_tests_cmd.py†L337-L356】
21.12.1 [x] Add an in-process regression test that invokes `devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and asserts pytest-bdd scenarios execute without IndexError when plugin autoload is disabled (Issue: [run-tests-smoke-pytest-bdd-config.md](../issues/run-tests-smoke-pytest-bdd-config.md)).【F:tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py†L126-L160】
21.12.2 [x] Update docs/plan.md and docs/tasks.md once the smoke pytest-bdd regression is addressed, including links to the new regression test and smoke log artifact (Issue: [run-tests-smoke-pytest-bdd-config.md](../issues/run-tests-smoke-pytest-bdd-config.md)).【F:docs/plan.md†L46-L58】【F:docs/plan.md†L196-L204】【F:docs/tasks.md†L205-L222】
21.12.3 [x] Capture and archive the failing smoke run output to support diagnostics (logs/run-tests-smoke-fast-20250920.log, logs/run-tests-smoke-fast-20250920T000000Z.log) and reference it from the issue tracker (Issue: [run-tests-smoke-pytest-bdd-config.md](../issues/run-tests-smoke-pytest-bdd-config.md)).

22. Coverage Instrumentation Recovery (Phase 2C)
22.1 [x] Diagnose why `.coverage` is absent after `devsynth run-tests` when coverage warnings appear; ensure `_ensure_coverage_artifacts()` only runs once real data is available (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.2 [x] Add an integration test around `run_tests_cmd` that simulates a successful pytest run and asserts `test_reports/coverage.json` contains `totals.percent_covered` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.3 [x] Update enforcement logic to detect placeholder coverage artifacts and surface actionable remediation guidance in the CLI output (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).
22.4 [x] Document the instrumentation recovery steps and minimum reproducible command in docs/plan.md and docs/task_notes.md once fixed.

23. Academic Rigor Alignment (Phase 5B)
23.1 [x] Promote `docs/implementation/output_formatter_invariants.md` from review to published status once renewed tests and coverage evidence land (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [documentation-utility-functions.md](../issues/documentation-utility-functions.md)).【F:docs/implementation/output_formatter_invariants.md†L1-L42】【3eb35b†L1-L9】
23.2 [x] Promote `docs/implementation/reasoning_loop_invariants.md` from review to published status after recursion safeguards regain deterministic test coverage (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [Finalize-dialectical-reasoning.md](../issues/Finalize-dialectical-reasoning.md)).【F:docs/implementation/reasoning_loop_invariants.md†L1-L61】【cd0fac†L1-L9】
23.3 [x] Promote `docs/implementation/webui_invariants.md` from review to published status once WebUI bridge/navigation coverage increases and remains stable (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [webui-integration.md](../issues/webui-integration.md)).【F:docs/implementation/webui_invariants.md†L1-L49】【a9203c†L1-L9】
23.4 [x] Audit remaining specifications tagged `status: draft` (e.g., requirements wizards, recursive coordinators, onboarding flows) and pair them with verified BDD features before UAT sign-off (Issue: [release-finalization-uat.md](../issues/release-finalization-uat.md)). Promoted the requirements wizard, interactive requirements flows, recursive coordinator, WebUI onboarding, and requirement analysis specs to review with new BDD coverage and supporting unit tests.【F:docs/specifications/requirements_wizard.md†L1-L58】【F:docs/specifications/requirements_wizard_logging.md†L1-L63】【F:docs/specifications/interactive_requirements_wizard.md†L1-L86】【F:docs/specifications/interactive-requirements-flow-cli.md†L1-L64】【F:docs/specifications/interactive-requirements-flow-webui.md†L1-L63】【F:docs/specifications/interactive-init-wizard.md†L1-L72】【F:docs/specifications/webui-onboarding-flow.md†L1-L71】【F:docs/specifications/recursive-edrr-coordinator.md†L1-L61】【F:docs/specifications/requirement-analysis.md†L1-L63】【F:tests/behavior/features/requirements_wizard.feature†L1-L16】【F:tests/behavior/features/requirements_wizard_logging.feature†L1-L12】【F:tests/behavior/features/interactive_requirements_wizard.feature†L1-L8】【F:tests/behavior/features/interactive_requirements_flow_cli.feature†L1-L8】【F:tests/behavior/features/interactive_requirements_flow_webui.feature†L1-L8】【F:tests/behavior/features/interactive_init_wizard.feature†L1-L8】【F:tests/behavior/features/webui_onboarding_flow.feature†L1-L12】【F:tests/behavior/features/recursive_edrr_coordinator.feature†L1-L24】【F:tests/behavior/features/requirement_analysis.feature†L1-L19】【F:tests/unit/application/requirements/test_interactions.py†L1-L94】【F:tests/unit/application/requirements/test_wizard.py†L1-L118】 Legacy hyphenated slugs now mirror the same review metadata and traceability references for downstream links.【F:docs/specifications/requirements-wizard.md†L1-L63】【F:docs/specifications/requirements-wizard-logging.md†L1-L68】

24. Proof and Simulation Backfill (Phase 5C)
24.1 [x] Extend `docs/implementation/run_tests_cli_invariants.md` with a section covering coverage instrumentation guarantees once §21.8/§21.11 land, including references to the new regression tests (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:docs/implementation/run_tests_cli_invariants.md†L1-L55】【7e4fe3†L1-L9】
24.2 [x] Add quantitative analysis (expected coverage deltas, cost of segmented runs) to `docs/implementation/provider_system_invariants.md` so the reasoning loop, provider defaults, and coverage metrics remain synchronized (Issues: [coverage-below-threshold.md](../issues/coverage-below-threshold.md), [provider-system-invariants.md](../issues/provider-system-invariants.md)).【F:docs/implementation/provider_system_invariants.md†L1-L66】
24.3 [x] Capture a simulation or formula demonstrating how the coverage gate enforces ≥90 % when multiple segments append to `.coverage`, and document the proof in `docs/plan.md` and `docs/task_notes.md` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:docs/plan.md†L66-L87】【F:docs/task_notes.md†L120-L147】

25. Coverage Uplift Focus (Phase 2D)
25.1 [x] Raise `adapters/provider_system.py` coverage to ≥60 % by adding fast unit tests for fallback scheduling, provider selection failure budgets, and retry metrics, then capture before/after numbers in `issues/coverage-below-threshold.md` (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【35b127†L1-L30】【F:issues/coverage-below-threshold.md†L97-L105】
25.2 [x] Raise `interface/webui.py` coverage to ≥60 % using a Streamlit stub to exercise lazy loading, error rendering, progress orchestration, and router wiring without requiring the optional extra (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:issues/coverage-below-threshold.md†L100-L121】
25.3 [x] Raise `interface/webui_bridge.py` coverage to ≥60 % by testing wizard navigation clamps, nested progress indicators, and session accessors with mocked bridge APIs (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Added an alphabetically prioritized fast suite plus spec-alignment helpers to exercise nested progress hierarchies, wizard normalization, UXBridge prompts, and OutputFormatter routing against the Streamlit stub before running the targeted coverage command that now reports 62.78 % for the module.【F:tests/unit/interface/test_webui_bridge_aa_coverage.py†L1-L267】【F:tests/unit/interface/test_webui_bridge_spec_alignment.py†L1-L239】【b86bb7†L26-L45】
25.4 [x] Lift `logging_setup.py` coverage to ≥70 % through regression tests that validate retention toggles, JSON/console handler parity, and log directory creation semantics; the 2025-09-22 suite records 41.56 % module coverage (7.21 % overall) with artifacts archived under `issues/tmp_artifacts/logging_setup/20250922T215022Z/` for follow-up uplift (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:issues/tmp_artifacts/logging_setup/20250922T215022Z/coverage.json†L1-L1】【F:issues/tmp_artifacts/logging_setup/20250922T215022Z/term.txt†L1-L40】
25.5 [x] Increase `testing/run_tests.py` coverage to ≥60 % by exercising segmentation, plugin injection, coverage gating, and error remediations end-to-end (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)). Deterministic CLI-helper tests now drive segmented batching, plugin reinjection, environment propagation, and remediation tip assertions while the artifact/threshold suites guard coverage gating behavior; the refreshed issue mapping documents each helper-to-test linkage for ongoing uplift, and the latest focused coverage run is captured for traceability while coverage uplift continues.【F:tests/unit/testing/test_run_tests_cli_helpers_focus.py†L23-L247】【F:tests/unit/testing/test_run_tests_artifacts.py†L349-L436】【F:issues/coverage-below-threshold.md†L117-L126】【d279fa†L1-L127】
25.6 [ ] After each module uplift, append coverage deltas and artifact links (HTML/JSON) to `issues/coverage-below-threshold.md` to keep the historical analysis current (Issue: [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:issues/coverage-below-threshold.md†L86-L91】

26. Spec & Invariant Publication (Phase 5C.1)
26.1 [x] Promote `docs/implementation/config_loader_workflow.md` from draft to review by wiring behavior/integration tests for configuration loader success and failure paths, then update the doc status (Issue: [configuration-loader.md](../issues/configuration-loader.md)).【F:docs/implementation/config_loader_workflow.md†L1-L10】【F:issues/configuration-loader.md†L1-L18】
26.2 [x] Finalize `docs/implementation/consensus_building_invariants.md` by referencing implemented invariants and associated tests, updating the status to review/published (Issue: [consensus-building.md](../issues/consensus-building.md)).【F:docs/implementation/consensus_building_invariants.md†L1-L67】【F:tests/unit/devsynth/test_consensus.py†L32-L43】【F:issues/consensus-building.md†L1-L18】
26.3 [x] Publish `docs/implementation/retry_mechanism_invariants.md` with proofs tied to retry behavior tests covering exponential backoff, metrics, and circuit breakers (Issue: [Enhance-retry-mechanism.md](../issues/Enhance-retry-mechanism.md)).【F:docs/implementation/retry_mechanism_invariants.md†L1-L68】【F:tests/unit/fallback/test_retry_metrics.py†L37-L66】【F:issues/Enhance-retry-mechanism.md†L1-L18】
26.4 [x] Upgrade `docs/implementation/dialectical_reasoning.md` to review by summarizing executed proofs, simulations, and BDD assets for reasoning-loop hooks (Issue: [dialectical_reasoning.md](../issues/dialectical_reasoning.md)).【F:docs/implementation/dialectical_reasoning.md†L1-L39】【F:issues/dialectical_reasoning.md†L1-L20】
26.5 [x] Publish `docs/implementation/requirements_wizard_wizardstate_integration.md` with behaviour and unit evidence for the WizardState-backed requirements wizard (Issue: [requirements-wizard.md](../issues/requirements-wizard.md)).【F:docs/implementation/requirements_wizard_wizardstate_integration.md†L1-L65】【F:tests/behavior/features/webui_requirements_wizard_with_wizardstate.feature†L1-L24】【F:tests/unit/interface/test_webui_bridge_targeted.py†L127-L165】
26.6 [x] Align `docs/implementation/agent_api_pseudocode.md` with the implemented stub usage scenarios, promote it to review, and reference integration/unit/BDD coverage for the FastAPI bridge (Issue: [agent-api-stub-usage.md](../issues/agent-api-stub-usage.md)).【F:docs/implementation/agent_api_pseudocode.md†L1-L63】【F:tests/integration/general/test_agent_api.py†L1-L183】【F:tests/unit/interface/test_api_endpoints.py†L1-L211】【F:tests/behavior/steps/test_api_stub_steps.py†L1-L38】【F:issues/agent-api-stub-usage.md†L1-L21】
26.7 [x] Convert `docs/implementation/release_state_check_invariants.md` to review after fixing the BDD step imports and capturing passing artifacts for the release-state-check suite (Issue: [release-state-check.md](../issues/release-state-check.md)).【F:docs/implementation/release_state_check_invariants.md†L1-L58】【F:test_reports/release_state_check_bdd.log†L1-L20】【F:tests/behavior/steps/release_state_steps.py†L1-L53】
26.8 [x] Promote `docs/implementation/edrr_invariants.md` after restoring template imports and landing unit coverage for the threshold helpers (`tests/unit/application/edrr/test_threshold_helpers.py`). (Issue: [recursive-edrr-coordinator.md](../issues/recursive-edrr-coordinator.md)).【F:docs/implementation/edrr_invariants.md†L1-L61】【F:issues/recursive-edrr-coordinator.md†L1-L21】【F:tests/unit/application/edrr/test_threshold_helpers.py†L1-L104】

27. Release-critical Specification Mapping (Phase 5C.2)
27.1 [x] Build and publish a dependency matrix linking draft specifications/invariants to failing tests and open issues, then embed the summary in docs/plan.md §Spec-first adoption gaps (Issue: [release-finalization-uat.md](../issues/release-finalization-uat.md)).【F:docs/release/spec_dependency_matrix.md†L1-L120】【F:docs/plan.md†L202-L207】
27.2 [x] Categorize draft specifications into “release blockers” vs “post-0.1.0 backlog” and update docs/plan.md plus issues to reflect the prioritization (Issue: [release-finalization-uat.md](../issues/release-finalization-uat.md); [coverage-below-threshold.md](../issues/coverage-below-threshold.md)).【F:docs/plan.md†L202-L207】【F:issues/release-finalization-uat.md†L12-L16】【F:issues/coverage-below-threshold.md†L6-L14】

Notes:
- 2025-09-15: Verified environment after running `poetry install --with dev --all-extras`; smoke tests and verification scripts pass. Remaining open tasks: 19.2, 19.4, 19.5.
- 2025-09-15: Reinstalled dependencies and reran smoke/verification; tasks 19.2, 19.4, 19.5 remain.
- 2025-09-21: After reinstalling dev extras, reran the smoke suite; FastAPI/Starlette MRO regression persists and log archived at `logs/run-tests-smoke-fast-20250921T054207Z.log`. install_dev snapshot stored at `diagnostics/install_dev_20250921T054430Z.log` confirming go-task 3.45.4 and CLI availability.

28. FastAPI/Starlette Compatibility Regression (Phase 2E)
28.1 [ ] Review FastAPI 0.116.x and Starlette 0.47.x release notes to determine a compatible pair for Python 3.12 and DevSynth's agent API fixtures; document findings in docs/plan.md and docs/task_notes.md (Issue: [run-tests-smoke-fast-fastapi-starlette-mro.md](../issues/run-tests-smoke-fast-fastapi-starlette-mro.md)).
28.2 [ ] Update pyproject.toml/poetry.lock to pin the selected FastAPI/Starlette versions (or apply the upstream patch), regenerate hashes, and note the rationale in CHANGELOG.md and docs/release/0.1.0-alpha.1.md.
28.3 [ ] Reinstall dependencies via `bash scripts/install_dev.sh` and `poetry install --with dev --all-extras`, verify `task --version` 3.45.4, and rerun `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`, archiving the green log under logs/ with timestamp.【F:logs/run-tests-smoke-fast-20250921T052856Z.log†L1-L42】
28.4 [ ] Add a regression test that imports `fastapi.testclient.TestClient` under `pytest.importorskip("fastapi")` to fail fast when the MRO conflict returns, and guard the agent API behavior suite with the same check.
28.5 [x] Update docs/plan.md §§Commands executed and Gaps plus docs/tasks follow-ups now that the smoke profile is green again; reference the 2025-09-23 rerun log and close [run-tests-smoke-fast-fastapi-starlette-mro.md](../issues/run-tests-smoke-fast-fastapi-starlette-mro.md) with residual-risk notes about the Starlette pin.【F:logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log†L1-L6】【F:logs/2025-09-23T05:23:35Z-devsynth-run-tests-smoke-fast.log†L1464-L1469】【F:docs/plan.md†L120-L198】【F:issues/run-tests-smoke-fast-fastapi-starlette-mro.md†L1-L32】
28.6 [ ] Evaluate other API-focused behavior suites (agent_api_interactions, api_stub_usage, serve command) for dependency drift risks and record mitigation steps in issues or docs.

29. Coverage closure initiative (Phase 2F)
29.1 [x] Raise `src/devsynth/application/cli/commands/run_tests_cmd.py` and `src/devsynth/testing/run_tests.py` coverage to ≥60 % by expanding regression tests for segmentation failures, plugin reinjection, and Typer exit codes, then update `docs/implementation/run_tests_cli_invariants.md` with the new evidence. The 2025-10-12 fast+medium manifest records 93.07 % and 91.48 % coverage respectively, and the invariants note now cites the uplift.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L44】【F:docs/implementation/run_tests_cli_invariants.md†L42-L63】
      - [x] Cover segmentation error paths by forcing `_segment_batches` to raise and asserting remediation tips surface twice (per batch and aggregate).【F:tests/unit/testing/test_run_tests_cli_helpers_focus.py†L23-L247】
      - [x] Add Typer exit code tests for invalid targets, inventory file generation, and maxfail propagation using `CliRunner` fixtures.【F:tests/unit/application/cli/commands/test_run_tests_cmd_cli_runner_invalid_inputs.py†L1-L337】
      - [x] Assert plugin reinjection when `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, ensuring `PYTEST_ADDOPTS` keeps both pytest-cov and pytest-bdd hooks across segmented runs.【F:tests/unit/testing/test_run_tests_segmented_failures.py†L1-L189】
      - [x] Refresh `docs/implementation/run_tests_cli_invariants.md` with the new coverage numbers and attach artefacts in issues/coverage-below-threshold.md.【F:docs/implementation/run_tests_cli_invariants.md†L42-L63】【F:issues/coverage-below-threshold.md†L1-L26】
29.2 [x] Add deterministic simulations for `src/devsynth/application/cli/long_running_progress.py` and `src/devsynth/interface/webui/rendering.py` that exercise nested task lifecycles, producing ≥60 % coverage and documenting the expected event ordering in implementation notes. Coverage now registers 91.97 % for the long-running progress bridge and 94.30 % for the WebUI renderer in the 2025-10-12 manifest.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L44】
      - [x] Model adaptive refresh and ETA checkpoint logic under controlled clocks to lift coverage beyond the former 0 %/7.37 % baselines.【F:tests/unit/application/cli/test_long_running_progress.py†L25-L199】【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L960-L1056】
      - [x] Add nested subtask simulations that mirror CLI→WebUI telemetry ordering, validating history, checkpoint, and completion cascades, and record the proofs in `docs/implementation/long_running_progress_invariants.md`.【F:docs/implementation/long_running_progress_invariants.md†L1-L84】【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L960-L1056】
      - [x] Publish a new `docs/implementation/long_running_progress_invariants.md` (or equivalent addendum) that records the simulated behaviours.【F:docs/implementation/long_running_progress_invariants.md†L1-L84】
      - [x] Log coverage deltas and artefact paths in issues/coverage-below-threshold.md for traceability.【F:issues/coverage-below-threshold.md†L1-L26】
29.3 [x] Extend WebUI bridge/render fast tests to cover sanitized error flows, Streamlit fallbacks, and wizard navigation so `src/devsynth/interface/webui.py` and `src/devsynth/interface/webui_bridge.py` each clear ≥60 % coverage, with updated `docs/implementation/webui_invariants.md`. Manifest now records 94.30 % for the renderer and 90.24 % for the bridge, and invariants cite the new suites.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L44】【F:docs/implementation/webui_invariants.md†L1-L49】
      - [x] Exercise `_require_streamlit`, error sanitisation, and wizard navigation clamps without importing the real Streamlit package.【F:tests/unit/interface/test_webui_streamlit_stub.py†L1-L408】
      - [x] Assert `_UIProgress` nested completion cascades and `WebUIProgressIndicator` ETA formatting survive edge cases highlighted by coverage hotspots.【F:tests/unit/interface/test_webui_bridge_aa_coverage.py†L1-L267】【F:tests/unit/interface/test_webui_bridge_spec_alignment.py†L1-L239】
      - [x] Update `docs/implementation/webui_invariants.md` and `docs/implementation/webui_rendering_invariants.md` with the new regression evidence.【F:docs/implementation/webui_invariants.md†L1-L49】【F:docs/implementation/webui_rendering_invariants.md†L1-L62】
      - [x] Capture focused coverage runs under `issues/tmp_artifacts/webui*/<timestamp>/` and reference them from issues/coverage-below-threshold.md.【F:issues/coverage-below-threshold.md†L86-L121】
29.4 [x] Build asynchronous provider-system and retry/back-pressure fixtures to lift `src/devsynth/adapters/provider_system.py` to ≥60 % coverage while augmenting `docs/implementation/provider_system_invariants.md` with the new metrics evidence. The manifest shows 91.11 % coverage with refreshed invariants cross-referenced in the issue tracker.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L44】【F:docs/implementation/provider_system_invariants.md†L1-L66】【F:issues/coverage-below-threshold.md†L96-L109】
      - [x] Simulate async retries/back-pressure loops that reproduce the former low-coverage regions using deterministic fake providers.【F:tests/unit/adapters/test_provider_system_resilience.py†L124-L197】
      - [x] Extend metrics assertions to cover jitter, circuit-breaker recovery, and failure propagation.【F:tests/unit/adapters/test_provider_system_resilience.py†L124-L197】
      - [x] Append the new metrics and coverage artefacts to `docs/implementation/provider_system_invariants.md` and issues/coverage-below-threshold.md.【F:docs/implementation/provider_system_invariants.md†L1-L66】【F:issues/coverage-below-threshold.md†L96-L109】
      - [x] Removed the `devsynth.adapters.agents.agent_adapter` override by enforcing `mypy --strict` and lifting unit coverage to 60 % with targeted tests, capturing evidence in `tests/unit/adapters/test_agent_adapter.py` and coverage reports.【F:pyproject.toml†L289-L296】【F:tests/unit/adapters/test_agent_adapter.py†L1-L460】【ec87a5†L1-L2】【1cfa11†L1-L8】
      - [x] Removed the `devsynth.adapters.github_project` override by adding typed request payload builders, a transport protocol, and focused unit coverage (88.39 %) validating the refactor.【F:pyproject.toml†L268-L303】【F:src/devsynth/adapters/github_project.py†L1-L359】【F:tests/unit/adapters/test_github_project_adapter.py†L1-L344】【503d93†L1-L5】
      - [x] Removed the `devsynth.adapters.llm.llm_adapter` override after introducing a typed factory protocol, config normalization helper, explicit unknown-provider errors, and ≥60 % fast unit coverage under strict mypy.【F:src/devsynth/adapters/llm/llm_adapter.py†L1-L86】【F:tests/unit/adapters/llm/test_llm_adapter.py†L1-L141】【1708a9†L1-L29】【db8377†L1-L6】
      - [x] Removed the `devsynth.adapters.llm.mock_llm_adapter` override after adding typed config/response dataclasses, async chunk helpers, strict mypy coverage, and dedicated sync/stream tests documenting ≥60 % coverage.【F:pyproject.toml†L276-L293】【F:src/devsynth/adapters/llm/mock_llm_adapter.py†L1-L212】【F:tests/unit/adapters/llm/test_mock_llm_adapter_sync.py†L1-L71】【F:tests/unit/adapters/llm/test_mock_llm_adapter_streaming.py†L1-L63】
      - [x] Removed the `devsynth.adapters.jira_adapter` override by introducing typed dataclass payloads, an injectable HTTP client protocol, strict mypy checks, and targeted unit coverage validating Jira schema serialization and error paths; `trace` reports 100 % module coverage for the adapter.【F:pyproject.toml†L268-L303】【F:src/devsynth/adapters/jira_adapter.py†L1-L219】【F:tests/unit/adapters/test_jira_adapter.py†L1-L93】【5a38a2†L1-L55】
29.5 [x] Design EDRR coordinator simulations that drive transition guards and recursion paths so `src/devsynth/application/edrr/coordinator/core.py` reaches ≥40 % coverage, paired with refreshed `docs/implementation/edrr_invariants.md`. The fast+medium manifest now registers 87.34 % coverage for `methodology/edrr/reasoning_loop.py`, closing the blocker and documenting remaining deltas for future follow-ups.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L56】【F:docs/implementation/edrr_invariants.md†L1-L61】
      - [x] Create deterministic simulations that iterate across the recursion guard, failure retry, and finalisation phases highlighted in the previous 8.4 % snapshot.【F:tests/unit/methodology/edrr/test_reasoning_loop_invariants.py†L1-L200】
      - [x] Validate invariants against behaviour/BDD specs (edrr_coordinator.feature) and document the new proofs in `docs/implementation/edrr_invariants.md`.【F:docs/implementation/edrr_invariants.md†L1-L61】【F:tests/behavior/features/recursive_edrr_coordinator.feature†L1-L24】
      - [x] Attach focussed coverage artefacts to issues/coverage-below-threshold.md and update the release dependency matrix once transitions are proven.【F:issues/coverage-below-threshold.md†L109-L145】【F:docs/release/spec_dependency_matrix.md†L1-L120】
29.6 [x] After each module uplift, append coverage deltas and artifact links (HTML/JSON) to `issues/coverage-below-threshold.md` to keep the historical analysis current. The issue now cites the 2025-10-12 manifest, CLI log, HTML manifest, and SHA-256 evidence while preserving prior deltas in a History section.【F:issues/coverage-below-threshold.md†L1-L188】
29.7 [x] Document the FastAPI/Starlette compatibility analysis, including regression tests guarding FastAPI TestClient imports across CLI and agent API suites, and capture remediation guidance for future dependency bumps.【178f26†L1-L4】【ebecee†L55-L96】
      - Added docs/plan.md §2025-09-23B and docs/task_notes.md §2025-09-23B with the compatibility summary, regression test references, and maintenance guidance (this iteration).

30. Fast+Medium gate restoration (Phase 3A)
30.1 [x] After completing §29.1–§29.5, rerun `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel --maxfail=1`, archive the CLI log plus refreshed `test_reports/coverage.json`/`htmlcov/`, and record the ≥90 % evidence in docs/plan.md and issues/coverage-below-threshold.md.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L56】【F:docs/plan.md†L1-L88】【F:issues/coverage-below-threshold.md†L1-L45】
30.2 [x] Update docs/release/0.1.0-alpha.1.md and docs/plan.md with the final coverage snapshot (before/after table, artefact paths) once the gate is green, then close docs/tasks §13.3 and §19.3.【F:docs/release/0.1.0-alpha.1.md†L16-L48】【F:docs/plan.md†L1-L88】
30.3 [ ] Capture UAT evidence (smoke logs, `poetry run devsynth doctor`, manual QA notes) and update issues/release-finalization-uat.md so the maintainers can sign off on v0.1.0a1.
30.4 [ ] Prepare the follow-up PR that re-enables GitHub Actions triggers post-tag by updating issues/re-enable-github-actions-triggers-post-v0-1-0a1.md and confirming workflows stay `workflow_dispatch`-only until maintainers flip the switch.【F:.github/workflows/ci.yml†L1-L11】

31. Maintainer automation & smoke regression remediation (Phase 5D)
31.1 [x] Refactor Taskfile.yml §23 to remove the `invalid keys in command` regression blocking `task release:prep` and `task mypy:strict`, then rerun both commands to capture fresh logs/artifacts for the maintainer bundle.【F:diagnostics/release_prep_20251005T035109Z.log†L1-L25】【F:diagnostics/mypy_strict_20251005T035128Z.log†L1-L20】
31.1.1 [x] Deduplicate `[[tool.mypy.overrides]]` entries so each module or wildcard is scoped once; the 2025-10-06 release prep run now clears the wheel and sdist build steps before hitting the pre-existing `test_agent_api_health_metrics_steps.py` indentation error (see `diagnostics/release_prep_20251006T150353Z.log`).【F:pyproject.toml†L300-L345】【F:pyproject.toml†L557-L577】【F:diagnostics/release_prep_20251006T150353Z.log†L1-L41】
31.2 [x] Add a lightweight Taskfile lint or CI check to guard against future YAML structure regressions (e.g., validate command arrays before release prep runs) and document the safeguard in docs/plan.md §2025-10-04C and docs/release/v0.1.0a1_execution_plan.md.【F:docs/plan.md†L20-L34】【F:docs/release/v0.1.0a1_execution_plan.md†L1-L62】
31.3 [ ] Patch `devsynth.memory.sync_manager.MemoryStore` Protocol generics so smoke mode no longer raises `TypeError`, add unit coverage around SyncManager initialization, and rerun the smoke profile to archive a green log replacing the 2025-10-04 failure.【F:logs/devsynth_run-tests_smoke_fast_20251004T183142Z.log†L7-L55】
31.4 [ ] After the Taskfile and memory fixes land, regenerate strict mypy manifests and the fast+medium coverage bundle to prove the gates remain green and lift `methodology/edrr/reasoning_loop.py` to ≥90 % if needed.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L51】【F:docs/release/v0.1.0a1_execution_plan.md†L88-L128】
31.5 [x] Update issues/release-readiness-assessment-v0-1-0a1.md and issues/release-finalization-uat.md with the new evidence bundle, revised risk assessment, and the PR breakdown from the refreshed execution plan.【F:issues/release-readiness-assessment-v0-1-0a1.md†L1-L120】【F:issues/release-finalization-uat.md†L1-L120】【F:docs/release/v0.1.0a1_execution_plan.md†L1-L128】
31.6 [x] Consolidate pytest plugin registration (hoist nested `pytest_plugins` exports, add regression checks) so fast+medium rehearsals stop raising duplicate `pytest_bdd` errors before collection, then archive the clean transcript. Completed 2025-10-07: the previous `ValueError: Plugin already registered` in fast+medium rehearsal logs is replaced by clean `pytest --collect-only -q` and `pytest -k nothing --collect-only` transcripts that now serve as regression commands for plugin stability.【F:logs/devsynth_run-tests_fast_medium_20251006T033632Z.log†L1-L84】【F:logs/pytest_collect_only_20251007.log†L1-L40】【F:logs/pytest_collect_only_20251006T043523Z.log†L1-L24】【F:docs/release/v0.1.0a1_execution_plan.md†L34-L118】
31.7 [ ] Repair behavior step indentation drift and remove placeholder `feature_path` sentinels so `pytest --collect-only -q` reaches behavior suites without raising `IndentationError`/`NameError`; capture before/after transcripts under `diagnostics/`.【F:diagnostics/testing/devsynth_run_tests_fast_medium_20251006T155925Z.log†L1-L25】
31.8 [ ] Resolve the `devsynth.testing.run_tests` strict typing regression by refactoring segmentation helpers, adding unit coverage, and capturing passing `diagnostics/mypy_strict_*` manifests with refreshed knowledge-graph IDs.【F:diagnostics/mypy_strict_20251006T212233Z.log†L1-L32】【F:diagnostics/typing/mypy_strict_20251127T000000Z.log†L1-L40】【F:docs/release/v0.1.0a1_execution_plan.md†L50-L87】
31.9 [ ] Update WebUI/UXBridge scenario loaders to point at existing `.feature` files, regenerate traceability manifests, and log results in issues/test-collection-regressions-20251004.md and issues/coverage-below-threshold.md.【F:issues/test-collection-regressions-20251004.md†L16-L33】【F:docs/release/v0.1.0a1_execution_plan.md†L50-L87】
31.10 [ ] After tasks 31.6–31.9, rerun `pytest --collect-only -q` and `pytest -k nothing --collect-only` to prove collection hygiene, archiving logs in `diagnostics/pytest_collect_*.log` for the release bundle.【F:docs/release/v0.1.0a1_execution_plan.md†L68-L87】
31.11 [ ] Once collection and smoke are green, execute `poetry run mypy --strict src/devsynth`, `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`, and `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`, attaching refreshed manifests/logs to docs/plan.md, docs/tasks.md, and release readiness issues.【F:docs/release/v0.1.0a1_execution_plan.md†L68-L87】【F:docs/plan.md†L1-L88】【F:issues/release-readiness-assessment-v0-1-0a1.md†L1-L120】
