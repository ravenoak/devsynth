# DevSynth 0.1.0a1 Testing & Release Readiness Improvement Plan

Status: Draft for immediate execution (maintainer-run). Version 2025-09-01.
Owners: Core maintainers team. Scope: repository-wide testing, tooling, and release readiness for 0.1.0a1.

This plan critically evaluates the current test strategy and implementation, highlights gaps/blockers, and provides a concrete, reproducible remediation roadmap to ensure all tests (unit, integration, behavior/BDD, property, and resource-gated LLM integrations) are functional and reliable for the 0.1.0a1 release.

References
- Guidelines: See root message “DevSynth Development Guidelines” and tests/README.md.
- CLI: devsynth run-tests (src/devsynth/application/cli/commands/run_tests_cmd.py).
- Diagnostics evidence: diagnostics/*.txt (exec_log.txt, pip_list.txt, doctor.txt, pytest_version.txt).
- In-repo tickets under issues/ and linked throughout docs/.


0) Executive Summary (Dialectical Synthesis)
- Thesis: Our test system is comprehensive (unit/integration/behavior/property, strict speed markers, resource gating, Typer CLI runner, provider stubbing) and generally aligned to 0.1.0a1 constraints.
- Antithesis: Evidence shows instability and partial breakage around LM Studio integration, plugin loading variance, and optional deps that are not optional for maintainers. Docs/task checklists drifted empty; CI is disabled; some modules have relaxed mypy strictness with deadlines to restore.
- Synthesis: Consolidate commands and environments to a deterministic maintainer baseline via Poetry extras; enforce marker discipline; segment and smoke modes for stability; mandate evidence capture in diagnostics/; triage LM Studio/OpenAI flakes by resource flags and explicit local enablement; unblock release via low-throughput CI post‑release.

Release-Ready Definition (for 0.1.0a1)
- All unit tests fast path green locally with smoke mode off and xdist off by default; behavior and integration fast subsets green; resource‑gated LLM paths proven both in stub/offline mode and in opt‑in local live mode; marker report clean; type/lint/safety green with documented temporary mypy relaxations.
- For maintainers: nothing is optional; execute both offline/stub and live resource-gated subsets (OpenAI and LM Studio) before sign-off, per Sections 4.F and 11.


1) Current State Snapshot (Observed)
- Version: pyproject.toml pins version = "0.1.0a1" and Python >=3.12,<3.13.
- CLI runner: devsynth (Typer) with run-tests command supporting: target, --speed, --no-parallel, --report, --smoke, --segment, --segment-size, --maxfail, --feature, --inventory, and -m marker.
- Provider defaults: run-tests sets DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false unless overridden and applies ProviderEnv.with_test_defaults() to run offline/stub by default. This is correct for default stability.
- Tests structure: tests/README.md documents unit/, integration/, behavior/ (pytest-bdd), standalone/, fixtures/, property tests behind DEVSYNTH_PROPERTY_TESTING=true. A sentinel test tests/test_speed_dummy.py exists and must remain.
- Marker discipline: Exactly one speed marker per test function is mandatory (fast|medium|slow); script scripts/verify_test_markers.py enforces. Report output: test_reports/test_markers_report.json.
- Evidence: diagnostics/exec_log.txt records prior maintainer runs, including failing LM Studio subsets that were later stabilized, and a smoke fast run instruction pending execution capture.

Key Risks/Gaps
- LM Studio integration tests intermittently failed (diagnostics/exec_log.txt shows exit codes 1–2 before a pass). Root causes may include env flags, network mocking, or plugin interference.
- Optional deps (e.g., web UI/streamlit) caused import issues in doctor (doctor.txt); CLI must not import heavy UI modules on basic doctor/tests paths.
- Docs/task lists (docs/tasks.md, docs/task_notes.md) are empty; this reduces operational clarity.
- CI is disabled; we need a local, reproducible maintainer path and a minimal, low-throughput CI plan to enable post‑release.


2) Test Strategy Evaluation (Socratic)
- Q: Are speed markers precise and enforced? A: Mechanism exists; ensure it’s run on every local cycle. Action: integrate verify_test_markers.py into the maintainer workflow below.
- Q: Do behavior/BDD tests run deterministically? A: Only if pytest-bdd and related plugins are loaded; smoke mode disables third-party plugins. Action: provide non-smoke and smoke recipes and explicitly note when to use each.
- Q: Are LLM provider tests safe by default? A: Yes, default stub/offline and resources disabled. Action: provide explicit steps to enable OpenAI/LM Studio resources locally and separate smoke vs. live runs.
- Q: Do integration tests avoid accidental network calls? A: Should, via fixtures and responses; unit target toggles DEVSYNTH_TEST_ALLOW_REQUESTS=true to aid mocking while blocking raw sockets elsewhere. Action: keep this behavior; confirm no accidental egress by running in smoke + no-parallel + -m filters.
- Q: Is type safety acceptable? A: Strict globally with targeted relaxations and TODO deadlines (by 2025‑10‑01). Action: enforce mypy in plan; document relaxations.


3) Environment Baselines (Maintainer)
Recommended install profiles via Poetry (choose one):
- Full dev+docs with all extras (heaviest):
  poetry install --with dev,docs --all-extras
- Targeted test baseline (recommended for maintainers):
  poetry install --with dev --extras "tests retrieval chromadb api llm memory lmstudio"
- Minimal contributor (not for maintainers at this stage):
  poetry install --with dev --extras minimal

Set required environment defaults before running tests:
- export DEVSYNTH_OFFLINE=true
- export DEVSYNTH_PROVIDER=stub
- export OPENAI_API_KEY=test-openai-key
- export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false
- export DEVSYNTH_RESOURCE_CLI_AVAILABLE=true
- export DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true
- export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234

Note: The run-tests command applies similar defaults if unset; explicit export ensures clarity in shell sessions and when calling pytest directly.


3a) Tooling Availability Verification (Environment Probe)
- Verify core tools are available and capture versions (append outputs to diagnostics/ where useful):
  - poetry --version | tee diagnostics/poetry_version.txt
  - python --version | tee -a diagnostics/poetry_version.txt
  - pip --version | tee diagnostics/pip_version.txt
  - pytest --version | tee diagnostics/pytest_version.txt
  - mypy --version | tee diagnostics/mypy_version.txt
  - flake8 --version | tee diagnostics/flake8_version.txt
  - black --version | tee diagnostics/black_version.txt
  - isort --version | tee diagnostics/isort_version.txt
  - bandit --version | tee diagnostics/bandit_version.txt
  - safety --version | tee diagnostics/safety_version.txt
  - curl --version | tee diagnostics/curl_version.txt
  - devsynth --version | tee diagnostics/devsynth_version.txt
  - task --version | tee diagnostics/task_version.txt  # Taskfile aliases are available and mirror Poetry commands verified below
- LM Studio preflight (only for live/gated runs):
  - echo ${LM_STUDIO_ENDPOINT:-http://127.0.0.1:1234} | tee diagnostics/lmstudio_endpoint.txt
  - curl -sS ${LM_STUDIO_ENDPOINT:-http://127.0.0.1:1234}/v1/models | tee diagnostics/lmstudio_models.json
  - if lms --help >/dev/null 2>&1; then lms models list | tee diagnostics/lms_models_list.txt; else echo "[warn] lms CLI not found; rely on curl preflight" | tee -a diagnostics/exec_log.txt; fi
  - If endpoint not reachable, set DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false (default) and skip live LM Studio tests until resolved; file/update an issue with collected diagnostics.
- Note on Task aliases: The repository’s Taskfile.yml provides aliases such as tests:unit-fast, tests:integration-fast, verify:markers, doctor:lmstudio, and guardrails:all. You may use either the task alias or the explicit Poetry command shown in this plan; both are supported and equivalent.

4) Operational Runbook (Execute and Capture Evidence)
All commands below must be executed by maintainers and captured to diagnostics/ (append to diagnostics/exec_log.txt with timestamp, exit code, and notes). Prefer running via Poetry to ensure plugin availability.

A. Discovery and collection
- poetry run pytest --collect-only -q | tee diagnostics/pytest_collect.txt
- poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1 | tee diagnostics/unit_fast_smoke.txt
- poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json | tee diagnostics/test_marker_verify.txt
- poetry run devsynth run-tests --inventory | tee diagnostics/test_inventory_capture.txt

B. Unit tests
- Fast path (no plugins disabled):
  poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
- Medium/slow when needed:
  poetry run devsynth run-tests --target unit-tests --speed=medium --no-parallel --maxfail=1
  poetry run devsynth run-tests --target unit-tests --speed=slow --no-parallel --maxfail=1

C. Integration tests
- Fast, stable run:
  poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1
- Segment if instability is observed:
  poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --segment --segment-size 50 --maxfail=1

D. Behavior/BDD tests
- Standard:
  poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1
- If plugin issues arise, use smoke mode (disables third‑party plugins):
  poetry run devsynth run-tests --target behavior-tests --smoke --speed=fast --no-parallel --maxfail=1

E. Property tests (opt-in)
- export DEVSYNTH_PROPERTY_TESTING=true
- poetry run pytest tests/property/ -q

F. Resource-gated LLM tests (two modes)
1) Offline/stub validation (default):
- poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai') and not requires_resource('lmstudio')" --no-parallel --maxfail=1
2) Live/local validation (maintainer-only; ensure backends installed and running):
- OpenAI:
  export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
  export OPENAI_API_KEY=sk-...  # real key
  poetry run devsynth run-tests --speed=fast -m "requires_resource('openai') and not slow" --no-parallel --maxfail=1
- LM Studio:
  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234  # ensure LM Studio server is running
  poetry run devsynth run-tests --speed=fast -m "requires_resource('lmstudio') and not slow" --no-parallel --maxfail=1

G. Full report generation
- poetry run devsynth run-tests --report --speed=fast --no-parallel | tee diagnostics/test_report_fast.txt
  # HTML output under test_reports/

H. Quality gates
- Format/lint:
  poetry run black --check . && poetry run isort --check-only . && poetry run flake8 src/ tests/
- Security:
  poetry run bandit -r src/devsynth -x tests
  poetry run safety check --full-report
- Typing (strict with configured relaxations):
  poetry run mypy src/devsynth

I. Troubleshooting quick path
- poetry run devsynth doctor | tee diagnostics/doctor.txt  # if this fails due to optional UI deps, file a ticket and avoid importing UI in doctor path
- poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 | tee diagnostics/fast_smoke_run.txt


5) Findings To Date (from diagnostics and repo scan)
- LM Studio subset runs intermittently failed but were ultimately green (see diagnostics/exec_log.txt entries 45–180). This suggests timing/env flakiness instead of deterministic failures.
- devsynth doctor previously failed due to streamlit import (diagnostics/doctor.txt). Action: ensure doctor path does not import web UI modules; if already fixed, confirm and close the corresponding issue.
- tests/ README and tooling are comprehensive; however, we need to enforce marker verification in daily workflow and include the generated report in PR artifacts post‑release.
- docs/tasks.md and docs/task_notes.md are empty; we’ll fill actionable checklists in this plan instead and consider removing/archiving empty files or populating them in a follow-up docs task.


6) Remediation Tasks (Prioritized and Actionable)
A. Stabilize LM Studio integration tests
- Install required extras locally: poetry install --with dev --extras "llm api"
- Ensure LM Studio server available at LM_STUDIO_ENDPOINT; consider a lightweight health check in tests to skip fast if unreachable despite DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true.
- Add retry/backoff for transient connection failures in LM Studio provider adapter (if not present) under tests requiring live calls; bound retries to <5s to keep tests fast.
- Run focused subset: poetry run devsynth run-tests --speed=fast -m "requires_resource('lmstudio') and not slow" --no-parallel --maxfail=1
- Capture outputs to diagnostics/ and record flake rate; open/close issues under issues/ accordingly.

B. Enforce marker discipline continuously
- Mandate: poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Fail local pre‑commit/Task if violations exist; add a Taskfile target (if not already present) to run marker verification.

C. Prevent heavy optional imports in test/doctor paths
- Ensure devsynth doctor and run-tests code paths do not import GUI/webui modules by default. If import occurs, refactor to lazy‑load behind feature flags or extras.
- Validate: run doctor again and capture diagnostics/doctor.txt.

D. Behavior test plugin stability
- Default runs should be without smoke; document smoke fallback for plugin flake. If persistent, identify problematic plugin via PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 toggling and selectively load required plugins only.

E. Provider configuration sanity
- Confirm ProviderEnv.with_test_defaults() sets DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true when not set. Document overrides explicitly in this plan (done above). Add tests for this behavior if missing.

F. Property tests hygiene
- Ensure all property tests include both @pytest.mark.property and exactly one speed marker. Update tests/property/ accordingly and add to marker verification scope.

G. Type and lint gates (pre‑release)
- Run black/isort/flake8; fix violations.
- Run mypy; for modules with temporary relaxations (documented in pyproject [tool.mypy] overrides), add TODO comments and a tracking issue to restore strictness by 2025‑10‑01.

H. Requirements traceability and inventory
- Run --inventory to generate test inventory under test_reports/ and attach to release notes. Ensure tests’ docstrings contain ReqID: tags per tests/README.md.

I. Minimal CI (post‑release only)
- Prepare a GitHub Actions workflow (disabled until after 0.1.0a1) with:
  - Single Linux/Python 3.12 job
  - poetry install --with dev --extras "tests api llm" (no GPU/backends)
  - smoke fast run: devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  - marker verification script
  - mypy and flake8
  - Cache Poetry and .pytest_cache
  - Low throughput (manual dispatch and nightly schedule only)


7) Evidence Capture Protocol
- For each command executed, append an entry in diagnostics/exec_log.txt:
  - Timestamp
  - Command
  - Exit code
  - Key outputs/artifacts
  - Notes/anomalies
- Store larger outputs under diagnostics/ or test_reports/ and reference paths in commit messages and issues/ tickets.


8) Rollout Plan & Timeline
- T+0 (today): Execute §4 A–D and H, capture evidence; fix test and import instabilities identified; raise/close issues as appropriate.
- T+1: Complete §6 A–G tasks; repeat core test runs; generate report.
- T+2: Freeze for 0.1.0a1, tag release; keep CI disabled.
- Post‑release: Enable minimal CI described in §6.I; monitor; incrementally widen scope.


9) Risk Register
- Plugin instability (pytest-bdd/xdist): Mitigation — smoke mode, no-parallel default for maintainers, segmentation.
- External provider flakiness (OpenAI/LM Studio): Mitigation — default to stub/offline, gated resource flags; short retries and explicit availability checks.
- Optional dependency import bleed: Mitigation — lazy‑load GUI/web components; add guard tests.
- Marker discipline drift: Mitigation — verify_test_markers in local workflow and CI post‑release.
- Type hygiene debt: Mitigation — documented relaxations with deadline; mypy gate.


10) Alignment with In‑Repo Issues (non‑exhaustive linkage)
- issues/devsynth-run-tests-hangs.md — incorporate smoke/no-parallel/segment guidance and plugin gating.
- issues/Resolve-pytest-xdist-assertion-errors.md — addressed by defaulting to no‑parallel for maintainers and segment mode; plan to re‑enable selectively.
- issues/Critical-recommendations-follow-up.md — parts mapped to testing stabilization and provider configuration in this plan.
- issues/kuzu-memory-integration.md and related backends — treat as resource‑gated; keep disabled by default; provide enablement guidance.
- Any doctor/streamlit import tickets — addressed by §6.C.


11) Exit Criteria Checklist (maintainer must tick locally)
- [ ] Fast unit tests green: devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
- [ ] Fast integration tests green (segmented if needed)
- [ ] Behavior fast tests green (smoke fallback not required)
- [ ] Marker verification passes and report attached
- [ ] Offline/stub runs exclude resource tests cleanly
- [ ] Live OpenAI subset passes when explicitly enabled
- [ ] Live LM Studio subset passes when explicitly enabled
- [ ] mypy/flake8/black/isort/safety/bandit pass (with documented relaxations)
- [ ] Evidence captured in diagnostics/ and referenced in issues/
- [ ] Release notes include test inventory and known limitations


Appendix: Useful Commands
- poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
- poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --segment --segment-size 50 --maxfail=1
- poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1
- poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- poetry run devsynth run-tests --inventory
- poetry run mypy src/devsynth
- poetry run flake8 src/ tests/
- poetry run black --check . && poetry run isort --check-only .


12) Critical Reevaluation & Alignment Update (2025-09-01)
- The plan is broadly aligned with the DevSynth Development Guidelines and repo reality. Enhancements added here tighten operational rigor, increase determinism, and make every exit criterion verifiable with concrete commands and artifacts. Key updates:
  - Added an Execution Verification Matrix tying exit criteria to commands and evidence.
  - Added a Failure Triage Loop and Smoke vs. Full Run decision tree.
  - Clarified provider module paths and recommended bounded retry/health-check strategy for LM Studio and OpenAI.
  - Elevated maintainer baseline to explicitly include the lmstudio extra in installs.
  - Provided an Execution Ledger template and an issues/ review protocol.

13) Execution Verification Matrix (Commands, Expected Artifacts, Pass/Fail Signals)
- Fast unit tests green
  - Command: task tests:unit-fast
  - Artifact: diagnostics/unit_fast_smoke.txt (or console if not tee'd). Pass: exit code 0, no xfail/unexpected failures.
- Fast integration tests green (segmented if needed)
  - Command: task tests:integration-fast; if flaky: poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --segment --segment-size 50 --maxfail=1
  - Artifact: diagnostics/integration_fast.txt. Pass: exit code 0.
- Behavior fast tests green (without smoke ideally)
  - Command: poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1
  - Fallback: task tests:behavior-fast-smoke
  - Artifacts: diagnostics/behavior_fast.txt. Pass: exit code 0.
- Marker verification passes
  - Command: task verify:markers
  - Artifact: test_reports/test_markers_report.json (clean, zero violations).
- Offline/stub runs exclude resource tests cleanly
  - Command: poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai') and not requires_resource('lmstudio')" --no-parallel --maxfail=1
  - Pass: exit code 0; collection shows 0 selected for gated resources.
- Live OpenAI subset passes (explicitly enabled)
  - Export: DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true; OPENAI_API_KEY=sk-...
  - Command: poetry run devsynth run-tests --speed=fast -m "requires_resource('openai') and not slow" --no-parallel --maxfail=1
  - Modules: src/devsynth/application/llm/openai_provider.py; adapters/provider_system.py
  - Pass: exit code 0.
- Live LM Studio subset passes (explicitly enabled)
  - Export: DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true; LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  - Preflight: task doctor:lmstudio
  - Command: poetry run devsynth run-tests --speed=fast -m "requires_resource('lmstudio') and not slow" --no-parallel --maxfail=1
  - Modules: src/devsynth/application/llm/lmstudio_provider.py; provider_factory.py; providers.py; tests/fixtures/lmstudio_service.py
  - Pass: exit code 0.
- Type/Lint/Security gates pass
  - Command: task guardrails:all (runs black/isort/flake8/mypy/bandit/safety)
  - Artifacts: diagnostics/*_report.txt as produced by the script. Pass: no errors.
- Test inventory captured
  - Command: poetry run devsynth run-tests --inventory | tee diagnostics/test_inventory_capture.txt
  - Artifacts: test_reports/ inventory outputs + diagnostics/test_inventory_capture.txt

14) Failure Triage Loop (Deterministic Debugging Protocol)
1. Re-run in smoke mode to minimize plugin surface:
   - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 | tee diagnostics/fast_smoke_run.txt
2. Segment failing target to isolate:
   - add --segment --segment-size 50
3. Capture environment and versions:
   - poetry run pytest --version | tee diagnostics/pytest_version.txt
   - poetry run pip list | tee diagnostics/pip_list.txt
   - date -u +'ISO8601: %Y-%m-%dT%H:%M:%SZ' | tee -a diagnostics/exec_log.txt
4. Provider triage:
   - Ensure DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true for offline runs.
   - For LM Studio, run: task doctor:lmstudio and capture diagnostics/lmstudio_health.json.
5. Minimize imports: set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and selectively enable needed plugins.
6. File/update an issue under issues/ with links to diagnostics artifacts, reproduction command, and exit code.

15) Smoke vs. Full Run Decision Tree
- Start with full run for the chosen target with --no-parallel.
- If intermittent plugin failures or unrelated third-party stack traces appear, re-run with --smoke.
- If collection-time errors occur, use --smoke first, then add plugins back selectively.
- Use segmentation when the suite is large or instability persists.

16) Provider Modules & Health Checks (LM Studio and OpenAI)
- LM Studio
  - Primary module: src/devsynth/application/llm/lmstudio_provider.py (LMStudioProvider, LMStudioConnectionError, LMStudioModelError, _LMStudioProxy).
  - Factory flags: src/devsynth/application/llm/provider_factory.py and src/devsynth/application/llm/providers.py (lmstudio_requested).
  - Health-check heuristic: GET {LM_STUDIO_ENDPOINT}/v1/models or a lightweight /health endpoint if available; skip fast if non-200 and DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true with clear message.
  - Bounded retry guidance: short exponential backoff totaling <= 5s for initial handshake calls; open a tracking issue if missing; keep retries off for unit tests unless requires_resource('lmstudio').
- OpenAI
  - Primary module: src/devsynth/application/llm/openai_provider.py; adapters/provider_system.py.
  - Validation: fail fast if OPENAI_API_KEY missing when provider explicitly requested; otherwise default to stub.

17) Execution Ledger Template (append to diagnostics/exec_log.txt)
---
Timestamp: 2025-09-01THH:MM:SSZ
Command: poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
Exit Code: 0
Artifacts: diagnostics/unit_fast_smoke.txt, test_reports/index.html
Notes: brief summary of failures/retries/segments used
---

18) Systematic Issues Review Protocol
- Enumerate issues/ directory and link each relevant ticket within commit messages.
- For every non-green run, create/update an issue with: reproduction command, exit code, logs under diagnostics/, and suspected root cause.
- Close issues only after evidence of green rerun and artifacts are captured.

19) Maintainer Must-Run Sequence (Concise)
1) Setup: poetry install --with dev --extras "tests retrieval chromadb api llm memory lmstudio"
2) Sanity: task tests:collect && task verify:markers
3) Unit fast: task tests:unit-fast
4) Integration fast: task tests:integration-fast
5) Behavior fast: poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --maxfail=1
6) Offline/stub: poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai') and not requires_resource('lmstudio')" --no-parallel --maxfail=1
7) Live OpenAI (opt-in): export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true && export OPENAI_API_KEY=sk-... && poetry run devsynth run-tests --speed=fast -m "requires_resource('openai') and not slow" --no-parallel --maxfail=1
8) Live LM Studio (opt-in): export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true && task doctor:lmstudio && poetry run devsynth run-tests --speed=fast -m "requires_resource('lmstudio') and not slow" --no-parallel --maxfail=1
9) Reports: poetry run devsynth run-tests --report --speed=fast --no-parallel | tee diagnostics/test_report_fast.txt
10) Guardrails: task guardrails:all
