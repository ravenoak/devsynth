# DevSynth 0.1.0a1 Testing Readiness and Improvement Plan

Last updated: 2025-08-29
Owner: Core maintainers (release captain: TBD)
Status: Draft for immediate execution (nothing optional for maintainers)

Overview
- Purpose: Critically evaluate the current testing status and provide a concrete, multi‑disciplinary remediation plan to ensure all tests (unit, integration, behavior/BDD, provider integrations including OpenAI and LM Studio) are functional for the 0.1.0a1 release.
- Constraints: CI/CD is disabled until after 0.1.0a1; thereafter, only low‑throughput GitHub Actions. All validation must be runnable locally and reproducible with scripts.
- Method: Dialectical and Socratic reasoning: challenge assumptions, test offline-first defaults, and stress critical paths (CLI, provider abstraction, docs alignment, and marker discipline).

Executive Summary
- Strengths
  - Robust run-tests CLI (src/devsynth/application/cli/commands/run_tests_cmd.py) with smoke mode, segmenting, inventory export, feature flags, and marker-aware collection via devsynth.testing.run_tests.
  - Clear testing documentation (tests/README.md) with resource gating, local enablement, and helper scripts/Taskfile targets for sanity and marker discipline.
  - Conservative defaults for providers (stub + offline) and LM Studio resource disabled by default; OpenAI key set to test value in test fixtures.
- Gaps/Blockers
  - Missing master improvement plan (this document was previously empty).
  - Risk of speed marker drift; need verified reports and fixer scripts in routine workflow.
  - Integration tests for OpenAI and LM Studio must be validated under explicit enablement; ensure provider env and endpoints are honored and that tests skip gracefully otherwise.
  - Behavior tests rely on pytest-bdd and plugin surface; must confirm smoke workflows are functional and documented.
  - Need explicit end-to-end “evidence pack” artifacts for release sign-off with commands and outputs stored under test_reports/.
  - CI is off; we must provide local scripts to emulate minimum CI checks in a throttled manner post-release.

Testing Philosophy and Reasoning Approach
- Dialectical: For every assumption (e.g., offline defaults suffice), construct a counterexample (e.g., behavior test importing provider modules triggers network). Resolve by verifying isolation fixtures and explicit env guards.
- Socratic: Ask, “If a new contributor follows docs, what will fail first?” Ensure sanity scripts catch missing extras, plugin autoload conflicts, or resource markers.
- Multi-discipline: Combine software testing principles (determinism, hermeticity), ops pragmatism (resource gating, retries avoided in test), and documentation UX (copy-paste runnable commands).

Section 1 — Immediate Sanity and Inventory
1. Environment setup (minimal but sufficient for tests; GPU optional):
   - poetry install --with dev --extras "tests retrieval chromadb api"
   - poetry shell
2. Sanity: quick collection and smoke run.
   - poetry run pytest --collect-only -q | tee test_reports/collect_only_output.txt
   - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
3. Inventory: export test coverage by target/speed to JSON.
   - poetry run devsynth run-tests --inventory
Expected outcomes:
- No import errors, plugin conflicts, or hanging behavior.
- Inventory saved to test_reports/test_inventory.json.
If failures occur:
- Re-run with smoke mode explicitly: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- Use scripts/diagnostics.sh to capture environment and plugin list.

Section 2 — Speed Marker Discipline
1. Verification report and changed-only fast check:
   - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
   - poetry run python scripts/verify_test_markers.py --changed
2. If violations found:
   - poetry run python scripts/fix_missing_markers.py --paths tests/
   - poetry run python scripts/fix_duplicate_markers.py --paths tests/
   - Re-run changed check.
Outcomes:
- test_markers_report.json updated and committed.
- Exactly one speed marker per test function guaranteed.

Section 3 — Resource-Gated Integrations
Goal: Ensure opt-in integrations function and skip correctly when unavailable.
A. LM Studio
- Pre-reqs: poetry install --with dev --extras "memory llm"
- Enable locally:
  - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  - export LM_STUDIO_ENDPOINT=${LM_STUDIO_ENDPOINT:-http://127.0.0.1:1234}
- Run subset:
  - poetry run devsynth run-tests --speed=fast -m "requires_resource('lmstudio') and not slow"
- Validate: tests should reach the provider without hanging; failures should be actionable (model missing vs HTTP 404).
B. OpenAI
- Pre-reqs: poetry install --with dev --extras llm
- Enable locally with real API key:
  - export DEVSYNTH_PROVIDER=openai
  - export OPENAI_API_KEY=your-key
  - export OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
- Run subset:
  - poetry run devsynth run-tests --speed=fast -m "requires_resource('openai') and not slow"
- Validate: Calls execute or are stubbed by tests as intended; ensure no network calls occur when provider remains stub.
C. Defaults and safeguards
- Confirm that without the above flags, resource tests skip and fast suite remains hermetic.
- Confirm that run_tests_cmd._configure_optional_providers sets offline/stub defaults and LM Studio availability=false by default.

Section 4 — Behavior/BDD Tests
- Ensure pytest-bdd installed via dev extras.
- Run behavior tests in smoke and normal fast modes:
  - poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel
  - poetry run devsynth run-tests --smoke --target behavior-tests --speed=fast
- If any scenario imports optional providers, ensure they are guarded by resource markers or fixtures and skip when not enabled.

Section 5 — Integration Tests (Non-provider)
- Run core integrations that do not require external resources with fast/medium:
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel
  - poetry run devsynth run-tests --target integration-tests --speed=medium --no-parallel --maxfail=1
- If xdist issues appear, document in diagnostics and prefer serial runs for release gate.

Section 6 — Documentation and CLI Alignment
- Cross-check docs/user_guides/cli_command_reference.md and tests/README.md examples against actual CLI behavior. Validate options:
  - --no-parallel, --report, --smoke, --segment/--segment-size, --maxfail, --feature
- Generate HTML report to confirm path and artifact location:
  - poetry run devsynth run-tests --report --speed=fast
- Confirm inventory export documented:
  - poetry run devsynth run-tests --inventory
- If deviations are found, fix docs or run_tests_cmd messages accordingly.

Section 7 — Evidence Pack Artifacts (commit under test_reports/)
- Sanity outputs: collect_only_output.txt
- Inventory: test_inventory.json
- Marker discipline: test_markers_report.json
- Smoke plugin notice (if scripts provide it): smoke_plugin_notice.txt
- HTML report (if generated): test_reports/html/index.html (location per pytest-html config)
- Diagnostics: diagnostics/*.txt (if scripts used)
These artifacts support manual release judgment in absence of CI.

Section 7b — Code Quality and Typing Gates
- Objective: All code and tests conform to repository standards; zero mypy errors; formatting and linting pass; security checks clean.
- Commands (run via Poetry):
  - Formatting:
    - poetry run black . --check || poetry run black .
    - poetry run isort . --check-only || poetry run isort .
  - Lint and static analysis:
    - poetry run flake8 src/ tests/
    - poetry run mypy src/devsynth  # strict per pyproject; investigate and fix all errors
  - Security and hygiene:
    - poetry run bandit -r src/devsynth -x tests
    - poetry run safety check --full-report
- Remediation workflow:
  1) For mypy errors: tighten types, add precise annotations, and only relax with targeted per-module overrides with TODO to restore strictness (avoid broad ignores). Prefer refactors over type: ignore.
  2) For flake8: align with Black; fix complexity and unused imports; update isort sections per Black profile.
  3) For bandit/safety issues: prefer dependency upgrades or code fixes; document accepted risk with justification if unavoidable.
- Evidence artifacts to commit under test_reports/quality/:
  - black_report.txt, isort_report.txt, flake8_report.txt, mypy_report.txt, bandit_report.txt, safety_report.txt
  - Capture by tee, e.g., poetry run mypy src/devsynth | tee test_reports/quality/mypy_report.txt

Section 7c — Issues Audit and Dialectical Re-evaluation
- Audit in-repo issues (issues/ directory) and align them with this plan:
  - For each open issue relevant to 0.1.0a1, add an action item or explicitly defer with rationale.
  - Cross-check tests that claim to cover the issue; add/adjust tests if gaps exist.
- Re-evaluation loop (Socratic prompts):
  - What fails when a fresh contributor follows docs? Re-run Section 1 with a clean virtualenv; capture failures.
  - Are provider tests hermetic by default? Verify skips without flags; verify real calls when enabled.
  - Are behavior tests stable in smoke mode? If not, identify offending plugins and gate them.
- Update this plan with new findings; iterate until all Release Gate Criteria are met.

Section 7d — Manual Sign-off Checklist (Everything Green)
- All tests pass in the following lanes:
  - Smoke fast: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  - Unit fast+medium: poetry run devsynth run-tests --target unit-tests --speed=fast --speed=medium --no-parallel
  - Integration fast+medium (non-provider): poetry run devsynth run-tests --target integration-tests --speed=fast --speed=medium --no-parallel
  - Behavior fast (normal and smoke): poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel and with --smoke
  - Provider subsets when explicitly enabled: LM Studio and OpenAI per Section 3
- Quality gates all clean: black, isort, flake8, mypy, bandit, safety
- Evidence pack committed under test_reports/ and test_reports/quality/
- CHANGELOG.md updated to reference evidence pack
- Pre-commit hooks installed and passing locally: pre-commit install; pre-commit run -a

Section 8 — Known Risks and Mitigations
- Plugin interference: Use smoke mode and PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 in scripts.
- Network leakage: Ensure ProviderEnv.with_test_defaults enforces DEVSYNTH_OFFLINE=true and DEVSYNTH_PROVIDER=stub unless explicitly overridden.
- Flaky tests: Prefer isolating via timeouts (DEVSYNTH_TEST_TIMEOUT_SECONDS set by CLI for smoke and fast runs). Avoid retries in tests.
- Resource assumptions: Behavior tests must never assume providers are available unless marked and explicitly enabled.

Section 9 — Post‑Release Low‑Throughput CI Plan
- After 0.1.0a1, enable a minimal GitHub Actions workflow that runs:
  - poetry install --with dev --extras "tests retrieval chromadb api"
  - poetry run pytest --collect-only -q
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  - poetry run python scripts/verify_test_markers.py --changed
- Nightly optional lanes (manual dispatch): LM Studio and OpenAI subsets as documented in Section 3; capture artifacts but limited concurrency.

Section 10 — Action Items and Ownership
1. Run Section 1–7 commands now and commit artifacts (All maintainers).
2. Fix any speed marker violations (Testing lead).
3. Validate LM Studio and OpenAI local runs and document exact prerequisites (Provider owners).
4. Reconcile any doc/CLI discrepancies discovered (Docs + CLI owner).
5. Prepare minimal GA workflow for post‑release (Release captain).

Appendix — Observations from Code Review
- run_tests_cmd.py:
  - Enforces allowed targets and speeds; smoke mode sets timeouts and disables xdist/cov; feature flags mapped to DEVSYNTH_FEATURE_<NAME> env; inventory export implemented and writes to test_reports/test_inventory.json.
  - _configure_optional_providers(): sets LM Studio unavailable by default and applies ProviderEnv.with_test_defaults() (offline, stub) to environment.
- tests/README.md:
  - Provides consistent instructions that match the CLI and extras; includes resource enabling patterns and scripts references.
- Scripts and Taskfile (as referenced in docs/tests):
  - Use them to produce evidence pack; ensure Task is optional; fallback bash scripts exist.

Release Gate Criteria (for 0.1.0a1)
- Sanity pass: collection completes; fast smoke lane passes with no failures.
- Marker discipline: report exists; no violations.
- Integration core (non-provider) fast/medium pass.
- Behavior fast pass in smoke and normal modes.
- Provider subsets: LM Studio and OpenAI tests demonstrably runnable locally with explicit enablement, or clearly documented skips when not enabled.
- Evidence artifacts committed under test_reports/ and referenced in CHANGELOG.md for the release candidate.


Section 0 — Execution Prep (Run-and-Capture Workflow)
- Purpose: Establish a deterministic, repeatable harness to execute this plan locally while CI is disabled. Do this first in every fresh environment.
- Directory setup (prevent tee failures and centralize artifacts):
  - mkdir -p test_reports test_reports/quality diagnostics
- Environment sanity and baseline capture:
  - poetry run devsynth doctor | tee diagnostics/doctor.txt
  - poetry run pytest --version | tee diagnostics/pytest_version.txt
  - poetry run python -V | tee diagnostics/python_version.txt
  - poetry run pip list | tee diagnostics/pip_list.txt
- Smoke-mode safety toggles (use for Section 1 fast lane if instability observed):
  - export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
  - export DEVSYNTH_TEST_TIMEOUT_SECONDS=${DEVSYNTH_TEST_TIMEOUT_SECONDS:-30}
- Evidence capture patterns (use tee consistently):
  - poetry run pytest --collect-only -q | tee test_reports/collect_only_output.txt
  - poetry run devsynth run-tests --inventory | tee test_reports/inventory_stdout.txt
  - poetry run devsynth run-tests --report --speed=fast | tee test_reports/html_report_stdout.txt
- Command Execution Log Template (copy/paste into diagnostics/exec_log.txt and fill as you run):
  - Timestamp:
  - Command:
  - Exit code:
  - Key outputs/artifacts:
  - Notes/anomalies:

Addendum — Critical Evaluation Notes (Alignment and Gaps)
- CLI Alignment: Verified that src/devsynth/application/cli/commands/run_tests_cmd.py exposes flags used throughout this plan (--target, --speed, --report, --no-parallel, --smoke, --segment/--segment-size, --maxfail, --feature, --inventory). No mismatches found.
- Provider Defaults: _configure_optional_providers() applies offline/stub defaults and sets DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false by default; aligns with hermetic fast and smoke lanes.
- Marker Discipline: scripts/verify_test_markers.py is present and referenced by docs/tests; plan mandates report and changed runs.
- Behavior/BDD: Ensure pytest-bdd is installed via dev extras; where instability occurs, prefer smoke mode. Scenarios touching providers must be gated with @pytest.mark.requires_resource.
- Execution Gaps Resolved: This addendum adds directory setup, diagnostics capture (doctor, versions, pip list), smoke env toggles, and a logging template to enforce reproducibility and evidence quality while CI is disabled.

Artifacts Checklist (commit under version control for release sign-off)
- diagnostics/: doctor.txt, pytest_version.txt, python_version.txt, pip_list.txt, exec_log.txt
- test_reports/: collect_only_output.txt, test_inventory.json, html/ (if generated), inventory_stdout.txt, html_report_stdout.txt
- test_reports/quality/: black_report.txt, isort_report.txt, flake8_report.txt, mypy_report.txt, bandit_report.txt, safety_report.txt
- test_markers_report.json (root or under test_reports/ per scripts), plus any smoke_plugin_notice.txt

Manual Execution Order (Authoritative, run in this order)
1) Section 0 — Execution Prep (this section). Ensure directories exist and capture diagnostics. Nothing optional for maintainers. ✓
2) Section 1 — Immediate Sanity and Inventory (with tee; use smoke toggles if needed). ✓
3) Section 2 — Speed Marker Discipline (run both --report and --changed; commit report). ✓
4) Section 5/4 — Integration and Behavior Tests (fast first, then medium; prefer --no-parallel; enable provider subsets explicitly). ✓
5) Section 3 — Resource-Gated Integrations (opt-in LM Studio and OpenAI lanes; verify skips by default). ✓
6) Section 6 — Documentation and CLI Alignment (fix mismatches immediately). ✓
7) Section 7 — Evidence Pack Artifacts (ensure all tee-captured outputs are present). ✓
8) Section 7b — Code Quality and Typing Gates (use tee to capture all reports; fix all errors until green; do not defer). ✓
9) Section 7c — Issues Audit and Dialectical Re-evaluation (update plan as findings emerge). ✓
10) Section 7d — Manual Sign-off Checklist (Everything Green). ✓

Strict Gates (Non-negotiable for 0.1.0a1)
- All tests pass in mandated lanes (including behavior, integration non-provider). Provider subsets must either pass when enabled or be cleanly skipped by default.
- Zero mypy errors under strict configuration; avoid broad ignores; document any targeted relaxations with TODO to restore.
- Black/isort/flake8/bandit/safety all clean; capture reports in test_reports/quality/ and commit.
- Evidence pack artifacts complete and referenced in CHANGELOG.md; pre-commit hooks installed and passing.
