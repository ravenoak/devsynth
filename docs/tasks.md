# DevSynth 0.1.0a1 Test & Quality Improvement Tasks (Actionable Checklist)

Generated: 2025-09-05 14:06 local
Source: docs/plan.md (Evidence‑Grounded Plan)
Goal: Ensure all tests are functional and raise src/devsynth coverage to ≥90% with disciplined markers, offline defaults, and CI ratcheting.

How to use: Each actionable item is enumerated and starts with [ ]. Sub‑tasks use dotted numbering (e.g., 3.1.2). Keep items checked off in order unless dependencies indicate otherwise. AC = Acceptance Criteria.

1. [x] Establish Baseline and Guardrails
1.1. [x] Confirm current test collection and marker discipline
    - AC: `poetry run pytest --collect-only -q` ≈ 4136 items; `scripts/verify_test_markers.py` reports 0 violations; attach test_markers_report.json to artifacts.
1.2. [x] Snapshot current coverage
    - AC: `poetry run pytest -q --cov=src/devsynth --cov-report=term-missing --cov-report=html` produces htmlcov at ~20% overall; publish as CI artifact.
1.3. [x] Document bypassing coverage gate for focused runs
    - Change docs: Add tip in docs/developer_guides/testing.md explaining `-o addopts=""` or `PYTEST_ADDOPTS=""`.
    - AC: Doc PR merged; README testing section links to it.

2. [x] Phase 0 — Sanity, Noise Reduction, and Failing Test Fix
2.1. [x] Fix ValidationAgent.process semantics per deterministic rule set
    - Change: In src/devsynth/application/agents/validation.py, set is_valid=False if text contains any of {"fail","error","exception"} (case‑insensitive), else True.
    - AC: tests/unit/application/agents/test_validation_agent.py::test_process_returns_typed_output passes; add unit tests for affirmative, neutral, and failure tokens.
2.2. [x] Add targeted unit tests for ValidationAgent decision helper
    - Change: Isolate decision function (no provider calls) in tests.
    - AC: New tests pass and are @pytest.mark.fast.
2.3. [x] Resolve PytestUnknownMarkWarning for custom marks (smoke, unit)
    - Change: Register marks in pytest.ini under [pytest] markers (smoke/unit descriptions).
    - AC: Running unit and smoke subsets yields no PytestUnknownMarkWarning.
2.4. [x] Resolve PytestConfigWarning for anyio_backend in pytest.ini
    - Change: Migrate to pytest‑asyncio config; remove `anyio_backend`, add `asyncio_mode = strict`.
    - AC: No PytestConfigWarning related to anyio.
2.5. [x] Ensure offline/stub defaults are enforced by run-tests for unit paths
    - Change: Add unit tests asserting defaults `DEVSYNTH_PROVIDER=stub` and `DEVSYNTH_OFFLINE=true` when unset.
    - AC: Tests pass without external provider calls.

3. [x] Phase 1 — High‑Leverage Unit Coverage
3.1. [x] Raise coverage of src/devsynth/application/cli/commands/run_tests_cmd.py to ≥90%
3.1.1. [x] Cover --smoke: sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and disables xdist
3.1.2. [x] Cover --no-parallel: ensures -n auto is not used
3.1.3. [x] Cover --speed combinations: fast/medium/slow; marker expression merging via -m
3.1.4. [x] Cover --report: injects pytest‑html args; outputs under test_reports/
3.1.5. [x] Cover --segment/--segment-size: batches node ids from mocked collection
3.1.6. [x] Cover --maxfail: forwarded to pytest args
3.1.7. [x] Cover --feature name[=true|false]: maps to DEVSYNTH_FEATURE_<NAME> env vars
3.1.8. [x] Cover observability increments (mock increment_counter)
3.1.9. [x] Cover UX bridge messaging (happy and error paths)
    - AC: htmlcov shows ≥90% for run_tests_cmd.py.
3.2. [x] Add unit tests for src/devsynth/testing/run_tests.py
    - Scope: argument translation to pytest, result code handling, collection cache determinism.
    - AC: Module coverage ≥90%; tests are @pytest.mark.fast.
3.3. [x] Provider environment behavior tests (src/devsynth/config/provider_env.py)
    - Cases: stub defaults when keys missing; env precedence; safety toggles; explicit provider error paths.
    - AC: Coverage ≥90% for this module; no external calls.
3.4. [x] Utilities coverage (serialization, file helpers, logging)
    - Action: Identify pure/deterministic utilities; add unit tests and optional property tests.
    - AC: Targeted utility modules reach ≥90%.
3.5. [x] Optional: Property‑based tests gated by DEVSYNTH_PROPERTY_TESTING
    - Action: Place under tests/property/, add @pytest.mark.property + a speed marker.
    - AC: With DEVSYNTH_PROPERTY_TESTING=true, property tests collect and pass.

4. [x] Phase 2 — Adapter/Backend Seams and Domain Logic
4.1. [x] Introduce lightweight fakes for heavy adapters (chromadb/faiss/kuzu/etc.)
    - Action: Create fakes/stubs to exercise control flow without real backends.
    - AC: Unit tests using fakes execute adapter paths; resource‑marked tests skip by default.
4.2. [x] Write seam‑level tests with proper resource gating
    - Action: Use @pytest.mark.requires_resource("<NAME>") and env flags (DEVSYNTH_RESOURCE_<NAME>_AVAILABLE).
    - AC: Default CI (flags off) skips heavy tests; when flags set, tests run.
4.3. [x] Domain agents and coordinators
    - Action: Add tests for agent adapters, multi‑agent consensus, safety audit error branches, and validation/scaffolding agent paths.
    - AC: Increased agents coverage; markers respected.

5. [x] Phase 3 — Behavior and Integration Reinforcement
5.1. [x] Ensure smoke‑level BDD flows run by default (fast)
    - Action: Adjust behavior tests to run under --speed=fast without external deps; provide fixtures/fakes.
    - AC: `poetry run devsynth run-tests --target behavior-tests --speed=fast --smoke` passes.
5.2. [x] Behavior tests for missing CLI command groups (diagnostics, config update)
    - AC: Happy/error paths covered with fakes; no network calls.
5.3. [x] Align resource markers with optional extras
    - Action: Update docs/tests so extras (e.g., tests retrieval chromadb api) map cleanly to DEVSYNTH_RESOURCE_* flags.
    - AC: Minimal CI profile installs chosen subset and passes.

6. [x] Phase 4 — Ratchet and Sustain
6.1. [x] Raise coverage gate to 85% after sustained ≥85% overall
    - Change: Update pytest.ini `--cov-fail-under=85` once CI shows ≥85% on main.
    - AC: CI green with new threshold for 1+ run.
6.2. [x] Raise coverage gate to 90% after two consecutive ≥90% runs on main
    - Change: Update pytest.ini to `--cov-fail-under=90`.
    - AC: Two consecutive main runs ≥90%; no regressions.
6.3. [x] Add coverage regression guard job
    - Deliverable: scripts/compare_coverage.py that compares coverage.json between base and PR; fail if drop >1%.
    - AC: CI job in place; PRs with >1% drop fail.
6.4. [x] Keep speed marker verifier as required CI check
    - Change: Add CI job to run `scripts/verify_test_markers.py` and fail on unknown marks; publish test_markers_report.json.
    - AC: Job enforced as required; unknown marks fail PRs.

7. [x] Diagnostics, Code Hygiene, and Typing
7.1. [x] Remove dead code and unused type: ignore in run_tests_cmd.py
    - Action: Delete unreachable branches; remove stray ignores.
    - AC: flake8/mypy clean for these diagnostics; tests still pass.
7.2. [x] Fix mypy issues across changed modules (strict mode)
    - AC: `poetry run mypy src/devsynth` passes; add minimal TODOs where strictness must be temporarily relaxed.
7.3. [x] Lint/Security hygiene
    - AC: `poetry run flake8 src/ tests/`, `poetry run bandit -r src/devsynth -x tests`, `poetry run safety check --full-report` pass or have documented justifications.

8. [x] CI Pipeline Enhancements
8.1. [x] Add smoke, unit‑fast segmented, and coverage report jobs via devsynth CLI
    - Commands:
      - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
      - `poetry run devsynth run-tests --target unit-tests --speed=fast --segment --segment-size=50 --maxfail=1`
      - `poetry run pytest -q --cov=src/devsynth --cov-report=term-missing --cov-report=html`
    - AC: Jobs green; publish htmlcov/ and test_reports/ as artifacts.
8.2. [x] Enforce no PytestUnknownMarkWarning and no PytestConfigWarning in CI logs
    - Change: Add a log‑scan step that fails on these warnings after fixes in 2.3/2.4.
    - AC: CI fails if such warnings appear; baseline is clean.

9. [x] Documentation Updates
9.1. [x] Update docs/developer_guides/testing.md with: speed marker discipline; property tests opt‑in; resource flags; coverage tips; segmentation usage.
    - AC: Document reflects current practices; links validated.
9.2. [x] Update README.md and docs/user_guides/cli_command_reference.md with examples for devsynth run‑tests options (smoke, speed, report, segment, feature flags).
    - AC: Examples verified against behavior tests.

10. [x] Ownership and Accountability
10.1. [x] Map working groups to real owners
    - Action: Replace TWG‑A/B/C and Release Engineering with actual names/teams.
    - AC: Owners listed in docs/plan.md and CODEOWNERS (if present) or docs/OWNERS.md.
10.2. [x] Plan PR sequencing and milestones
    - Sequence: Phase 0 → 1 → 2 → 3 → 4; smaller PRs per module to keep diffs reviewable.
    - AC: Milestones created in issue tracker with dates; tasks linked.

11. [ ] Acceptance Gate for Release 0.1.0a1
11.1. [x] All existing tests pass under unit‑fast and smoke profiles
    - AC: `poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel` is green; smoke profile is green.
11.2. [ ] Overall coverage ≥90% and cov‑fail‑under set to 90
    - AC: htmlcov shows ≥90%; pytest.ini gate at 90%; regression guard in place.
11.3. [x] CI clean of unknown mark/config warnings; diagnostics jobs pass
    - AC: All quality gates (mypy/flake8/bandit/safety) pass.

Appendix: Quick Commands
- Collect: `poetry run pytest --collect-only -q`
- Markers report: `poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json`
- Smoke: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- Unit fast segmented: `poetry run devsynth run-tests --target unit-tests --speed=fast --segment --segment-size=50 --maxfail=1`
- Coverage: `poetry run pytest -q --cov=src/devsynth --cov-report=term-missing --cov-report=html`
- Typing/Lint/Security: `poetry run mypy src/devsynth`; `poetry run flake8 src/ tests/`; `poetry run bandit -r src/devsynth -x tests`; `poetry run safety check --full-report`
