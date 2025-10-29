---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-09-21"
status: review
tags:
  - implementation
  - pseudocode
  - api
title: Agent API Pseudocode
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Agent API Pseudocode
</div>

# Agent API Pseudocode

## Overview
The Agent API stub exposes DevSynth's CLI workflows through FastAPI so programmatic clients can issue the same commands as the interactive bridge. The original router relies on the `APIBridge` helper to capture CLI output, forwards requests to the existing command modules, and shares a FastAPI router plus `AgentAPI` convenience wrapper for direct invocation.【F:src/devsynth/interface/agentapi.py†L32-L204】【F:src/devsynth/interface/agentapi.py†L461-L589】【F:src/devsynth/interface/agentapi.py†L588-L955】

The enhanced router builds on the same surface area but wraps mutable state in typed data-transfer objects. A lightweight `AgentAPIState` tracks latest messages, rate-limiter buckets, and metrics so tests can inject clean fixtures without touching globals.【F:src/devsynth/interface/agentapi_enhanced.py†L32-L118】【F:src/devsynth/interface/agentapi_enhanced.py†L208-L246】

## Key components
- **`APIBridge`** implements the `UXBridge` contract, capturing messages and scripted answers so HTTP requests can reuse CLI flows without additional prompts.【F:src/devsynth/interface/agentapi.py†L66-L215】
- **`AgentAPI`** offers a thin wrapper that calls the CLI modules (`init_cmd`, `gather_cmd`, `run_pipeline_cmd`, etc.) while persisting the latest messages for subsequent `/status` calls.【F:src/devsynth/interface/agentapi.py†L461-L589】
- **`router` and `app`** expose typed FastAPI endpoints and error handlers; `devsynth.api` mounts the router under `/api`, configures metrics, and enforces optional bearer-token authentication.【F:src/devsynth/interface/agentapi.py†L588-L955】【F:src/devsynth/api.py†L42-L100】
- **Typed state and rate limiting** wrap mutable data in `AgentAPIState`, `MetricsTracker`, and `RateLimiterState`, ensuring arithmetic and dictionary access operate on concrete types while exposing helpers to persist workflow messages.【F:src/devsynth/interface/agentapi_enhanced.py†L32-L205】
- **Structured error responses** are emitted through `_error_detail` and module-level exception handlers so every HTTP failure serialises the shared `ErrorResponse` schema.【F:src/devsynth/interface/agentapi_enhanced.py†L208-L287】【F:src/devsynth/interface/agentapi_enhanced.py†L1195-L1234】

## Example: wiring the stub for tests or contracts
```python
import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import devsynth.interface.agentapi as agentapi

cli_stub = ModuleType("devsynth.application.cli")
cli_stub.init_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result("init"))
cli_stub.gather_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result(
    f"{kwargs['bridge'].ask_question('g')},{kwargs['bridge'].ask_question('c')},{kwargs['bridge'].ask_question('p')}"
))
cli_stub.run_pipeline_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result(f"run:{kwargs['target']}"))
cli_stub.spec_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result(f"spec:{kwargs['requirements_file']}"))
cli_stub.test_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result(f"test:{kwargs['spec_file']}"))
cli_stub.code_cmd = MagicMock(side_effect=lambda **kwargs: kwargs["bridge"].display_result("code"))

sys.modules["devsynth.application.cli"] = cli_stub
importlib.reload(agentapi)

client = TestClient(agentapi.app)
response = client.post("/init", json={"path": "proj"})
assert response.json() == {"messages": ["init"]}
```
The real contract tests add doctor and EDRR cycle stubs, reload the module to pick up the monkeypatched dependencies, and assert that each route responds with the captured bridge messages.【F:tests/integration/general/test_agent_api.py†L1-L124】【F:tests/integration/general/test_agent_api.py†L126-L183】

## Contract coverage
- **Integration tests** validate the FastAPI stub end-to-end by substituting CLI modules and exercising every route, ensuring the documented flow stays in sync with the router implementation.【F:tests/integration/general/test_agent_api.py†L1-L231】 The suite now adds enhanced-router checks for metrics accumulation, rate-limit breaches, and typed error payloads.【F:tests/integration/general/test_agent_api.py†L185-L231】
- **Unit tests** cover token enforcement, metrics exposure, and direct `AgentAPI` usage so the higher-level wrapper and shared `app` remain stable.【F:tests/unit/interface/test_api_endpoints.py†L1-L213】 Additional fast unit tests assert the enhanced state container and error helpers remain strongly typed.【F:tests/unit/interface/test_api_endpoints.py†L214-L240】
- **BDD scenario** keeps the specification aligned by asserting that the stub triggers the CLI bridge, mirroring the behavioral contracts referenced in the issue tracker.【F:tests/behavior/steps/test_api_stub_steps.py†L1-L38】

## Notes
`docs/tasks.md` item 26.6 now points to these tests and marks the document as review-ready. Progress for the related tracking issue lives in [`issues/agent-api-stub-usage.md`](../../issues/agent-api-stub-usage.md).
