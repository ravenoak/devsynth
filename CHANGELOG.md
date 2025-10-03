---
title: "DevSynth Changelog"
date: "2025-08-23"
version: "0.1.0a1"
tags:
  - "devsynth"
  - "changelog"
  - "version history"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-09-13"
---

# Changelog

All notable changes to the DevSynth project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

DevSynth's pre-release milestones in the `0.1.x` range lead up to the first
stable release. Version `0.1.0a1` marks the project's initial published
milestone.

## [Unreleased]

### Added
- Autoresearch overlays for the MVUU dashboard can now be toggled via
  `mvuu-dashboard --research-overlays`, emitting signed telemetry consumed by
  Streamlit overlays and documented in `docs/user_guides/mvuu_dashboard.md`.

### Changed
- Lifted the repo-wide strict typing guard to cover `src/devsynth`, routing `task mypy:strict` through `poetry run mypy --strict src/devsynth`, leaning on the mypy configuration smoke tests for regression detection, and archiving the clean transcript at `diagnostics/mypy_strict_src_devsynth_20251003T172126Z.txt`; the updated strictness note cross-links the enforcement details for ongoing review.【F:Taskfile.yml†L143-L147】【F:tests/unit/general/test_mypy_config.py†L1-L70】【F:diagnostics/mypy_strict_src_devsynth_20251003T172126Z.txt†L1-L1】【F:docs/typing/strictness.md†L9-L12】
- Enforced a dedicated strict typing guard for the memory stack by removing the override exemption, wiring `task mypy:strict` to archive the new transcript, and extending the guardrail runner; diagnostics live at `diagnostics/mypy_strict_application_memory_20251002T220045Z.txt` for ongoing verification.【F:pyproject.toml†L321-L333】【F:Taskfile.yml†L143-L152】【F:scripts/run_guardrails_suite.py†L41-L64】【F:docs/typing/strictness.md†L5-L27】【F:diagnostics/mypy_strict_application_memory_20251002T220045Z.txt†L1-L200】
- Brought the Agent API and requirements service stack under the strict typing gate, removing the Phase‑5 override and archiving fresh mypy/test diagnostics as release evidence.【F:docs/typing/strictness.md†L18-L21】【F:docs/typing/strictness.md†L130-L136】【F:diagnostics/mypy_strict_agentapi_requirements_20250929T162537Z.txt†L1-L106】【F:diagnostics/devsynth_run_tests_fast_medium_api_strict_20250929T163210Z.txt†L1-L20】
- Removed legacy strict-typing overrides for adapters and application workflows after strict sweeps, consolidating the `pyproject.toml` configuration and archiving diagnostics for each batch.【F:pyproject.toml†L285-L309】【F:docs/typing/strictness.md†L15-L23】【F:diagnostics/mypy_strict_adapters_20250930T201103Z.txt†L1-L2】【F:diagnostics/mypy_strict_application_orchestration_20250930T201117Z.txt†L1-L2】【F:diagnostics/mypy_strict_application_prompts_20250930T201132Z.txt†L1-L2】
- Updated release readiness documentation to reinforce the ≥90 % coverage gate, strict mypy verification via `poetry run task mypy:strict`, and fast+medium artifact archival workflows, referencing the latest diagnostics evidence.
- Realigned the FastAPI 0.116.x pin with Starlette 0.47.3 after reviewing the
  upstream release notes; the `sitecustomize` shim continues to patch
  `WebSocketDenialResponse` until the Python 3.12 TestClient MRO fix lands
  natively (tracked in
  `issues/run-tests-smoke-fast-fastapi-starlette-mro.md`).
- Recorded the 2025-09-30 strict and fast+medium runs for the CLI and collaboration stacks after pruning their overrides, capturing the outstanding mypy violations and the Pydantic recursion loop blocking regression coverage.【F:docs/typing/strictness.md†L18-L21】【F:docs/typing/strictness.md†L66-L79】【F:diagnostics/mypy_strict_cli_collaboration_20250930T013408Z.txt†L1-L200】【F:diagnostics/devsynth_run_tests_fast_medium_20250930T014103Z.txt†L1-L200】

> This changelog entry for 0.1.0a1 is now frozen for the tag.

## [0.1.0a1] - 2025-08-23

Initial alpha release delivering a modular architecture, unified memory backends, and a LangGraph-powered agent system.

### Highlights
- Aligned versioning with PEP 440 and standardized `0.1.0a1` across code and docs.
- Release automation stabilized; `task release:prep` runs locally and in CI (dry-run).
- Test runner stabilized with safe defaults and deterministic provider stubs; CLI entrypoint resolution fixed.
- Pre-commit/dev toolchain reliability improved; circular import in reasoning fixed.
- Verification scripts for markers and release state streamlined and documented.

### Breaking Changes
- CLI command renames:
  - `adaptive` → `refactor`
  - `analyze` → `inspect`
  - `run` → `run-pipeline`
  - `replay` → `retrace`
  Update any scripts or automation that reference old commands.

### Added
- Documented acceptance criteria for MVU command execution with linked BDD feature coverage.
- Modular, hexagonal architecture
- Unified memory system with multiple backends
- Agent system powered by LangGraph
- Advanced code analysis using NetworkX
- Provider abstraction for LLM services
- Comprehensive SDLC policy corpus
- Automated documentation and testing
- Recursive EDRR framework implementation
- Documentation cleansing and organization
- Behavior-driven tests for the EDRR coordinator
- Basic security utilities for authentication, authorization, and input sanitization
- Doctor command for configuration validation
- Anthropic API support and deterministic offline provider implementation
- MVUU engine for tracking Minimum Viable Utility Units
- Atomic-Rewrite workflow for granular commit generation

- Documentation cross-references linking issues and BDD features for Code Analysis, Complete Sprint-EDRR integration, Complete memory system integration, Critical recommendations follow-up, Enhance retry mechanism, Expand test generation capabilities, Finalize WSDE/EDRR workflow logic, Finalize dialectical reasoning, Improve deployment automation, Integrate dialectical audit into CI, Multi-Agent Collaboration, Multi-Layered Memory System, Resolve pytest-xdist assertion errors, Review and Reprioritize Open Issues, and User Authentication.

### Changed
- Moved development documents to appropriate locations in the docs/ directory
- Consolidated DevSynth analysis documents
- Updated cross-references in documentation
- Renamed CLI commands: `adaptive`→`refactor`, `analyze`→`inspect`, `run`→`run-pipeline`, `replay`→`retrace`
- Synchronized feature status reports with latest implementation
- Stabilized pre-release references to maintain version `0.1.0a1` across configuration and documentation
- Updated documentation to reflect implementation of WebUI, CLI overhaul,
  hybrid memory architecture, and basic metrics system.

### Deprecated
- `scripts/alignment_check.py` and `scripts/validate_manifest.py` replaced by
  CLI commands `devsynth align` and `devsynth validate-manifest`. These scripts
  will be removed in v1.0 per the deprecation policy.

### Fixed
- Improved error handling in the EDRR coordinator
- EDRR coordinator emits sync hooks even when memory management is unavailable or flush operations fail
- Optional tiktoken dependency no longer breaks Kuzu memory initialization
- Added missing step definitions for enhanced memory scenarios
- Linked remaining alpha tasks (WebUI, Kuzu memory, WSDE collaboration, CLI ingestion) to milestone `0.1.0-alpha.1` and updated development status.
- Memory module import no longer leaves residual TinyDB state when the dependency is absent
- TinyDBMemoryAdapter converts non-JSON types (e.g., sets, datetimes) during serialization to avoid TypeError
- Seeded WSDE/EDRR simulation for deterministic convergence and added sentinel speed test

### Dialectical audit
- Generated `dialectical_audit.log`; see Issue 125 for unresolved questions.

### Known P1 Issues and Test Gaps
- Some performance and GUI-related tests are gated and may be skipped in minimal CI jobs.


[0.1.0a1]: https://github.com/ravenoak/devsynth/releases/tag/v0.1.0a1
