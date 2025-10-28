
# DevSynth System Verification Report

## Test Results Summary
- **Passes**: 3
  - Fast integration suite with optional backends gated by stubs (`diagnostics/integration-fast-default-threshold1.log`).
  - Fast integration suite with `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true` to confirm skips (`diagnostics/integration-fast-lmstudio-enabled.log`).
  - LM Studio live subset task (all tests skipped as expected) (`diagnostics/lmstudio_fast_subset.txt`).
- **Failures**: 1
  - OpenAI live subset task exited with code 5 because no `requires_resource('openai')` tests collected (`diagnostics/openai_fast_subset.txt`).
- **Smoke check**: Fails early during collection; coverage artifacts are not produced (`diagnostics/smoke-fast-20251021.log`).

## Component Status
✅ Promise system
✅ Agent system
✅ Error scenarios
⚠️ Memory system (Kuzu suites skipped without optional backend)
⚠️ LLM provider integrations (only LM Studio subset executed; OpenAI/OpenRouter unverified)
⚠️ Memory integrations (optional backends skipped)
⚠️ Fast execution paths (core integrations pass, but smoke profile still failing)
⚠️ LLM provider: openai (subset produced no collected tests)
⚠️ LLM provider: openrouter (not exercised this run)
⚠️ LLM provider: lmstudio (tests skipped behind feature flag)

## Available LLM Providers
⚠️ openai (no live evidence collected)
⚠️ openrouter (not exercised)
⚠️ lmstudio (skipped without local service)
