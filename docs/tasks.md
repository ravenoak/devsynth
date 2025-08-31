# DevSynth v0.1.0a1 Improvement Tasks Checklist

Note: Each item is actionable. Complete them in order. Use the acceptance criteria in parentheses to verify completion. Items reference modules and docs called out in docs/plan.md.

See also:
- [Improvement Plan](plan.md)
- [CLI Command Reference](user_guides/cli_command_reference.md)
- [Test Framework README](../tests/README.md)

1. [ ] Establish baseline dev environment for validation
   1.1. [ ] Install minimal extras for a clean environment: poetry install --with dev --extras minimal (Verify install completes without optional extras)
   1.2. [x] Run quick sanity collection: poetry run pytest --collect-only -q (Expect collection succeeds)  
   1.3. [x] Verify doctor succeeds without optional extras: poetry run devsynth doctor (Expect exit 0; no ModuleNotFoundError: streamlit)

2. [x] Make WebUI optional at import time (guard/lazy import)
   2.1. [x] Audit for eager streamlit imports at module scope across:
        - src/devsynth/application/cli/commands/webui_cmd.py
        - src/devsynth/interface/webui.py
        - src/devsynth/interface/webui_bridge.py  
        (Identify any from-import or top-level import streamlit patterns.)
   2.2. [x] Implement lazy import within the command function in webui_cmd.py (import streamlit inside the function) with a friendly ImportError handler suggesting installing extras: webui.  
        (Module import must succeed on machines without streamlit.)
   2.3. [x] Add a guard at command registration (if aggregator exists) to conditionally register the webui command, or register a stub that prints a clear guidance message when invoked without the extra.  
        (devsynth --help either hides the WebUI command or shows it but it errors gracefully on invocation.)
   2.4. [x] Defer streamlit imports in src/devsynth/interface/webui.py and webui_bridge.py via a helper (e.g., _require_streamlit()) that raises a clear DevSynthError with install guidance if missing.  
        (No optional import at module scope; failure only on actual use.)
   2.5. [x] Re-run doctor on minimal env: poetry run devsynth doctor (Expect exit 0)  
        (Optionally verify devsynth --help behavior as per 2.3.)

3. [ ] Stabilize LM Studio tests and deterministic local path
   3.1. [x] Confirm default offline behavior: ensure DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false and DEVSYNTH_PROVIDER=stub are respected so LM Studio tests skip by default.  
        (Run: poetry run pytest -q -m "requires_resource('lmstudio')"; expect all skipped.)
   3.2. [x] Prevent accidental network calls in provider factory when resource flag is false. Review and adjust:
        - src/devsynth/application/llm/provider_factory.py
        - src/devsynth/application/llm/providers.py
        - src/devsynth/adapters/provider_system.py  
        (Add defensive checks for DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE and DEVSYNTH_OFFLINE.)
   3.3. [x] Add configurable request timeouts/retries in src/devsynth/application/llm/lmstudio_provider.py:  
        - Env vars: DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS (default: 10), DEVSYNTH_LMSTUDIO_RETRIES (default: 1), LM_STUDIO_ENDPOINT (default: http://127.0.0.1:1234)  
        - Apply timeouts to HTTP calls and implement small, idempotent retry logic.
   3.4. [x] Document the precise local enablement recipe in tests/README.md (and/or developer docs):  
        poetry install --with dev --extras "tests llm"  
        export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true  
        export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234  
        export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10  
        export DEVSYNTH_LMSTUDIO_RETRIES=1  
        poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 -m "requires_resource('lmstudio') and not slow"
   3.5. [ ] Validate enabled stability: run the targeted subset 3 times consecutively with no-parallel and maxfail=1; all green.  
        (Record results; flake rate must be 0.)

4. [x] Enforce and accelerate test speed marker/resource discipline
   4.1. [x] Ensure scripts/verify_test_markers.py is wired in pre-commit and release prep.  
        (Add/confirm a pre-commit hook running verify_test_markers.py with caching.)
   4.2. [x] Run marker verification report locally and fix violations:  
        poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json  
        poetry run python scripts/verify_test_markers.py --changed  
        (Expect zero violations.)
   4.3. [x] Confirm sentinel test exists and is marked @pytest.mark.fast: tests/test_speed_dummy.py  
        (Do not remove; ensure it adheres to discipline.)

5. [x] Default-to-stability ergonomics for triage
   5.1. [x] Add/verify documentation snippets recommending smoke mode to reduce plugin surface:  
        poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
   5.2. [x] Document segmentation guidance for medium/slow runs:  
        poetry run devsynth run-tests --segment --segment-size 50 --no-parallel
   5.3. [x] Document inventory scoping for quick target discovery:  
        poetry run devsynth run-tests --inventory --target unit-tests --speed=fast

6. [ ] Lint, typing, and security guardrails (high-signal fixes only)
   6.1. [x] Run Black/isort formatting checks and fix as needed:  
        poetry run black --check .  
        poetry run isort --check-only .
   6.2. [ ] Run Flake8 and address high-signal issues in src/ and tests/:  
        poetry run flake8 src/ tests/
   6.3. [ ] Run mypy in strict mode, adding minimal, documented overrides where required (with TODOs to restore strictness):  
        poetry run mypy src/devsynth
   6.4. [ ] Run Bandit (exclude tests) and address critical findings:  
        poetry run bandit -r src/devsynth -x tests
   6.5. [ ] Run Safety and review dependency advisories:  
        poetry run safety check --full-report

7. [x] Update CLI and testing documentation
   7.1. [x] Update docs/user_guides/cli_command_reference.md to explain WebUI optional availability and the guidance message when the extra is not installed.  
        (Reflect lazy/guarded import behavior and invocation-time error messaging.)
   7.2. [x] Update tests/README.md (and docs/developer_guides/testing.md if present) to include LM Studio enablement steps, smoke/segmentation defaults, and inventory scoping.  
        (Ensure examples are copy-paste runnable.)
   7.3. [x] Ensure Taskfile targets (Taskfile.yml) reference smoke/segmentation defaults and inventory scoping to speed triage.  
        (Add or adjust tasks without adding heavy new dependencies.)

8. [ ] Validate full local test matrix (no GPU/LLM heft; segmentation where appropriate)
   8.1. [x] Baseline discovery:  
        poetry run pytest --collect-only -q  
        poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
   8.2. [ ] Fast suites (no xdist):  
        poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel  
        poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel  
        poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel --smoke
   8.3. [ ] Medium/slow with segmentation:  
        poetry run devsynth run-tests --target unit-tests --speed=medium --segment --segment-size 50 --no-parallel  
        poetry run devsynth run-tests --target unit-tests --speed=slow --segment --segment-size 50 --no-parallel  
        (Repeat for integration/behavior as needed; optionally add --report.)

9. [ ] Confirm LM Studio offline/online acceptance criteria
   9.1. [x] Offline: poetry run pytest -q -m "requires_resource('lmstudio') and not slow".  
        (Resource flag false.)
   9.2. [ ] Enabled: Follow Section 3.4 recipe and run:  
        poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 -m "requires_resource('lmstudio') and not slow"  
        (Pass 3 consecutive runs.)

10. [x] Integrate marker verification and reports into release prep
    10.1. [x] Ensure test_markers_report.json is generated under test_reports/ during release prep (see .github/workflows/release_prep*.yml).  
         (Adjust workflow or scripts if necessary.)
    10.2. [x] Include verify_test_markers.py in the release readiness checklist and document how to run --changed for faster feedback on modified subsets.

11. [ ] Final release sign-off validation (v0.1.0a1)
    11.1. [ ] Doctor without optional extras: poetry run devsynth doctor → exit 0.  
          (Minimal extras env.)
    11.2. [ ] Marker discipline: zero violations from verify_test_markers.py.  
          (Report saved to test_markers_report.json.)
    11.3. [ ] All speeds green across unit/integration/behavior tests, following Section 8 matrix.  
          (Segment medium/slow first; optionally confirm without segmentation.)
    11.4. [ ] LM Studio: offline skipped by default; enabled path stable (3x green).  
          (No flakes.)
    11.5. [ ] Lint/typing/security checks: black/isort/flake8/mypy/bandit/safety all pass or have documented, temporary overrides with TODOs.

12. [x] Post-completion documentation tidy-up
    12.1. [x] Cross-link docs/plan.md, docs/tasks.md, docs/user_guides/cli_command_reference.md, and tests/README.md.  
          (Ensure consistency and remove stale guidance.)
    12.2. [x] Note timeline/ownership (optional) reflecting plan Sections 9–10 and Addendum.
