---
title: "DevSynth Changelog"
date: "2025-08-16"
version: "0.1.0-alpha.1"
tags:
  - "devsynth"
  - "changelog"
  - "version history"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-16"
---

# Changelog

All notable changes to the DevSynth project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

DevSynth's pre-release milestones in the `0.1.x` range lead up to the first
stable release. Version `0.1.0-alpha.1` marks the project's initial published
milestone.

> **Pre-release:** The `0.1.0-alpha.1` tag has not been created. Details may change until the release is tagged.

## [0.1.0-alpha.1] - 2025-08-16

Initial alpha release delivering a modular architecture, unified memory backends, and a LangGraph-powered agent system.

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
- Stabilized pre-release references to maintain version `0.1.0-alpha.1` across configuration and documentation
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

### Dialectical audit
- Generated `dialectical_audit.log`; see Issue 125 for unresolved questions.

### Known P1 Issues and Test Gaps

- `poetry run python scripts/verify_test_markers.py` fails due to pytest collection errors in several test modules (e.g., `tests/performance/test_api_benchmarks.py`, `tests/behavior/test_agentapi.py`).
- `poetry run task release:prep` reports `Command not found: task`, preventing release artifact preparation.
