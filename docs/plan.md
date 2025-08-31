# DevSynth v0.1.0a1 Test & Release Readiness Improvement Plan

Status: Maintainers Final (2025-08-29)
Scope: Bring all fast/medium/slow unit, integration, behavior, and LM Studio tests to green locally; document gaps; propose minimal, high‑impact fixes for 0.1.0a1; keep CI/CD off until after release.

See also:
- [Improvement Tasks Checklist](tasks.md)
- [CLI Command Reference](user_guides/cli_command_reference.md)
- [Test Framework README](../tests/README.md)

0) Executive Summary (What we learned, why it matters)
- Current baseline (from diagnostics and repo evidence):
  - devsynth doctor fails on clean dev installs due to optional web UI dependency (streamlit) being imported at CLI import time. Evidence: diagnostics/doctor.txt shows ModuleNotFoundError: streamlit from devsynth.interface.webui import path.
  - LM Studio tests exist across unit and integration layers and are gated by @pytest.mark.requires_resource("lmstudio"). Default resource gating disables them (DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false in conftest and CLI), but targeted runs indicate intermittent failures before passing once. Evidence: diagnostics/exec_log.txt shows several non‑zero exits for lmstudio subsets before one green run.
  - run-tests CLI provides strong controls (smoke mode, segmentation, collection caching, inventory, feature flags) and sets offline/stub defaults as intended. Evidence: src/devsynth/application/cli/commands/run_tests_cmd.py and docs/user_guides/cli_command_reference.md.
  - Marker discipline is enforced via scripts/verify_test_markers.py; past performance issues were mitigated with caching. Evidence: issues/release-readiness-v0-1-0-alpha-1.md and numerous docs references; test_markers_report.json exists.
  - Release checklist previously blocked by: missing sentinel test (now added per issue history), hangs in run-tests, and slow marker verification. Evidence: issues/release-readiness-v0-1-0-alpha-1.md.

- Primary blockers for a frictionless local green suite before 0.1.0a1:
  1) Optional dependency import at CLI import time (streamlit) breaks doctor and can impact any CLI entrypoint that imports all commands eagerly.
  2) LM Studio tests show flakiness/instability under certain envs; require deterministic offline/stub mode or a robust local endpoint configuration with timeouts.
  3) Discipline and tooling must guarantee: exactly one speed marker per test, resource gating correctness, and stable collection (no plugin‑induced hangs) using smoke/segmentation defaults during triage.

- Thesis → Antithesis → Synthesis (Dialectical snapshot):
  - Thesis: The suite is already near‑green with offline/stub defaults; only enable resources intentionally and tests will skip reliably.
  - Antithesis: Evidence shows doctor fails on optional import; LM Studio subsets fail intermittently; prior hangs occurred even with fast marker sets; so defaults alone aren’t sufficient for a frictionless maintainer workflow.
  - Synthesis: Apply minimal code changes to make optional features truly optional at import time, codify stable LM Studio test execution paths (offline stub by default; explicit local endpoint recipe with timeouts), and enforce marker/resource discipline with fast verification tooling and smoke/segmentation as first‑line mitigations.

1) Ground Truth and Evidence
- Files reviewed:
  - src/devsynth/application/cli/commands/run_tests_cmd.py: Confirms offline‑first defaults, resource gating, smoke/segmentation options, inventory, feature flags.
  - conftest.py (repo root): Sets DEVSYNTH_OFFLINE=true, DEVSYNTH_PROVIDER=stub, DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false by default; restores env/CWD between tests; registers pytest‑bdd markers when available; relaxes coverage by default.
  - tests/README.md: Directory conventions, marker policies, resource gating guidance; commands to run subsets; confirms resource flags and extras.
  - docs/user_guides/cli_command_reference.md: Behavior of run-tests (inventory path, smoke mode, collection caching, segmentation guidance).
  - diagnostics/doctor.txt: ModuleNotFoundError: streamlit imported via webui command – breaks doctor.
  - diagnostics/exec_log.txt: Multiple attempts to run LM Studio subsets; initially non‑zero exits; one eventual green run. Indicates instability or sensitivity to environment/config ordering.
  - issues/release-readiness-v0-1-0-alpha-1.md: Historical blockers, later mitigations (sentinel test added; marker verifier caching), but persistent points about hangs and optional deps.
- LM Studio test surface (examples found):
  - tests/integration/general/test_lmstudio_provider.py
  - tests/integration/general/test_provider_system*.py
  - tests/integration/general/test_error_handling_at_integration_points.py
  - tests/integration/live/test_lmstudio_live_smoke.py
  - tests/unit/general/test_lmstudio_* and adapter/provider factory tests using requires_resource("lmstudio").

2) Goals and Non‑Goals (for 0.1.0a1)
- Goals:
  - All fast, medium, slow tests pass locally on a clean Poetry dev environment with minimal extras per guidelines (no GPU).
  - All integration tests green, with LM Studio tests either skipped by default (resource unavailable) or passing when enabled locally using the documented flow.
  - devsynth doctor succeeds without optional extras installed.
  - Marker verification and inventory generation complete reliably (<1 minute for markers; inventory scoping guidance documented).
- Non‑Goals:
  - CI/CD enablement or cloud cost optimizations (explicitly deferred until after initial release).
  - Feature expansion beyond what’s necessary for green tests and release readiness.

3) Risk Register
- Optional imports at module import time cause CLI crashes. Likelihood: High; Impact: Medium (blocks doctor). Mitigation: Lazy import or guarded command registration.
- LM Studio network instability or endpoint mismatches. Likelihood: Medium; Impact: Medium/High for integration runs. Mitigation: Offline stub as default, explicit local runbook, timeouts and retries.
- Plugin‑induced collection hangs (xdist, coverage, third‑party). Likelihood: Medium; Impact: Medium. Mitigation: smoke mode and segmentation defaults during triage; document.
- Marker discipline drift. Likelihood: Medium; Impact: Medium (collection paths broaden/not representative). Mitigation: pre‑commit guard and verify script in release checklist.

4) Minimal, High‑Impact Remediations (Actionable)
A. Make optional features truly optional at import time (doctor must pass without extras)
- Problem: diagnostics/doctor.txt shows streamlit imported during CLI import; doctor fails on clean dev.
- Proposed fix (one of):
  1) Guard command imports in application CLI: in devsynth.application.cli.commands.interface_cmds (or equivalent aggregator), wrap webui import in try/except ImportError; only register the webui command if import succeeds; otherwise, hide it with a helpful message on access.
  2) Alternatively, lazy import inside webui command function, so importing the module doesn’t import streamlit until execution.
- Acceptance:
  - poetry run devsynth doctor exits 0 without streamlit installed.
  - poetry run devsynth --help lists webui only if extra is installed (or lists it but errors gracefully on invocation with an explicit message).
- QA:
  - With minimal extras (poetry install --with dev --extras minimal), run doctor and run-tests fast; both succeed.

B. Stabilize LM Studio tests and document deterministic local path
- Problem: exec_log shows multiple failures before one success; resource gating exists but guidance needs to be operational and robust.
- Proposed actions:
  - Default path (offline): Keep DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false and DEVSYNTH_PROVIDER=stub; LM Studio tests skip unless explicitly enabled. Ensure tests don’t fail under this default – they must skip cleanly.
  - Local enabled path: Document a precise recipe to enable LM Studio tests:
    - poetry install --with dev --extras "tests llm"
    - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
    - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
    - export DEVSYNTH_OFFLINE=false (if hitting a real LM Studio)
    - Run: poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 -m "requires_resource('lmstudio') and not slow"
  - Timeouts/retries: If instability persists, add explicit request timeouts and small retry logic in the LM Studio adapter/service (idempotent ops only). Make timeouts configurable via env (e.g., DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10).
  - Segmentation: Recommend --segment --segment-size=50 for medium/slow suites and during triage.
- Acceptance:
  - Offline: No LM Studio test fails when resource flag is false; they report as skipped.
  - Enabled: The targeted subset above passes consistently (3 consecutive runs).

C. Enforce and accelerate marker/resource discipline
- Problem: Prior slow verify run; missing sentinel test once; discipline must be guaranteed.
- Proposed actions:
  - Keep scripts/verify_test_markers.py with persistent caching; ensure it’s wired in pre‑commit and release checklist.
  - Run both: poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json and poetry run python scripts/verify_test_markers.py --changed in local dev.
  - Ensure tests/test_speed_dummy.py remains present and marked @pytest.mark.fast.
- Acceptance:
  - Marker report shows zero violations.

D. Default‑to‑stability ergonomics when triaging flakes
- Problem: Prior hangs attributed to plugin surface.
- Proposed actions:
  - Document smoke mode as first step when encountering hangs: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  - Encourage segmentation for medium/slow: poetry run devsynth run-tests --segment --segment-size 50 --no-parallel
  - Recommend inventory scoping before full runs: poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
- Acceptance:
  - Maintainers can reproduce and bisect failures without stalls; documentation captures steps.

E. Lint/typing/coverage guardrails (keep strictness reasonable for 0.1.0a1)
- Actions:
  - Run and fix high‑signal findings only: black, isort, flake8, mypy strict (with targeted overrides documented), bandit (exclude tests), safety.
  - Maintain relaxed coverage by default (already implemented) and only enforce in a dedicated full run when needed.

5) Test Execution Matrix (Local)
- Baseline discovery
  - poetry run pytest --collect-only -q
  - poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
- Fast path
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel
  - poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --smoke
- Medium/Slow (prefer segmentation first)
  - poetry run devsynth run-tests --target unit-tests --speed=medium --segment --segment-size 50 --no-parallel
  - poetry run devsynth run-tests --target unit-tests --speed=slow --segment --segment-size 50 --no-parallel
  - Repeat for integration‑tests and behavior‑tests as needed; add --report to create HTML summaries.
- LM Studio subsets
  - Offline skip (default): no action; confirm skips via -m "requires_resource('lmstudio')"
  - Enabled local: see Section 4B recipe; require 3 consecutive green runs for stability sign‑off.

6) Validation and Acceptance Checklist
- Doctor works without optional extras:
  - poetry run devsynth doctor → exit 0 (no streamlit installed)
- Marker discipline:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json → zero violations
- All speeds green (unit/integration/behavior):
  - Fast: all pass without xdist
  - Medium/Slow: all pass with segmentation; re‑run without segmentation to confirm if time allows
- LM Studio:
  - Offline: all LM Studio tests skipped
  - Enabled: subset and then full LM Studio set pass 3x
- Lint/typing/safety:
  - poetry run black --check .
  - poetry run isort --check-only .
  - poetry run flake8 src/ tests/
  - poetry run mypy src/devsynth
  - poetry run bandit -r src/devsynth -x tests
  - poetry run safety check --full-report

7) Concrete Work Items (Minimal code/doc changes for 0.1.0a1)
- CLI optional import guard (High priority)
  - Implement guarded or lazy import for webui command to remove streamlit as hard dependency at import time.
  - Add a short section to docs/user_guides/cli_command_reference.md explaining optional availability of webui and the error message if not installed.
- LM Studio stability (High priority)
  - Verify resource‑gated tests skip cleanly by default.
  - If needed, add configurable timeout/retry parameters to LMStudio adapter/service; default reasonable timeouts in tests.
  - Add a local runbook snippet to tests/README.md (or developer_docs) with exact enablement steps.
- Marker discipline (Medium priority)
  - Ensure pre‑commit runs verify_test_markers.py; ensure test_markers_report.json is produced under test_reports/ in release prep scripts.
- Docs & runbooks (Medium priority)
  - This plan; ensure Taskfile targets reference the smoke/segmentation defaults and inventory scoping.

8) Socratic Review of Assumptions
- Q: Do we need LM Studio to pass in default local runs?
  - A: No. Resource‑gated tests are skipped by default; only enabled when explicitly requested. We must ensure enabling yields consistent green.
- Q: Will guarding optional imports hide features from users?
  - A: We can present commands conditionally or emit a clear error message suggesting to install the webui extra; no loss of core functionality.
- Q: Are hangs likely due to our code or third‑party plugins?
  - A: Past evidence implicates plugin surface; smoke mode mitigations are appropriate first response; further profiling only if hangs persist after smoke.
- Q: Is segmentation required long‑term?
  - A: It’s a triage tool. We keep it for medium/slow suites during the alpha period, aiming to remove once stability improves.

9) Timeline & Ownership (suggested)
- Week 0 (Now): Land optional import guard; update docs (this plan, LM Studio runbook notes). Re‑run baseline fast/unit/integration green. Owner: Core maintainer.
- Week 1: LM Studio timeout/retry tuning if needed; confirm 3x green runs enabled. Owner: Provider integrator.
- Week 1–2: Medium/slow stabilization via segmentation; marker discipline locks. Owner: Test engineering.

10) Release Sign‑off Criteria (v0.1.0a1)
- Green across fast/medium/slow for unit, integration, and behavior on a clean dev env without optional extras.
- devsynth doctor passes without streamlit.
- LM Studio: default skip; enabled path green 3x.
- Marker report shows zero violations; inventory generation works in scoped mode.

Appendix A: Environment Recipes
- Minimal contributor setup:
  - poetry install --with dev --extras minimal
  - poetry run pytest --collect-only -q
  - poetry run devsynth run-tests --speed=fast --no-parallel
- Targeted tests baseline without GPU/LLM heft:
  - poetry install --with dev --extras "tests retrieval chromadb api"
- LM Studio enabled path:
  - poetry install --with dev --extras "tests llm"
  - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel -m "requires_resource('lmstudio') and not slow"

Appendix B: Known References
- diagnostics/doctor.txt, diagnostics/exec_log.txt, diagnostics/pip_list.txt, diagnostics/pytest_version.txt
- issues/release-readiness-v0-1-0-alpha-1.md
- docs/user_guides/cli_command_reference.md
- tests/README.md


11) Critical Evaluation and Alignment Review (Dialectical + Socratic)
- Alignment with 0.1.0a1 goals:
  - Scope accurately targets green local runs for all speeds and test types with CI disabled. This aligns with release criteria (Sections 2, 6, 10). No CI dependencies assumed.✓
  - Optional dependency pain (streamlit) is a confirmed blocker for devsynth doctor and any eager CLI import path; remedy must be code-level (lazy/guarded import).✓
  - LM Studio instability acknowledged; plan mandates deterministic offline default and a precise enablement recipe. Need concrete code touchpoints and timeout env to ensure stability.✓
- Accuracy of evidence:
  - Diagnostics files and source references exist; we verified concrete modules:
    - Optional WebUI import sites: src/devsynth/application/cli/commands/webui_cmd.py, src/devsynth/interface/webui.py, src/devsynth/interface/webui_bridge.py.✓
    - LM Studio provider/adapters: src/devsynth/application/llm/lmstudio_provider.py, src/devsynth/application/llm/provider_factory.py, src/devsynth/application/llm/providers.py, src/devsynth/adapters/provider_system.py.✓
  - Tests that touch these areas exist (unit/integration/webui and lmstudio).✓
- Usefulness and forward drive:
  - The plan enumerates specific acceptance checks and a test matrix. To be fully actionable, it must include explicit code change options and env flags with names and default values (added below).✓
- Risks/Contradictions:
  - If CLI aggregates commands on import, simply lazy-importing inside webui_cmd may be insufficient; must ensure command registration itself is guarded. Mitigation: conditional registration in the CLI command aggregator (if present) or in Typer/Click command factory.✓
  - LM Studio mocks vs. live endpoint: ensure tests marked requires_resource("lmstudio") never attempt network calls when the resource flag is false, even if provider_factory imports lmstudio symbols. Add defensive checks.✓

12) Current Test Inventory & Status Synthesis
- Unit tests: fast/medium/slow across application, adapters, interface. WebUI unit tests mock streamlit via tests/fixtures/streamlit_mocks.py and webui_test_utils; they should pass without real streamlit.✓
- Integration tests: include general and live subsets for LM Studio (tests/integration/general/test_lmstudio_provider.py, tests/integration/live/test_lmstudio_live_smoke.py). By default, these must skip via @pytest.mark.requires_resource("lmstudio").✓
- Behavior tests: include Streamlit WebUI navigation feature and steps. Must pass under mocks and skip/live appropriately per resource flags.✓
- Marker discipline: scripts/verify_test_markers.py with caching; sentinel tests/test_speed_dummy.py present. Expect zero violations.✓
- Observed gaps needing attention before release:
  - Doctor failure via streamlit import on clean env. Critical.✓
  - Intermittent LM Studio subset failures; add timeout/retry and document exact enablement path.✓

13) Concrete Code Touchpoints and Minimal Change Options
A. Optional WebUI import safety (make optional at import time)
- Affected modules:
  - src/devsynth/application/cli/commands/webui_cmd.py (CLI command registration)
  - src/devsynth/interface/webui.py (may import streamlit directly)
  - src/devsynth/interface/webui_bridge.py (uses streamlit; add guard)
- Minimal options (choose one or combine):
  1) Guard command registration:
     - In the CLI commands aggregator or in webui_cmd.py, wrap import/registration in try/except ImportError for streamlit and, on failure, either:
       - Do not register the command; or
       - Register a stub command that prints: "WebUI is optional; install extras: webui or minimal+webui to enable (missing 'streamlit')." and exits with code 2 when invoked.
  2) Lazy import:
     - Within the command function (e.g., def webui():), import streamlit inside the function body and handle ImportError with a clear message while allowing module import to succeed.
  3) Bridge-level guard:
     - In src/devsynth/interface/webui.py and webui_bridge.py, add helper _require_streamlit() to defer import until used and raise DevSynthError with guidance if missing.
- Acceptance:
  - poetry run devsynth doctor → exit 0 on env without streamlit.
  - poetry run devsynth --help: webui not shown unless available, or shown but invoking gives a clear guided error without stack trace.

B. LM Studio stability and determinism
- Affected modules:
  - src/devsynth/application/llm/lmstudio_provider.py (HTTP calls; add timeouts/retries)
  - src/devsynth/application/llm/provider_factory.py and providers.py (respect DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE and DEVSYNTH_OFFLINE to avoid accidental live calls)
  - src/devsynth/adapters/provider_system.py (LMStudioProvider wiring)
- Configuration knobs (new/confirmed):
  - DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS (default: 10)
  - DEVSYNTH_LMSTUDIO_RETRIES (default: 1)
  - LM_STUDIO_ENDPOINT (default: http://127.0.0.1:1234)
- Test behavior:
  - When DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false, provider_factory must not attempt network calls; tests are skipped.
  - When true, provider uses configured endpoint with timeouts and limited retries; targeted subset should pass 3x consistently.

C. Marker/resource discipline guardrails
- Keep verify_test_markers.py in pre-commit. Ensure test_markers_report.json is generated under test_reports/ during release prep.
- Ensure exactly one speed marker per test function; resource markers used only where needed.

14) Measurable Success Metrics and Procedures
- Doctor stability: 100% pass on clean minimal env (5 consecutive runs). Command: poetry run devsynth doctor.
- LM Studio offline correctness: 0 failures, all relevant tests skipped when resource flag is false (verified via -m "requires_resource('lmstudio')").
- LM Studio enabled stability: run subset 3x with --no-parallel and --maxfail=1; 0 flake rate.
- Marker verification: verify_test_markers.py reports zero violations in <60s.
- End-to-end local matrix (Section 5) completes without hangs using smoke/segmentation guidance.

15) Refined Local Runbooks
- Optional WebUI not installed:
  - poetry install --with dev --extras minimal
  - poetry run devsynth doctor  # succeeds
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
- LM Studio enabled deterministic path:
  - poetry install --with dev --extras "tests llm"
  - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  - export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10
  - export DEVSYNTH_LMSTUDIO_RETRIES=1
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 -m "requires_resource('lmstudio') and not slow"

16) Definition of Done (DoD) Traceability
- Each point in Section 6 maps to a measurable command and pass/fail criteria.
- Release sign-off (Section 10) remains unchanged; all checks must be satisfied on a clean machine using Poetry.


Addendum (2025-08-29): Finalization and Quick-Start
- Reality Check: Current Status
  - The historical doctor failure was due to devsynth.interface.webui importing streamlit at module import time. Current code shows src/devsynth/application/cli/commands/webui_cmd.py performs a lazy import inside the command, which should allow doctor and general CLI imports to succeed even without the webui extra installed. Acceptance checks below remain required to validate on a clean environment.
  - LM Studio provider and tests exist; tests are resource-gated with requires_resource("lmstudio"). Offline default should skip these tests; enabled path must pass consistently.
  - Provider factory modules are present under both application/llm and adapters/providers; references in this plan are accurate.

- Do This Now (Maintainers Quick Start)
  1) Doctor sanity without extras
     - poetry install --with dev --extras minimal
     - poetry run devsynth doctor  # expect exit 0; no ModuleNotFoundError for streamlit
  2) Fast unit/integration baseline (no xdist)
     - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
     - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1
  3) Marker discipline
     - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json  # expect zero violations
  4) LM Studio offline skip check
     - poetry run pytest -q -m "requires_resource('lmstudio')" --collect-only  # expect listed tests, all skipped when run

- Failure Triage Flow (Decision Guide)
  - If collection or startup hangs:
    - Re-run in smoke mode: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
    - Use segmentation for medium/slow: --segment --segment-size 50 --no-parallel
    - Generate inventory to scope: poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
  - If doctor fails due to webui:
    - Confirm that webui_cmd performs lazy import (it does in current code). Inspect any aggregator that might eagerly import streamlit; if found, guard with try/except ImportError and show a friendly message or conditionally register the command.
  - If LM Studio tests flake when enabled:
    - Ensure environment: export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true; export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
    - Consider: export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10; export DEVSYNTH_LMSTUDIO_RETRIES=1
    - Run targeted subset 3x with no parallel and maxfail=1.

- Explicit Acceptance Commands and Expected Outcomes
  - Doctor without extras:
    - poetry run devsynth doctor → exit 0; no ModuleNotFoundError for streamlit
  - Marker report:
    - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json → zero violations
  - Fast suites (unit/integration/behavior):
    - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel → all pass
    - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel → all pass
    - poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --smoke → all pass
  - Medium/Slow with segmentation:
    - poetry run devsynth run-tests --target unit-tests --speed=medium --segment --segment-size 50 --no-parallel → all pass
    - poetry run devsynth run-tests --target unit-tests --speed=slow --segment --segment-size 50 --no-parallel → all pass
  - LM Studio offline:
    - poetry run pytest -q -m "requires_resource('lmstudio') and not slow" → all skipped
  - LM Studio enabled local path:
    - poetry install --with dev --extras "tests llm"
    - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
    - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
    - export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10
    - export DEVSYNTH_LMSTUDIO_RETRIES=1
    - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 -m "requires_resource('lmstudio') and not slow" → pass 3 consecutive runs

- Notes on Optional WebUI Import Safety
  - Current code uses lazy import within webui_cmd(), aligning with this plan’s recommendation. If any other module reintroduces eager streamlit import (e.g., in interface/webui.py at module scope or command aggregation), defer that import to runtime and handle ImportError with a clear guidance message.
