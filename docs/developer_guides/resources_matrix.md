---
author: DevSynth Team
date: "2025-08-26"
last_reviewed: "2025-08-26"
status: published
title: Resources Matrix (Extras ↔ Environment Flags)
version: "0.1.0a1"
---

# Resources Matrix (Extras ↔ Environment Flags)

This page concisely maps Poetry extras to their associated resource flags and shows how to opt into optional backends locally. It complements:
- project guidelines (testing/resource gating defaults)
- docs/developer_guides/testing.md (end-to-end testing practices)
- docs/user_guides/cli_command_reference.md (run-tests behavior and flags)

Principles:
- Offline-first and deterministic by default in CI and most local runs.
- Optional backends are disabled unless explicitly enabled via env flags.
- Tests that depend on optional backends are decorated with @pytest.mark.requires_resource("<name>").

Defaults (unless overridden):
- DEVSYNTH_OFFLINE=true
- DEVSYNTH_PROVIDER=stub
- DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false

## Quick usage
- Install the extra(s) you need, then enable the corresponding resource flag(s):
  poetry install --with dev --extras "<extra>"
  export DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true
  poetry run devsynth run-tests --speed=fast

Tip: Use smoke mode for the most stable runs when enabling backends the first time:
  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

## Matrix

Minimal formatting for clarity; NAME refers to the placeholder in DEVSYNTH_RESOURCE_<NAME>_AVAILABLE.

- Extra: minimal
  - Purpose: core libs for CLI and local workflows (no heavy backends)
  - Resource flags: none (does not enable optional backends)

- Extra: tests
  - Purpose: plugins and minimal backends used by tests
  - Resource flags: none auto-enabled; use flags below to opt in

- Extra: retrieval
  - Likely deps: kuzu, faiss-cpu
  - Resource flags you can enable:
    - DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true (NAME=KUZU)
    - DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true (NAME=FAISS)

- Extra: chromadb
  - Likely deps: chromadb, tiktoken
  - Resource flags:
    - DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true (NAME=CHROMADB)

- Extra: memory
  - Likely deps: tinydb, duckdb, lmdb, kuzu, faiss-cpu, chromadb, numpy
  - Resource flags (enable selectively as needed):
    - DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true (NAME=TINYDB)
    - DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true (NAME=DUCKDB)
    - DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true (NAME=LMDB)
    - DEVSYNTH_RESOURCE_VECTOR_AVAILABLE=true (NAME=VECTOR)
    - DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true (NAME=KUZU)
    - DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true (NAME=FAISS)
    - DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true (NAME=CHROMADB)

- Extra: llm
  - Likely deps: tiktoken, httpx
  - Resource flags: none required for stub provider; for real LLMs use provider-specific env (OPENAI_API_KEY, LM_STUDIO_ENDPOINT) and resource flags as applicable (see lmstudio below)

- Extra: api
  - Likely deps: fastapi, prometheus-client
  - Resource flags: none (API components are local)

- Extra: webui
  - Likely deps: nicegui
  - Resource flags: none (UI is local)

- Extra: gpu
  - Likely deps: torch + CUDA (Linux/x86_64 only)
  - Resource flags: none; GPU use is auto-detected by libraries

- Resource: lmstudio (not an extra by itself, typically leveraged with llm)
  - Enable when running LM Studio-related tests:
    - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true (NAME=LMSTUDIO)
    - export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234

- Built-in resources for test infrastructure
  - DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true (default true in tests)
  - DEVSYNTH_RESOURCE_CLI_AVAILABLE=true (default true in tests)

## Examples

- Enable TinyDB-backed tests:
  poetry install --with dev --extras memory
  export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
  poetry run devsynth run-tests --speed=fast

- Run vector adapter smoke tests (numpy-backed):
  poetry install --with dev --extras memory
  export DEVSYNTH_RESOURCE_VECTOR_AVAILABLE=true
  poetry run devsynth run-tests --tests tests/unit/application/memory/test_vector_memory_adapter_extra.py --speed=medium

- Exercise ChromaDB paths:
  poetry install --with dev --extras chromadb
  export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
  poetry run devsynth run-tests --target integration-tests --speed=medium

- Try FAISS-based retrieval locally (medium/slow recommended):
  poetry install --with dev --extras retrieval
  export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
  poetry run devsynth run-tests --speed=slow --segment --segment-size 50

## Notes
- Keep resource flags off in CI unless a job explicitly enables them.
- Use @pytest.mark.requires_resource("<name>") in tests to gate optional integrations.
- Verify speed markers with:
  poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
