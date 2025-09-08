# DevSynth 0.1.0a1 Test Readiness and Coverage Improvement Plan

Version: 2025-09-07
Owner: DevSynth Team (maintainers)
Status: Execution in progress; plan updated with new environment blocker (2025-09-08)

Executive summary
- Goal: Reach and sustain >90% coverage with a well‑functioning, reliable test suite across unit, integration, behavior, and property tests for the 0.1.0a1 release, with strict marker discipline and resource gating.
- Current state (evidence):
  - Test collection succeeds across a large suite (unit/integration/behavior/property).
  - Fast smoke/unit/integration/behavior profiles run successfully via the CLI.
  - Speed-marker discipline validated (0 violations).
  - Property tests (opt-in) reveal 2 failures; must be fixed before release to claim full readiness.
  - Diagnostics indicate environment/config gaps for non-test environments (doctor.txt) used by the app; tests succeed due to defaults and gating, but this requires documentation and guardrails.
  - Coverage report artifact (htmlcov) shows 20% from a prior run; targeted property-only run showed 8% and triggered coverage threshold failure. The global pytest.ini threshold is 90%, so any authoritative release run must aggregate full-suite coverage.

Commands executed (audit trail)
- poetry run pytest --collect-only -q → Collected successfully (very large suite).
- poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 → Success.
- poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1 → Success.
- poetry run devsynth run-tests --target behavior-tests --speed=fast --smoke --no-parallel --maxfail=1 → Success.
- poetry run devsynth run-tests --target integration-tests --speed=fast --smoke --no-parallel --maxfail=1 → Success.
- poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json → 0 issues, 0 violations.
- DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/ -q → 2 failing tests; coverage fail-under triggered (8% on this narrow subset).
- Environment: Python 3.12.x (pyproject constraint), Poetry 2.1.4; coverage artifacts present under htmlcov/ and coverage.json.

Environment snapshot and reproducibility (authoritative)
- Persist environment and toolchain details under diagnostics/ for reproducibility:
  - poetry run python -V | tee diagnostics/python_version.txt
  - poetry --version | tee diagnostics/poetry_version.txt
  - poetry run pip freeze | tee diagnostics/pip_freeze.txt
  - poetry run devsynth doctor | tee diagnostics/doctor_run.txt
  - date -u '+%Y-%m-%dT%H:%M:%SZ' | tee diagnostics/run_timestamp_utc.txt
- Capture test logs and reports deterministically:
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 2>&1 | tee test_reports/smoke_fast.log
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1 2>&1 | tee test_reports/unit_fast.log
  - poetry run devsynth run-tests --target behavior-tests --speed=fast --smoke --no-parallel --maxfail=1 2>&1 | tee test_reports/behavior_fast_smoke.log
  - poetry run devsynth run-tests --target integration-tests --speed=fast --smoke --no-parallel --maxfail=1 2>&1 | tee test_reports/integration_fast_smoke.log
- Maintainer guardrails (mandatory extras):
  - Ensure all extras are installed (we are providers, nothing is optional): poetry install --with dev --all-extras
  - If doctor surfaces missing optional backends, treat as non-blocking unless explicitly enabled via DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true.

Coverage aggregation (authoritative)
- Single-run approach (preferred for fail-under=90%):
  - poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report 2>&1 | tee test_reports/full_fast_medium.log
  - The above aggregates coverage across unit/integration/behavior according to the CLI target defaults.
- Segmented runs (if needed for memory/runtime) — ensure coverage combine:
  - poetry run devsynth run-tests --speed=fast --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_fast_1.log
  - poetry run devsynth run-tests --speed=medium --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_medium_1.log
  - poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json
  - Verify the combined threshold: poetry run pytest -q --maxfail=1 --no-header --no-summary --disable-warnings --cov-fail-under=90 -k "nonexistent_to_force_no_tests" || true
- Narrow subsets will not meet the global threshold; always use the single-run or segmented+combine approach above when asserting readiness.

Concrete remediation tasks (actionable specifics)
- Property tests (tests/property/test_requirements_consensus_properties.py):
  1) Hypothesis misuse of example() at definition time:
     - Replace any example() calls outside of @example decorators and @given usage.
     - Correct pattern:
       from hypothesis import given, example
       from hypothesis import strategies as st

       @pytest.mark.fast
       @pytest.mark.property
       @given(st.from_type(Requirement))
       @example(Requirement(id="FR-01", text="...", priority=1))
       def test_requirements_consensus_properties(req: Requirement) -> None:
           ...
  2) AttributeError: _DummyTeam lacks _improve_clarity:
     - Preferred: Adjust test to call a public API that invokes clarity improvement internally (e.g., team.improve_clarity(requirement)).
     - Alternative: Extend the Dummy test double to implement _improve_clarity with a no-op or minimal semantics in tests/helpers/dummies.py (or the appropriate test utility module), ensuring interface compatibility.
  - Re-run: DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/ -q 2>&1 | tee test_reports/property_tests.log
  - Success criteria: 0 failures; exactly one speed marker per function.
- run_tests_cmd coverage uplift (src/devsynth/application/cli/commands/run_tests_cmd.py): add unit tests to cover these branches/behaviors with clear test names:
  - test_smoke_mode_sets_pytest_autoload_off
  - test_no_parallel_maps_to_n0
  - test_inventory_mode_writes_file_and_exits
  - test_marker_anding_logic_builds_expression
  - test_segment_and_segment_size_batching
  - test_maxfail_propagates_to_pytest
  - test_feature_flags_map_to_env (DEVSYNTH_FEATURE_<NAME>)
  - test_provider_defaults_applied_when_unset
  - test_invalid_marker_expression_errors
  - test_nonexistent_target_exits_with_error
  - Ensure tests validate Typer exit codes and environment side effects without external network calls.

Critical evaluation of current tests (dialectical + Socratic)
1) Alignment with 0.1.0a1 requirements
- Pros: CLI run-tests paths validated by unit and behavior tests; marker discipline enforced; extensive test directories indicate breadth across subsystems (adapters, ingestion, metrics, CLI, UX bridge, etc.).
- Cons: Property tests failing; coverage artifacts indicate low coverage in at least some prior or partial runs; some modules like run_tests_cmd.py called out in diagnostics with ~15% coverage. Question: Are we measuring representative coverage across the full suite or only subsets? Answer: The 90% fail-under will fail if run against any narrow subset; we must aggregate coverage across appropriate targets.

2) Accuracy and usefulness of tests
- Pros: Behavior tests exercise CLI options (smoke mode, parallelism, feature flags). Unit tests validate environment variables and internal CLI invocation behavior. Marker verification ensures fast/medium/slow categorization discipline.
- Cons: Some modules likely under-tested (coverage hotspots); mocks may over-isolate critical logic, resulting in low coverage for real branches (e.g., Typer CLI option pathways). Property tests surface API inconsistencies (attribute missing on dummy) and misuse of Hypothesis strategies.

3) Efficacy and reliability
- Pros: Smoke mode limits plugin surface and is demonstrated to run cleanly. Resource gating and default provider stubbing prevent accidental external calls. Speed markers allow layered execution.
- Cons: The plan must guarantee a reproducible coverage workflow that meets 90% in maintainers’ environments; must ensure optional (for users) becomes mandatory for maintainers to prevent skips masking gaps.

4) Gaps and blockers identified
- Property tests: 2 failures observed in tests/property/test_requirements_consensus_properties.py
  - Hypothesis error: Using example() inside a strategy decorator context → test must be refactored to not call example() at definition time; use given/strategies only.
  - AttributeError: _DummyTeam lacks _improve_clarity → either the dummy must implement this method or tests need to call a public interface the dummy supports.
- Coverage hotspots: Historical diagnostics and htmlcov show low coverage in src/devsynth/application/cli/commands/run_tests_cmd.py (~14–15%), and other adapter-heavy modules show very low coverage in artifacts. Need targeted tests or broaden integration coverage.
- Environment/config: diagnostics/doctor.txt lists many missing env vars across environments; while tests pass due to default stubbing, release QA should include doctor sanity checks and documented defaults.
- Installation: `poetry install --with dev --all-extras` hangs repeatedly on `nvidia/__init__.py`, leaving the environment incomplete (see issues/poetry-install-nvidia-loop.md).
- Potential mismatch between pytest.ini fail-under=90 and how contributors run focused subsets; dev tooling must aggregate coverage or provide guidance on running complete profiles locally.

Standards and constraints reaffirmed
- Tests must have exactly one speed marker per function (verified by script; continue to enforce).
- For maintainers, “optional” dependencies are not optional: install with extras to run all tests.
- CI/CD is disabled until after 0.1.0a1; afterward, only low-throughput actions are allowed.
- Provider defaults for tests: offline=true, provider=stub, LM Studio unavailable by default.

Target state and success criteria
- Functional: All unit, integration, behavior, and property tests pass locally under documented commands; smoke profile remains green.
- Coverage: Combined coverage of src/devsynth >= 90% with pytest.ini enforced threshold; html report under test_reports/ and/or htmlcov/.
- Stability: Resource-gated tests deterministically skip unless explicitly enabled; no accidental network calls.
- Developer UX: Reproducible local commands; documented environment setup; marker discipline maintained.

Remediation plan to >90% coverage and full readiness
Phase 0: Environment and tooling (Day 0)
- Install deps with full extras for maintainers:
  poetry install --with dev --all-extras
  poetry shell
- Sanity commands:
  poetry run devsynth doctor
  poetry run pytest --collect-only -q
  poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Outcome: Ensure stable local environment; capture doctor.txt warnings as known non-blockers for tests (due to stubbing), but document default env in README/docs.

Phase 1: Property tests remediation (Day 0–1)
- Fix Hypothesis misuse:
  - Refactor tests/property/test_requirements_consensus_properties.py to remove example() invocation inside strategies; use @given with proper strategies; where concrete examples desired, parametrize separately or use @example decorators correctly.
- Fix _DummyTeam AttributeError:
  - Either implement _improve_clarity on the dummy test double consistent with expected interface, or adapt the test to use the public API that indirectly exercises clarity improvement.
- Re-run property tests:
  DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/ -q
- Acceptance: 0 failures; property tests additionally marked with a valid speed marker.

Phase 2: Coverage uplift (Day 1–3)
- Establish coverage baseline with full fast+medium (and targeted slow if feasible locally):
  poetry run devsynth run-tests --report --speed=fast --speed=medium --no-parallel
  Optionally, segment to reduce memory pressure:
  poetry run devsynth run-tests --speed=fast --speed=medium --segment --segment-size 100 --no-parallel --report
- Inspect coverage.json/htmlcov to identify modules <80% and <50%.
- Hotspot 1: run_tests_cmd.py
  - Add/extend unit tests to cover branches: smoke mode (PYTEST_DISABLE_PLUGIN_AUTOLOAD), --no-parallel maps to -n0, inventory mode writes file and exits, --marker ANDing logic, --segment/--segment-size batching, --maxfail propagation, feature flags env mapping, provider defaults application, error paths (invalid marker expression, non-existent target).
- Hotspot 2: adapters and stores
  - For pure-Python logic (e.g., deterministic serialization, simple transforms), add fast unit tests without requiring backends.
  - For backend integrations (TinyDB, DuckDB, ChromaDB, FAISS, Kuzu), add resource-gated tests behind `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` flags. Implement minimal smoke coverage for each backend:
    - TinyDB — set `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`; import TinyDB, insert a document, and read it back.
    - DuckDB — set `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true`; connect in memory, create a table, insert a row, and select it.
    - ChromaDB — set `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true`; start an ephemeral client, add a document with an embedding, and query by vector.
    - FAISS — set `DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true`; build an `IndexFlatL2`, add a vector, and perform a nearest-neighbor search.
    - Kuzu — set `DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true`; open a temporary database, create a node table, insert a record, and retrieve it.
- Hotspot 3: UX bridge and logging
  - Validate logging branches and user prompts in non-interactive mode; ensure CLIUXBridge basic flows have unit coverage.
- Iterate until combined coverage >=90% locally. Keep test order independence and isolation.

Phase 3: Behavior/integration completeness (Day 2–4)
- Ensure BDD behavior tests cover the documented run-tests CLI examples (unit fast no-parallel, report generation, smoke mode). Add scenarios for feature flags and segmented runs if missing.
- Integration ingestion and metrics: validate that key flows don’t require external services by default; expand fixtures to simulate inputs and verify metrics consistency.

Phase 4: Non-functional quality gates (Day 3–5)
- Linting/static analysis:
  poetry run black --check .
  poetry run isort --check-only .
  poetry run flake8 src/ tests/
  poetry run bandit -r src/devsynth -x tests
  poetry run safety check --full-report
- Typing (strict):
  poetry run mypy src/devsynth
  - Address strict failures or document temporary relaxations with TODOs and targeted pyproject overrides only where necessary.

Phase 5: Documentation and developer workflow (Day 4–5)
- Update docs/user_guides/cli_command_reference.md with any new CLI options or behavior clarifications discovered during testing.
- Document maintainer setup (all extras, resource flags) and how to selectively enable backend tests.
- Summarize environment defaults and provider stubbing behavior in README.md and docs.

Maintainer setup quickstart (resource-gated backends)
- Install with all extras for maintainers: `poetry install --with dev --all-extras`
- Enable specific backends locally by setting flags before running tests:
  - export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
  - export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true
  - export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
  - export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
  - export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
- Keep runs deterministic:
  - Prefer: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`
  - For smoke/stability: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel`
- Property tests are opt-in:
  - `export DEVSYNTH_PROPERTY_TESTING=true`
  - `poetry run pytest tests/property/ -q`

Phase 6: Release preparation and CI/CD strategy (post 0.1.0a1 cut)
- Keep GitHub Actions disabled until 0.1.0a1 is tagged.
- Afterward, enable low-throughput workflows:
  - on: workflow_dispatch and minimal on: push (main) with concurrency group (e.g., concurrency: { group: "devsynth-main", cancel-in-progress: true }).
  - Jobs:
    1) smoke (fast, --no-parallel, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1)
    2) unit+integration (fast+medium) without xdist for determinism
    3) typing+lint (mypy/flake8/black/isort/bandit/safety)
  - Nightly scheduled job for full suite with report upload (HTML coverage/artifacts).
  - Cache Poetry and .pytest_cache to reduce runtime:
    - actions/cache keys example:
      - key: poetry-cache-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
        path: ~/.cache/pypoetry
      - key: pip-cache-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
        path: ~/.cache/pip
      - key: pytest-cache-${{ runner.os }}-${{ github.sha }}
        path: .pytest_cache
  - Artifacts to upload on failures: test_reports/, htmlcov/, coverage.json, diagnostics/doctor_run.txt

Risks and mitigations
- Heavy optional backends on macOS/Windows: tests are resource-gated; document minimal smoke coverage and how to enable locally.
- Intermittent behavior due to plugins: smoke mode defaults to PYTEST_DISABLE_PLUGIN_AUTOLOAD.
- Coverage fluctuations for partial runs: standardize on devsynth run-tests with segmentation and aggregated coverage; provide a “coverage-only” profile.
- Strict mypy across actively changing modules: use temporary targeted relaxations with TODOs.

Issue tracker alignment (issues/ directory)
Issue tracker linkage protocol (how to cross-reference during planning)
- List open/local tickets and grep for readiness work:
  - ls -1 issues/ | tee diagnostics/issues_list.txt
  - grep -R "readiness\|coverage\|tests\|run-tests" -n issues/ | tee diagnostics/issues_grep_readiness.txt
- Cross-reference behavior features with issues mentioned in .feature files:
  - grep -R "Related issue:" -n tests/behavior/ | tee diagnostics/behavior_related_issues.txt
- When adding or updating tests, include the issue filename in docstrings (e.g., "ReqID: FR-09; Issue: issues/Critical-recommendations-follow-up.md").
- On each planning iteration, update this plan with any newly discovered blockers from issues/ and record them under Gaps and blockers identified.
- devsynth-run-tests-hangs.md: ensure smoke profile is default in docs for stability and add watchdog timeouts in behavior tests.
- reqid_traceability_gap.md: add behavior tests asserting presence of ReqID tags in docstrings for representative subsets; add a small tool to validate across tests.
- typing_relaxations_tracking.md: audit relaxations noted in this file and schedule their restoration within Phase 4.
- Resource/backend integration items (chromadb/kuzu/faiss/tinydb): provide togglable tests under requires_resource markers, with documentation in this plan.

Acceptance checklist
- [ ] All unit+integration+behavior tests pass locally with documented commands.
- [ ] Property tests pass under DEVSYNTH_PROPERTY_TESTING=true.
- [ ] Combined coverage >= 90% (pytest.ini enforced) with HTML report available.
- [ ] Lint, type, and security gates pass.
- [ ] Docs updated: maintainer setup, CLI reference, provider defaults, resource flags.
- [ ] Known environment warnings in doctor.txt triaged and documented; non-blocking for tests by default.

Maintainer quickstart (authoritative commands)
- Setup:
  poetry install --with dev --all-extras
  poetry run devsynth doctor
- Fast smoke sanity:
  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- Full fast+medium with HTML report:
  poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel
- Property tests (opt-in):
  DEVSYNTH_PROPERTY_TESTING=true poetry run pytest tests/property/
- Marker discipline check:
  poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Static analysis and typing:
  poetry run black --check . && poetry run isort --check-only . && poetry run flake8 src/ tests/ && poetry run mypy src/devsynth && poetry run bandit -r src/devsynth -x tests && poetry run safety check --full-report

Notes and next actions
- Immediate: Fix the two property test failures; add targeted tests for run_tests_cmd branches; re-generate coverage report and iterate on hotspots below 80% coverage.
- Short-term: Align docs with current CLI behaviors and ensure issues/ action items are traced to tests.
- Post-release: Introduce low-throughput GH Actions pipeline as specified and expand nightly coverage runs.
