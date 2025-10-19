# Adapter Strict Typing PR Plan

## Purpose
This roadmap decomposes the adapter strict-typing initiative into focused pull requests. Each PR targets a single adapter module, hardens its typing with Protocol/DataClass annotations, and ensures `mypy --strict` plus ≥60% unit-test coverage. The structure follows dialectical and Socratic best practices: we pose key questions, examine opposing constraints, and document decisive steps before implementation.

## Shared Guardrails (apply to every PR)
- **Socratic prompts:**
  - *What contract does this adapter expose (inputs/outputs, side effects)?*
  - *Which types remain uncertain, and what evidence resolves them?*
  - *How do we prove the adapter behaves under error conditions without real back-ends?*
- **Dialectical checkpoints:** capture trade-offs between precision and pragmatism (e.g., typed Protocol vs. runtime ABC) in code comments or PR notes when decisions affect downstream callers.
- **Implementation checklist:**
  1. Introduce typed DTOs/Protocols for external interactions and ensure serialization helpers use explicit schemas.
  2. Replace `Any` and implicit unions with concrete types (TypedDict, dataclasses, enums) and tighten exception flows.
  3. Add `tests/unit/adapters/test_<module>.py` cases covering happy-path request shaping, serialization round-trips, and representative error handling using fakes or fixtures; gate optional resources via `@pytest.mark.requires_resource`.
  4. Run `poetry run mypy --strict <module>` until clean, then execute `poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --cov-report=term` and confirm module-specific coverage ≥60% (use coverage JSON helpers if needed).
  5. Remove the module from the adapter override block in `pyproject.toml` and append evidence to `docs/typing/strictness.md` plus `docs/tasks.md §29.4`.

## Proposed PR Sequence

### PR 1 – `devsynth.adapters.chromadb_memory_store`
- **Focus questions:** How do query/update payloads translate into ChromaDB calls, and which vector shapes are supported? Which fallback paths fire when ChromaDB is unavailable?
- **Key tasks:**
  - Define Protocol(s) for the subset of ChromaDB client features used (e.g., `add`, `query`).
  - Wrap request/response payloads in dataclasses with explicit tensor/metadata typing.
  - Expand unit tests with fixture-based fake client capturing serialization plus error injection (timeouts, missing collection).
  - After strict success, drop override and update docs.

### PR 2 – `devsynth.adapters.cli.typer_adapter`
- **Focus questions:** What CLI command metadata must remain dynamically typed, and which pieces can be formalized? How do we simulate Typer callbacks without invoking the real CLI?
- **Key tasks:**
  - Introduce Protocols for command registries and callback signatures.
  - Type annotate CLI context objects and serialization of CLI configuration/state.
  - Unit tests using Typer’s testing utilities or lightweight fakes to cover option serialization and error reporting.
  - Remove override and document evidence.

### PR 3 – `devsynth.adapters.github_project`
- **Focus questions:** Which GitHub API surfaces are exercised, and how can we emulate responses without network calls? How do we enforce typed pagination and error envelopes?
- **Key tasks:**
  - Create typed DTOs for repository/project payloads and error structures.
  - Implement Protocol for the GitHub client stub used by the adapter.
  - Unit tests that mock responses for serialization, request shaping, and API error handling (e.g., rate limits).
  - Remove override and update docs.

### PR 4 – `devsynth.adapters.jira_adapter`
- **Focus questions:** What typed fields are essential for Jira issues/transitions, and how do we express optional workflow metadata? How do we simulate authentication failures or schema mismatches?
- **Key tasks:**
  - Dataclasses for Jira issue payloads, transitions, and errors with precise optionality.
  - Protocol for the Jira client wrapper capturing methods invoked.
  - Unit tests covering serialization to/from Jira JSON, request shaping for issue creation/update, and error translation scenarios.
  - Remove override and update docs.

### PR 5 – `devsynth.adapters.kuzu_memory_store`
- **Focus questions:** How are graph/query requests modeled, and what typed structures describe result sets? How do we isolate the adapter from the real Kùzu driver?
- **Key tasks:**
  - Define typed query/request DTOs and Protocol(s) for the minimal database interface.
  - Annotate cursor/result iterables with typed records (NamedTuple or dataclass) and error handling.
  - Unit tests using fake cursor objects to validate serialization, parameter binding, and failure paths (invalid query, connection error).
  - Remove override and update docs.

### PR 6 – `devsynth.adapters.llm.llm_adapter`
- **Focus questions:** Which message schemas and tool-call payloads need codified dataclasses? How are streaming responses differentiated from batch completions? What error envelopes exist for provider failures?
- **Key tasks:**
  - Introduce Protocols for model providers with typed request/response dataclasses (prompt parts, tool calls, metadata).
  - Ensure serialization helpers enforce schema conversions and raise typed exceptions.
  - Unit tests with fake provider covering prompt serialization, streaming iteration, and provider error translation.
  - Remove override and update docs.

### PR 7 – `devsynth.adapters.llm.mock_llm_adapter`
- **Focus questions:** How should the mock adhere to the real adapter’s Protocol to remain a drop-in replacement? Which fixtures drive deterministic outputs?
- **Key tasks:**
  - Align mock adapter with Protocols from PR 6, annotating stub responses.
  - Add tests verifying serialization compatibility and intentional error injections for edge cases.
  - Remove override and update docs.

### PR 8 – `devsynth.adapters.memory.chroma_db_adapter`
- **Focus questions:** How does this higher-level memory adapter wrap the ChromaDB store, and what typed contracts exist between layers? Which fallback or eviction paths need coverage?
- **Key tasks:**
  - Type annotated DTOs for memory records and protocol alignment with the lower-level store.
  - Tests combining fake store interactions for serialization and error cascades.
  - Remove override and update docs.

### PR 9 – `devsynth.adapters.memory.kuzu_adapter`
- **Focus questions:** How do graph operations map onto typed nodes/edges, and where are conversions performed? What errors surface from schema mismatches?
- **Key tasks:**
  - Dataclasses for memory graph entities and typed query builders.
  - Tests using fake driver verifying serialization, request shaping, and schema errors.
  - Remove override and update docs.

### PR 10 – `devsynth.adapters.memory.memory_adapter`
- **Focus questions:** What generic memory API does this module expose, and how should typed Protocols unify different back-ends? Which caching layers require typed invariants?
- **Key tasks:**
  - Formalize the high-level memory adapter interface with Protocols and typed DTOs.
  - Annotate caching/serialization helpers.
  - Tests with stub back-ends focusing on request shaping and failure propagation.
  - Remove override and update docs.

### PR 11 – `devsynth.adapters.memory.sync_manager`
- **Focus questions:** How do synchronization jobs coordinate between adapters, and what typed schedule/config objects exist? Which failure paths (retry exhaustion, resource gating) require coverage?
- **Key tasks:**
  - Typed dataclasses for sync jobs, schedules, and status reports.
  - Annotate concurrency helpers and error reporting flows.
  - Tests simulating sync cycles with fake adapters verifying serialization and error handling.
  - Remove override and update docs.

### PR 12 – `devsynth.adapters.onnx_runtime_adapter`
- **Focus questions:** What typed tensor inputs/outputs are required, and how do we express ONNX session options? How do we simulate runtime failures?
- **Key tasks:**
  - Dataclasses/TypedDicts for model metadata, inputs, and outputs with numpy typing where feasible.
  - Protocol for the ONNX inference session used.
  - Unit tests using lightweight fake session verifying serialization (tensor -> numpy array) and error scenarios.
  - Remove override and update docs.

### PR 13 – `devsynth.adapters.orchestration.langgraph_adapter`
- **Focus questions:** How are workflow nodes/edges typed, and what protocol ensures compatibility with LangGraph? Which state serialization paths require validation?
- **Key tasks:**
  - Typed Protocols for graph executors and dataclasses for node definitions and execution state.
  - Tests with fake graph engine verifying serialization of workflows and failure handling (missing node, cycle detection).
  - Remove override and update docs.

### PR 14 – `devsynth.adapters.provider_system`
- **Focus questions:** How does the provider registry expose typed hooks, and what serialization occurs for provider capabilities? How do we model provider errors and availability checks?
- **Key tasks:**
  - Introduce Protocols for provider interfaces and typed capability descriptors.
  - Annotate registry mutations and serialization functions.
  - Unit tests with fake providers covering registration serialization, request shaping, and error propagation.
  - Remove override and update docs.

## Tracking and Evidence
- Use an issue or task checklist mirroring this plan to ensure overrides are removed sequentially and documentation stays synchronized.
- After each PR, append strict typing evidence to both documentation pages with citations to coverage output and test artifacts.
