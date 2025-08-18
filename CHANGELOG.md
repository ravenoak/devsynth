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

## [0.1.0-alpha.1] - 2025-08-16

### Added
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

### Dialectical audit
- Generated `dialectical_audit.log`; see Issue 125 for unresolved questions.
