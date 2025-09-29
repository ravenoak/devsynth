# Integration Tests and Optional Extras Enablement

This guide explains how to enable and run integration tests that depend on optional extras. It complements the Resources Matrix and the Testing Guide by giving concrete, copy‑pasteable commands.

Audience: developers running integration tests locally or in targeted CI jobs.

## TL;DR
- Install only the extras you need with Poetry.
- Export the corresponding DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true flags so tests unskip.
- Run via the CLI wrapper to ensure consistent plugins and env defaults:
  poetry run devsynth run-tests --target integration-tests --speed=medium

### Deterministic unit coverage for optional memory backends
- The memory unit suite now provides in-repo stubs for ChromaDB, DuckDB, FAISS, and Kuzu.
- Stubs live under `tests/unit/application/memory/conftest.py` and set resource flags automatically.
- CRUD tests exercise the production adapters without needing the optional wheels installed.
- Install the real extras only when validating live integrations or performance tuning.

## Extras to Resource Flags Mapping
These extras are defined in pyproject [tool.poetry.extras] and map to test resource flags as follows:

- retrieval → kuzu, faiss-cpu
  - Flags: DEVSYNTH_RESOURCE_KUZU_AVAILABLE, DEVSYNTH_RESOURCE_FAISS_AVAILABLE
- chromadb → chromadb, tiktoken
  - Flags: DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE
- memory → tinydb, duckdb, lmdb, kuzu, faiss-cpu, chromadb, numpy
  - Flags: DEVSYNTH_RESOURCE_TINYDB_AVAILABLE, DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE, DEVSYNTH_RESOURCE_LMDB_AVAILABLE, DEVSYNTH_RESOURCE_KUZU_AVAILABLE, DEVSYNTH_RESOURCE_FAISS_AVAILABLE, DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE
- api → fastapi, prometheus-client
  - Flags: DEVSYNTH_RESOURCE_CLI_AVAILABLE=true is on by default; API-specific tests may require DEVSYNTH_RESOURCE_API_AVAILABLE=true (if present) or will be guarded via requires_resource("api").
- webui → nicegui
  - Flags: Prefer @pytest.mark.gui + requires_resource("webui"); enable with DEVSYNTH_RESOURCE_WEBUI_AVAILABLE=true.
- llm → tiktoken, httpx
  - In tests, LLM calls are stubbed by default; keep DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true unless explicitly testing live providers.

Other useful development extras:
- tests → fastapi, httpx, tinydb, duckdb, lmdb, astor (used by tests themselves)
- minimal → baseline CLI/runtime without heavy deps

Note: Defaults in tests/conftest.py set a conservative, isolated environment. Many resource flags default to false unless explicitly set. CLI wrapper sets DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true by default for safety.

## Common Scenarios and Commands

All examples assume Python 3.12 and Poetry environment.

### Chromadb-backed integration tests
Install extras and enable the resource:

```
poetry install --with dev --extras "tests chromadb"
poetry shell
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
# Optional: ensure property and slow tests stay disabled
unset DEVSYNTH_PROPERTY_TESTING
poetry run devsynth run-tests --target integration-tests --speed=medium
```

### Retrieval stack (Kuzu + FAISS)
```
poetry install --with dev --extras "tests retrieval"
poetry shell
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
poetry run devsynth run-tests --target integration-tests --speed=medium
```

### Memory backends (TinyDB, DuckDB, LMDB)
```
poetry install --with dev --extras "tests memory"
poetry shell
export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true
export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true
poetry run devsynth run-tests --target integration-tests --speed=medium
```

### API integrations (FastAPI endpoints, metrics)
```
poetry install --with dev --extras "tests api"
poetry shell
# Some suites gate API with a specific flag; if present, enable it:
export DEVSYNTH_RESOURCE_API_AVAILABLE=true
poetry run devsynth run-tests --target integration-tests --speed=medium
```

### WebUI-related integration tests (NiceGUI)
```
poetry install --with dev --extras "tests webui"
poetry shell
export DEVSYNTH_RESOURCE_WEBUI_AVAILABLE=true
# GUI tests are also marked with @pytest.mark.gui; include them explicitly if needed
poetry run devsynth run-tests --target integration-tests --speed=medium -m "not slow and not gui"  # default
# Or include gui explicitly:
poetry run devsynth run-tests --target integration-tests --speed=medium -m "not slow"
```

## Notes on Stability and Isolation
- Use --no-parallel if a backend is sensitive to parallel access. Prefer @pytest.mark.isolation on tests that must run alone.
- Deterministic seeds and timeouts are centralized in tests/conftest.py; medium-speed suites should remain deterministic.
- Keep network calls disabled (disable_network fixture). To temporarily allow requests for specific tests, use DEVSYNTH_TEST_ALLOW_REQUESTS=true and targeted markers.

## Troubleshooting
- If tests are being skipped unexpectedly, run with -rs to see skip reasons.
- Verify that the extras installed match the flags you set.
- Re-run in smoke mode if startup is slow or third-party plugins cause interference:
  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

## References
- DevSynth Development Guidelines (root of repo)
- docs/developer_guides/testing.md
- docs/user_guides/cli_command_reference.md
- pyproject.toml [tool.poetry.extras]
