# DevSynth 0.1.0a1 Test Improvement Plan (Evidence‑Grounded)

Last updated: 2025-09-05 11:09 local

Executive Summary
- Objective: Ensure all existing tests are functional and raise repository-wide coverage for src/devsynth to ≥90% ahead of 0.1.0a1 stabilization.
- Current status (evidence below):
  - Collection scale: ~4,136 items discovered.
  - Marker discipline: 0 violations across 988 files.
  - Smoke fast run: passes.
  - Unit fast run: fails on ValidationAgent behavior; additional warnings about unknown custom marks.
  - Coverage snapshot: ~20% overall (coverage.py HTML report), with notable low coverage in core CLI command run_tests_cmd.py (~14%) and multiple adapters/backends.
- Strategy: Fix high-signal failing tests and semantics first, then add high-leverage unit coverage on CLI/test harness/provider env/utilities, followed by adapter stubs and integration seams. Ratchet the coverage gate only after incremental wins; maintain speed/marker discipline, isolation, and offline defaults.

Evidence (commands and outcomes)
- Test discovery and scale:
  - poetry run pytest --collect-only -q | wc -l → 4136
- Speed marker verification:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json →
    info: files=988, cache_hits=988, cache_misses=0, issues=0, speed_violations=0, property_violations=0
- Smoke baseline:
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 → Tests completed successfully
- Unit fast baseline (first failure details):
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1 → FAIL
  - First failure: tests/unit/application/agents/test_validation_agent.py::test_process_returns_typed_output
    - Expected out["is_valid"] is True but got False.
- Coverage snapshot (HTML report present in repo):
  - htmlcov/index.html shows 20% overall (created at 2025-09-04 21:04 -0700)
  - run_tests_cmd.py shows 14% file coverage.
- Environment diagnostics:
  - poetry run devsynth doctor → reports missing provider/API env vars and config defaults, but these are gated/overridden in run-tests smoke/offline mode; not a blocker for unit tests.
  - Unit run warnings observed:
    - PytestUnknownMarkWarning for custom marks: smoke, unit. These marks are not registered in pytest.ini.
    - PytestConfigWarning: Unknown config option: anyio_backend (present in pytest.ini). This likely targets pytest-anyio but the project uses pytest-asyncio; migrate to pytest-asyncio's configuration (e.g., asyncio_mode=strict) or add pytest-anyio, otherwise remove the unknown option.

Corrections vs. earlier draft (current session):
- Marker verification files count corrected from 989 → 988.
- All empirical evidence in this section was re-run locally on 2025-09-05 ~10:35–10:40 local and recorded verbatim.
- Confirmed pytest.ini currently lacks registrations for custom marks 'smoke' and 'unit'; expect PytestUnknownMarkWarning where used unless registered or refactored.
- Confirmed pytest.ini sets anyio_backend=asyncio; this will emit PytestConfigWarning unless pytest-anyio is installed or configuration is migrated to pytest-asyncio (e.g., asyncio_mode=strict).
- Observed coverage gate (cov-fail-under=70) triggers failure during single-test runs; recommend documenting local override (e.g., -o addopts="") for focused iteration.
- Unit fast failure on ValidationAgent confirmed; first-failure location and assertion captured from test log.
- Coverage overview (20% overall) confirmed from htmlcov/index.html.

Critical Evaluation of Current Tests (Dialectical and Socratic)
1) Alignment vs. Guidelines
- Strengths:
  - Clear discipline on speed markers; automated verification has zero violations.
  - Test org matches the documented structure (unit/integration/behavior). BDD assets and CLI wrapper tests exist.
  - Offline/“stub provider” defaults in the run-tests CLI align with safe CI behavior.
- Gaps:
  - Coverage is very low (~20%) relative to the stated goal (90%). A large portion of src/devsynth is minimally exercised, especially CLI commands and adapters.
  - The default pytest.ini coverage gate is cov-fail-under=70. Given current coverage, full runs would fail on coverage even if tests pass; the smoke run “success” likely bypasses coverage or runs a subset.
  - At least one unit test (ValidationAgent.process) fails, indicating a semantic mismatch between test expectations and implementation.
  - Pytest warns about unknown custom marks (e.g., smoke, unit) that are not registered in pytest.ini. While non-fatal, warnings create noise and hinder triage.

2) Efficacy and Usefulness
- The suite is broad (4k+ items collected), and marker gating enables targeted local iterations. However, the breadth doesn’t translate into coverage; many code paths (adapters/backends/CLI commands) are not executed or are covered only through thin import smoke.
- Behavior/BDD coverage appears present, but if resource-marked or slow, it may be excluded from default coverage sampling.
- Diagnostics logs (mypy/flake8/bandit references in diagnostics/) flag issues in run_tests_cmd.py (unused type: ignore, unreachable code), hinting at dead branches and untested paths.

3) Release Readiness for 0.1.0a1
- A failing unit test (ValidationAgent) and 20% coverage are inconsistent with a release candidate. The run-tests CLI is a central entry point; its direct coverage (14%) is insufficient, risking regressions in test execution behaviors, env flagging, and segmentation.
- Configuration doctor finds missing env vars; the CLI’s offline provider defaults mitigate this for tests, but we must ensure unit/integration tests do not accidentally require live providers.

Root-Cause Hypotheses and Validation Steps
- Hypothesis A: ValidationAgent.process uses heuristics that don’t recognize “All checks passed; no failures detected.” as a success signal. Action: Inspect devsynth/application/agents/validation.py and adjust the parsing rules or the deterministic test stub to align with intended semantics (e.g., any message without “fail” tokens might be success; or explicit “PASS” token required). Add precise unit tests around the decision function.
- Hypothesis B: Low CLI coverage stems from relying primarily on behavior tests and not exercising option-matrix branches (smoke, parallel, report, segmentation, marker combination, feature flags). Action: Add unit tests that inject a dummy bridge and mock run_tests/collect_tests_with_cache to validate env controls and argument construction without executing pytest.
- Hypothesis C: Adapters/backends have minimal unit seams; tests either avoid them or require heavy extras/resources, leaving large files uncovered. Action: Introduce seam tests using fakes and feature flags; mark resource tests properly and keep default skips.

Plan to Achieve ≥90% Coverage and Full Test Functionality
Phase 0: Sanity, Noise Reduction, and Failing Test Fix (Week 0)
- Fix ValidationAgent.process semantics to satisfy tests/unit/application/agents/test_validation_agent.py::test_process_returns_typed_output. Add unit tests for any private helper that computes is_valid from text.
- Register auxiliary markers seen in the suite (e.g., smoke) in pytest.ini to remove PytestUnknownMarkWarning. Alternatively, refactor tests to standard speed/resource markers and remove extraneous custom marks. Choose one path and apply consistently.
- Ensure run-tests smoke/offline defaults are enforced in unit tests to avoid accidental provider calls (verify ProviderEnv and run-tests env toggles are covered by tests).

Phase 1: High-Leverage Coverage (Week 1)
- CLI Test Runner (src/devsynth/application/cli/commands/run_tests_cmd.py):
  - Add unit tests covering:
    - --smoke: sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and disables xdist.
    - --no-parallel: ensures -n auto is not used.
    - --speed: combinations (fast, medium, slow) and marker expression merging via -m.
    - --report: produces pytest-html args and ensures test_reports/ path is passed.
    - --segment/--segment-size: slices collected tests into batches (mock collect_tests_with_cache to return synthetic ids; assert batched pytest invocations).
    - --maxfail: passthrough to pytest.
    - --feature name[=true|false]: environment mapping to DEVSYNTH_FEATURE_<NAME> vars.
  - Mock increment_counter to validate observability increments.
  - Mock UX bridge to assert user-facing messages aren’t error-prone.
  - Target: raise file coverage from 14% → ≥90%.
- Testing Harness (src/devsynth/testing/run_tests.py):
  - Add unit tests for argument translation to pytest and result code handling.
  - Validate collection caching behavior determinism and sanitize node id helpers.
- Provider Env (src/devsynth/config/provider_env.py):
  - Tests ensuring stub provider defaults with missing keys; env var precedence; safety toggles; error paths for explicit providers without keys.
- Utils/Serialization/Logging:
  - Increase coverage by targeting pure functions and deterministic utilities with property-based tests (opt-in via DEVSYNTH_PROPERTY_TESTING) plus standard unit tests.

Phase 2: Adapter/Backend Seams and Domain (Week 2)
- For heavy adapters (chromadb/faiss/kuzu/etc.), add seam-level tests that:
  - Skip by default using @pytest.mark.requires_resource("<name>") but include lightweight fakes for default CI path to still exercise adapters’ control flow and error handling (e.g., missing resource raises friendly error or returns stubbed noop).
  - Cover serialization, mapping, and error branches without spinning real backends.
- Domain model and agents:
  - Add targeted tests for agent adapters, multi-agent coordinator consensus logic, error branches in safety audit tool, and validation/test scaffolding agents beyond the single happy path.

Phase 3: Behavior and Integration Reinforcement (Week 3)
- Ensure at least smoke-level BDD flows run under CI’s default filter (fast). Provide fake providers and fixtures.
- Add behavior tests for CLI command groups missing coverage (e.g., diagnostics, config update flows).
- Where integration depends on optional extras, ensure resource markers and extras are aligned; provide a minimal CI profile with a chosen subset (e.g., tests + retrieval) and appropriate DEVSYNTH_RESOURCE_* flags.

Phase 4: Ratchet and Sustain (Week 4)
- Once overall coverage ≥85% in CI consistently, raise cov-fail-under to 85 in pytest.ini; after meeting ≥90% for two consecutive main-branch runs, raise cov-fail-under to 90.
- Add a coverage “must not regress” job comparing coverage.json between main and PR (scripts/ can include a simple comparator). Gate merges if drop > 1%.
- Keep speed marker verifier in CI as a required check; add a check to fail on PytestUnknownMarkWarning.

Prioritized Fix List (Top 10)
1) Fix ValidationAgent.process semantics and add unit tests around decision logic.
2) Expand run_tests_cmd.py unit coverage (env toggles, segmentation, marker merge, feature flags).
3) Add tests for testing/run_tests matrix (args translation, result handling).
4) ProviderEnv tests for offline/stub behavior and safe defaults.
5) Register or remove extraneous custom marks to silence warnings.
6) Add adapter seam tests with fakes for ChromaDB/FAISS, focusing on error handling and simple paths.
7) Increase coverage on utils (serialization, file helpers); add property tests gated by DEVSYNTH_PROPERTY_TESTING.
8) Add behavior tests for CLI diagnostics/config flows.
9) Fix mypy errors and remove unused type: ignore and unreachable code paths mentioned in diagnostics.
10) Establish CI coverage ratchet and regression guard.

Coverage Projection and Milestones
- Baseline: 20% overall.
- After Phase 1: 55–65% (CLI + harness + provider + utils).
- After Phase 2: 75–82% (adapter seams + domain/agents core paths).
- After Phase 3: 88–92% (behavior/integration reinforcement).
- Final Ratchet: Set cov-fail-under=90 once sustained; allow temporary soft window (±1%) via regression guard.

Quality Gates and Commands (to be automated in CI)
- Collection sanity:
  - poetry run pytest --collect-only -q
- Marker discipline:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Fast smoke:
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- Unit (fast, segmented to isolate flakes):
  - poetry run devsynth run-tests --target unit-tests --speed=fast --segment --segment-size=50 --maxfail=1
- Coverage report:
  - poetry run pytest -q --cov=src/devsynth --cov-report=term-missing --cov-report=html
- Typing/lint/security:
  - poetry run mypy src/devsynth
  - poetry run flake8 src/ tests/
  - poetry run bandit -r src/devsynth -x tests
  - poetry run safety check --full-report

Risk Analysis and Mitigations
- Flaky tests under parallelism (xdist): default to no-parallel in smoke; segment large suites.
- Optional backend drift: gate with resource flags; maintain fakes and make real backend tests opt-in via extras.
- Coverage gaming risk: focus on meaningful branches (error paths, env toggles) rather than trivial lines; review PRs for test quality.
- Time risk to 90%: staged ratcheting with weekly milestones; visible HTML reports committed to artifacts (test_reports/).

Owner and Accountability Model
- CLI/test harness & provider env: Testing Working Group A (TWG-A)
- Adapters/backends seam tests: TWG-B
- Agents/domain: TWG-C
- CI and quality gates: Release Engineering
(Note: Replace placeholders with actual names in your team mapping.)

PR Sequencing and Milestones (Release 0.1.0a1)
- Sequence: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 (ratchet). Each phase lands as one or more small PRs per module to keep diffs reviewable.
- Milestones and target dates (tentative, adjust in tracker):
  - M1 (Week 0): Phase 0 fixes merged; unit-fast baseline green; warnings eliminated. Owners: TWG-A. Evidence: passing unit-fast and smoke runs.
  - M2 (Week 1): Phase 1 coverage uplift (CLI/harness/provider env/utils) to ≥55–65% overall; file-level targets ≥90% for run_tests_cmd.py and testing/run_tests.py. Owners: TWG-A. Evidence: htmlcov artifact, reports.
  - M3 (Week 2): Phase 2 adapter/backends seam tests using fakes; resource-gated tests in place. Owners: TWG-B. Evidence: default CI skips heavy tests; gated runs pass when enabled.
  - M4 (Week 3): Phase 3 behavior/integration reinforcement; smoke BDD green by default. Owners: TWG-C. Evidence: behavior-tests fast/smoke job green.
  - M5 (Week 4): Phase 4 ratchet to ≥85% coverage gate, followed by ≥90% after two consecutive ≥90% runs on main; coverage regression guard enforced. Owners: Release Engineering.
- Tracking: Create milestones in issue tracker for M1–M5; link tasks from docs/tasks.md to issues/PRs; record evidence links (artifacts) in each milestone description.

Appendix: Referenced Files and Notable Coverage Gaps
- src/devsynth/application/cli/commands/run_tests_cmd.py → 14%
- src/devsynth/adapters/chromadb_memory_store.py → ~14% (280 statements, 241 missing)
- Multiple src/devsynth/application/cli/commands/*.py modules with sub-50% coverage
- Diagnostics mention mypy strict issues in run_tests_cmd.py (unused ignore, unreachable)

Appendix: Immediate Fix Details for ValidationAgent (guidance)
- If process() currently computes is_valid from raw text, implement a simple, deterministic rule set for test predictability:
  - If the generated report contains any of: "fail", "error", "exception" (case-insensitive) → is_valid=False
  - Else → is_valid=True
- Add tests covering affirmative phrasing ("All checks passed"), neutral phrasing, and explicit failure tokens.
- Ensure create_wsde returns a minimally valid structure for downstream consumers; test for dict shape and types (already partially covered).

How to Use This Plan
- Implement Phase 0 immediately to turn red to green and remove noise.
- Track progress via:
  - htmlcov/index.html for coverage trend
  - test_reports/ for HTML test reports
  - test_markers_report.json for marker discipline
- Ratchet coverage gate only after sustained improvements to avoid blocking parallel work prematurely.


Session Validation Log (Current Session: 2025-09-05 11:09 local)
- Collection: poetry run pytest --collect-only -q | wc -l → 4136
- Marker verification: poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json → [info] verify_test_markers: files=988, cache_hits=988, cache_misses=0, issues=0, speed_violations=0, property_violations=0
- Smoke baseline: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 → Tests completed successfully
- Unit fast baseline: poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1 → Pytest exited with code 1; tests failed
- Focused failing test: poetry run pytest -q tests/unit/application/agents/test_validation_agent.py::test_process_returns_typed_output → FAILED with assertion: expected out["is_valid"] True, got False ("assert False is True"). Note: coverage gate enforced by pytest.ini (cov-fail-under=70) also triggers coverage failure when running a single test; this is orthogonal to the functional assertion failure.
- pytest.ini observations: anyio_backend = asyncio present. Custom marks 'smoke' and 'unit' are not registered; expect PytestUnknownMarkWarning unless tests avoid using them. Default addopts includes coverage and marker filter -m "not slow and not gui".
- devsynth doctor: diagnostics/doctor.txt lists missing provider env vars and schema defaults; consistent with offline/stub mitigations in run-tests CLI.

Debugging tip: For local focused runs bypassing the coverage gate, use one of:
- poetry run pytest <path>::<test> -q -o addopts=""
- PYTEST_ADDOPTS="" poetry run pytest <path>::<test>
Or use devsynth run-tests --smoke to reduce plugin surface during debugging.

Alignment verdict: The plan’s evidence and recommendations are consistent with this session’s empirical data. Additions above clarify the coverage gate side-effect on single-test iterations and confirm pytest.ini marker registration gaps.


Addendum: Coverage Corroboration (2025-09-05 11:12 local)
- Coverage HTML opened at htmlcov/index.html shows overall 20% coverage, created at 2025-09-04 21:04 -0700, corroborating the plan’s stated snapshot.
