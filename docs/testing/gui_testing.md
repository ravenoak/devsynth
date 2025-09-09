---
title: GUI Testing Guide
summary: How to run and skip GUI tests locally for the Dear PyGui optional interface.
status: draft
last_updated: 2025-08-24
---

# GUI Testing (Dear PyGui)

This project includes an optional desktop UI built with Dear PyGui. GUI tests are excluded by default in CI and during normal test runs to keep the suite fast and headless-friendly.

- Optional extra: `gui` (installs `dearpygui`)
- Marker used for GUI tests: `@pytest.mark.gui`
- Default behavior: excluded by `pytest.ini` via `-m "not slow and not gui"`

## Local Setup

1. Install the GUI extra (and dev tools):

   ```bash
   poetry install --with dev --extras gui
   ```

2. Verify optional import-time checks

   The `devsynth.interface.dpg_bridge` and `devsynth.interface.dpg_ui` modules guard Dear PyGui imports. If `dearpygui` is not installed, attempting to run the UI will raise a clear `RuntimeError`, while imports in non-UI contexts remain safe. Unit tests stub the `dearpygui` module to validate behavior without the extra installed.

## Running GUI Tests Locally

- Only GUI tests:

  ```bash
  poetry run pytest -m gui
  ```

- Include GUI tests with the rest:

  ```bash
  poetry run pytest -m "not slow"  # still excludes slow, includes gui
  ```

- Run a specific GUI test file:

  ```bash
  poetry run pytest tests/unit/interface/test_dpg_bridge.py -m gui
  ```

Note: Some GUI tests rely on stubbing Dear PyGui APIs and do not open real windows. Tests that require an actual GUI context are marked with `gui` and will be skipped unless explicitly included.

## CI and Headless Environments

- By default, CI excludes GUI tests via `pytest.ini` addopts.
- Keep GUI tests small and deterministic; prefer stubs/mocks over real windows.
- If you need to enable GUI tests in CI, ensure the runner has a display server (e.g., Xvfb) and explicitly pass `-m gui`.

## Troubleshooting

- If you see an error like "dearpygui is required for DearPyGUIBridge":
  - Install the extra: `poetry install --extras gui`
  - Or run tests without the gui marker (default behavior)
- If imports fail at collection time, ensure you're not importing `dearpygui` at module top-level outside guarded try/excepts. The DPG modules in this repo already follow this pattern.
