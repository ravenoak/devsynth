---
author: DevSynth Team
date: "2025-08-26"
last_reviewed: "2025-08-26"
status: published
title: DevSynth Resources Matrix
version: "0.1.0a1"
---
# DevSynth Resources Matrix

This matrix maps Poetry extras (pyproject [tool.poetry.extras]) to the environment flags used by tests and examples. Use it to quickly enable optional backends locally without pulling in unnecessary dependencies.

Guiding principles:
- Default test runs are offline and resource-gated; opt in explicitly when needed.
- Always run commands via Poetry to ensure the managed environment is active.

## Extras → Env Flags → Example Enablement

- minimal
  - Purpose: core CLI/runtime for local workflows
  - Install: `poetry install --with dev --extras minimal`
  - Env flags: none required

- tests
  - Purpose: plugins and minimal backends used by the test suite
  - Install: `poetry install --with dev --extras tests`
  - Env flags: set per‑resource as needed (see below)

- retrieval (Kuzu, FAISS)
  - Install: `poetry install --with dev --extras retrieval`
  - Env flags:
    - `DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true`

- chromadb (ChromaDB, tiktoken)
  - Install: `poetry install --with dev --extras chromadb`
  - Env flags:
    - `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true`

- memory (tinydb, duckdb, lmdb, kuzu, faiss-cpu, chromadb, numpy)
  - Install: `poetry install --with dev --extras memory`
  - Env flags (enable as needed):
    - `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true`
    - `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true`

- llm (client-side helpers like tiktoken, httpx)
  - Install: `poetry install --with dev --extras llm`
  - Env flags:
    - Provider defaults for tests: `DEVSYNTH_PROVIDER=stub`, `DEVSYNTH_OFFLINE=true`
    - To enable remote providers, set: `DEVSYNTH_PROVIDER=openai` and `OPENAI_API_KEY=...`

- api (FastAPI, Prometheus client)
  - Install: `poetry install --with dev --extras api`
  - Env flags:
    - `DEVSYNTH_RESOURCE_API_AVAILABLE=true` (if applicable in tests)

- webui (Streamlit for 0.1.0a1)
  - Install: `poetry install --with dev --extras webui`
  - Env flags:
    - `DEVSYNTH_RESOURCE_WEBUI_AVAILABLE=true`
  - Notes: NiceGUI is evaluated post-0.1.0a1 under a separate extra (webui_nicegui) if present.

- gpu (PyTorch + CUDA, Linux/x86_64 only)
  - Install: `poetry install --with dev --extras gpu`
  - Env flags: none specific; combine with providers/backends as needed

## Common Resource Flags

- CLI availability: `DEVSYNTH_RESOURCE_CLI_AVAILABLE=true`
- Codebase access: `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true`
- LM Studio (local LLM):
  - Install (optional): `poetry install --with dev --extras llm`
  - Configure: `export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234`
  - Enable tests: `export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true`
- Property tests: `DEVSYNTH_PROPERTY_TESTING=true` (with a speed marker + @pytest.mark.property)

Defaults in tests (set by fixtures/CLI for isolation):
- `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false`
- `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true`
- `DEVSYNTH_RESOURCE_CLI_AVAILABLE=true`
- `DEVSYNTH_PROVIDER=stub`
- `DEVSYNTH_OFFLINE=true`

## Recommended Install Profiles (recap)

- Minimal contributor setup:
  - `poetry install --with dev --extras minimal`
- Targeted test baseline without GPU/LLM heft:
  - `poetry install --with dev --extras "tests retrieval chromadb api"`
- Full dev + docs with all extras (maintainers):
  - `poetry install --with dev,docs --all-extras`

## Quick Examples

- Enable TinyDB-backed tests locally:
  - `poetry add tinydb --group dev`
  - `export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`
  - `poetry run devsynth run-tests --target unit-tests --speed=fast`

- Run fast smoke subset offline:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`

See also:
- `project guidelines` for authoritative development/testing practices
- `docs/developer_guides/testing.md` for detailed testing workflows and tips
