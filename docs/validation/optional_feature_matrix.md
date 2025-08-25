---
title: Optional Feature Validation Matrix
summary: Documentation of which optional extras were exercised, with commands, env vars, and outcomes.
status: draft
last_updated: 2025-08-24
---

# Optional Feature Validation Matrix

This matrix tracks which optional extras were validated for the 0.1.0a1 stabilization effort, with reproducible commands and expected environment variables. Update this table as validations are run locally or in CI. Link to the relevant tests where applicable.

> Note: Prefer stubs/mocks over live provider/backend calls in CI. Tests should be deterministic and respect the `no_network` marker when appropriate.

## How to Use

1. Install with the desired extras and dev tools. Examples:
   - Minimal: `poetry install --with dev --extras minimal`
   - LLM/Memory/API/WebUI: `poetry install --with dev --extras llm --extras memory --extras api --extras webui`
   - GUI: `poetry install --with dev --extras gui`
2. Run the corresponding tests or smoke checks as documented below.
3. Record pass/fail status and add links to tests and CI logs when available.

## Validation Table (Template)

| Extra       | Packages             | Commands                                                                                   | Env Vars                                 | Status | Notes/Links                                  |
|-------------|----------------------|--------------------------------------------------------------------------------------------|-------------------------------------------|--------|----------------------------------------------|
| retrieval   | kuzu, faiss-cpu      | `poetry run pytest -m "not slow and not gui" tests/integration/retrieval -q`              | n/a                                       | PASS   | See testing overview: [Testing Guide](../developer_guides/testing.md) |
| chromadb    | chromadb, tiktoken   | `poetry run pytest -m "not slow and not gui" tests/integration/retrieval -k chroma -q`    | n/a                                       | PASS   | [Retrieval extras](../specifications/testing_infrastructure.md) |
| lmstudio    | lmstudio             | smoke import only; provider selection mocked                                               | LM_STUDIO_ENDPOINT (optional)             | PASS   | [Provider system](../architecture/provider_system.md) |
| memory      | tinydb, duckdb, lmdb | `poetry run pytest tests/integration/memory -m "not slow and not gui" -q`                 | n/a                                       | PASS   | See `tests/integration/memory/test_cross_store_sync.py` |
| llm         | tiktoken, httpx      | `poetry run pytest tests/unit/application/llm -m "not slow and not gui" -q`               | DEVSYNTH_PROVIDER (default openai)        | PASS   | [Provider system](../architecture/provider_system.md) (no-network stubs) |
| gpu         | torch + CUDA libs    | smoke import (local only)                                                                  | CUDA related as applicable                | SKIPPED (CI) / PASS (local) | Local-only smoke; excluded in CI |
| offline     | transformers         | `poetry run pytest -k offline -m "not slow and not gui" -q`                               | n/a                                       | PASS   | [Hermetic testing](../developer_guides/hermetic_testing.md) |
| api         | fastapi, prometheus  | `poetry run pytest tests/unit/server -k api -q` and minimal TestClient startup            | n/a                                       | PASS   | metrics endpoint returns 200                  |
| webui       | streamlit            | smoke import and `mvuu-dashboard --no-run`                                                 | n/a                                       | PASS   | CLI entry-point loads                         |
| gui         | dearpygui            | `poetry run pytest -m gui -q` (local)                                                      | n/a                                       | SKIPPED (CI) / PASS (local) | See [GUI testing](../testing/gui_testing.md)               |

Update this matrix as validations complete. For CI, attach artifacts (HTML report, coverage) and link to workflow runs.
