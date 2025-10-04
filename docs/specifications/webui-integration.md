# WebUI Integration Contract

## Overview

This specification captures the expectations for wiring the Streamlit WebUI,
its bridge helpers, and the provider system fallbacks without invoking external
services. It documents the deterministic seams exercised by the fast unit tests
so changes to the UI façade or provider orchestrator remain reliable in offline
pipelines.

## WebUI bootstrapping

* `devsynth.interface.webui.WebUI.run()` **must** construct a router with the
  navigation map returned by `navigation_items()` and execute it once the page
  is configured.
* The WebUI bootstrapper **must** hydrate `st.session_state.screen_width` and
  `st.session_state.screen_height` defaults when the session lacks screen
  dimensions so downstream layout helpers have deterministic baselines.
* Streamlit interactions in the fast tests use the reusable
  `tests.helpers.dummies.DummyStreamlit` stub to avoid importing the real
  `streamlit` package. New code should prefer this helper over bespoke mocks so
  the contract remains consistent.
* The typed simulation helper
  `devsynth.interface.webui.rendering_simulation.simulate_progress_rendering`
  **must** sanitize progress summaries and error payloads and return a
  structured `SimulationResult` so tests can assert safe rendering without a
  live Streamlit runtime.
* UI bridges and routers **must** satisfy the shared contracts defined in
  `devsynth.interface.streamlit_contracts` so the lazy import guards remain
  type-checked under the strict mypy gate.

## Command dispatch parity

* WebUI command mixins resolve callable targets via `_cli(name)`; resolutions
  should first check module-level exports before falling back to CLI modules so
  the UI stays aligned with the CLI surface area.
* `_handle_command_errors` **must** return the command result on success and
  surface actionable remediation when common exceptions (`ValueError`,
  `PermissionError`, etc.) bubble up. Tests assert that ValueError paths record
  both the error banner and follow-up guidance via `display_result`.

## WebUI bridge state hydration

* `devsynth.interface.webui_bridge.WebUIBridge.get_wizard_manager()` **must**
  call `_require_streamlit()` and use the active `st.session_state` object when
  instantiating wizard managers.
* `create_wizard_manager()` **must** delegate to
  `devsynth.interface.wizard_state_manager.WizardStateManager` with the
  provided session, wizard name, step count, and initial state so the wizard
  lifecycle stays centralized.
* `get_session_value` and `set_session_value` are thin passthroughs to
  `devsynth.interface.state_access` helpers; the tests ensure these proxies are
  invoked exactly once per call so future refactors do not bypass the shared
  validation logic.
* The deterministic wizard and session objects live under
  `tests.helpers.dummies` (`DummyWizardManager`, `DummySessionState`) and should
  be reused when new WebUI bridge scenarios require offline fixtures.

## Provider system fallbacks

* `devsynth.adapters.provider_system.FallbackProvider.complete()` **must** try
  providers sequentially, short-circuiting on the first success and surfacing a
  `ProviderError` with the last failure when all providers exhaust.
* Configuration can disable circuit breakers and retries; the tests exercise
  this by injecting dummy providers via the shared helpers without invoking
  network transports.
* `provider_system.embed()` **must** wrap unexpected exceptions (anything other
  than `ProviderError`/`NotImplementedError`) so callers receive a consistent
  `ProviderError` contract even when provider implementations raise arbitrary
  exceptions.

## Testing guidance

* Place fast unit tests for these seams under `tests/unit/interface/` and
  `tests/unit/adapters/` with the `@pytest.mark.fast` marker.
* Prefer the shared dummy helpers for Streamlit sessions, wizard managers, and
  providers to keep the orchestrator logic deterministic and offline-friendly.
