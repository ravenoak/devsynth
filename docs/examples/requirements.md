# Examples Requirements and Extras

This page documents the minimal installation required to run each example and gates heavier examples behind optional extras. Install via Poetry to ensure plugin availability and consistent environments.

General setup options (see .junie/guidelines.md):
- Minimal contributors: `poetry install --with dev --extras minimal`
- Targeted tests baseline: `poetry install --with dev --extras "tests retrieval chromadb api"`
- Full dev+docs (heavier): `poetry install --with dev,docs --all-extras`

Example-specific requirements:
- e2e_cli_example: minimal
  - `poetry install --with dev --extras minimal`
- e2e_webui_example: requires webui extra
  - `poetry install --with dev --extras "minimal webui"`
- dpg_ui_example: requires webui extra (and a browser environment)
  - `poetry install --with dev --extras "minimal webui"`
- full_workflow: recommended targeted test extras (retrieval, chromadb, api)
  - `poetry install --with dev --extras "tests retrieval chromadb api"`
- edrr_cycle_example: minimal
  - `poetry install --with dev --extras minimal`
- agent_adapter: minimal
  - `poetry install --with dev --extras minimal`
- mvu, spec_example, calculator, init_example, test_example, code_example: minimal
  - `poetry install --with dev --extras minimal`

Notes:
- Resource-gated tests/examples default to skip unless their resources are available (see tests/conftest.py and .junie/guidelines.md). To force-enable a backend locally, install the extra and export the availability flag, e.g.:
  - `poetry add tinydb --group dev`
  - `export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`
- For offline/deterministic runs, keep `DEVSYNTH_OFFLINE=true` and provider set to `stub` unless intentionally testing remote providers.
