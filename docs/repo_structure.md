---

title: DevSynth Repository Structure
date: 2025-07-08
version: "0.1.0a1"
tags:
- documentation
status: published
author: DevSynth Team
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; DevSynth Repository Structure
</div>

# DevSynth Repository Structure

This document provides a comprehensive map of the DevSynth repository structure, serving as a navigation guide for both human and agentic contributors. It outlines the organization of the codebase, tests, documentation, and related artifacts.

## Directory Structure Overview

```text
devsynth/
├── CHANGELOG.md              # Project changelog with version history
├── CONTRIBUTING.md           # Contribution guidelines
├── README.md                 # Project overview and documentation
├── mkdocs.yml                # MkDocs configuration for documentation
├── poetry.lock               # Poetry dependencies lock file
├── pyproject.toml            # Project configuration and dependencies
├── docs/                     # Documentation directory
├── scripts/                  # Utility scripts
├── src/                      # Source code
└── tests/                    # Tests directory
```

## Source Code Structure (`src/devsynth/`)

The source code follows a hexagonal architecture pattern, separating core domain logic from external adapters and application services:

```text
src/devsynth/
├── __init__.py               # Package initialization
├── __main__.py               # Entry point
├── cli.py                    # Command-line interface
├── exceptions.py             # Exception definitions
├── fallback.py               # Error handling and fallback mechanisms
├── logging_setup.py          # Logging configuration
├── adapters/                 # External adapters (hexagonal architecture)
│   ├── __init__.py
│   ├── cli.py                # CLI adapter
│   ├── kuzu_memory_store.py      # Kuzu memory store adapter
│   ├── json_file_store.py    # JSON file store adapter
│   └── provider_system.py    # Provider system (OpenAI, LM Studio)
├── application/              # Application services
│   ├── __init__.py
│   ├── orchestration/        # Workflow orchestration
│   ├── code_analysis/        # Code analysis module
│   └── cli/                  # CLI application services
├── config/                   # Configuration handling
│   └── __init__.py
├── domain/                   # Domain model (core business logic)
│   ├── __init__.py
│   ├── interfaces/           # Domain interfaces
│   └── models/               # Domain models
└── ports/                    # Ports (hexagonal architecture)
    ├── __init__.py
    ├── memory_port.py        # Memory system port
    └── memory_store.py       # Memory store interface
```

## Tests Structure (`tests/`)

```text
tests/
├── conftest.py               # Shared test fixtures
├── README.md                 # Testing documentation
├── behavior/                 # Behavior-driven (BDD) tests
│   ├── conftest.py           # BDD test fixtures
│   ├── *.feature             # Feature files in Gherkin syntax
│   ├── steps/                # Step definitions for BDD tests
│   └── test_*.py             # Test implementations
├── integration/              # Integration tests
└── unit/                     # Unit tests
```

## Documentation Structure (`docs/`)

Following the [Documentation Policies](policies/documentation_policies.md), the documentation is organized as:

```text
docs/
├── index.md                       # Documentation home
├── requirements_traceability.md   # Requirements traceability matrix
├── getting_started/               # Getting started guides
├── user_guides/                   # User-focused documentation
├── developer_guides/              # Developer-focused documentation
├── architecture/                  # Architecture documentation
│   ├── overview.md                # Architecture overview
│   ├── agent_system.md            # Agent system architecture
│   ├── memory_system.md           # Memory system architecture
│   ├── dialectical_reasoning.md   # Dialectical reasoning system
│   └── hexagonal_architecture.md  # Hexagonal architecture details
├── technical_reference/           # Technical reference
├── specifications/                # Project specifications
├── roadmap/                       # Project roadmap
└── policies/                      # SDLC policies
```

## Key Files and Their Purpose

### Core Implementation Files

- **`src/devsynth/__main__.py`**: Main entry point for the application
- **`src/devsynth/adapters/provider_system.py`**: Provider abstraction for LLM integration (OpenAI, LM Studio)
- **`src/devsynth/adapters/kuzu_memory_store.py`**: Kuzu-based memory store implementation
- **`src/devsynth/ports/memory_store.py`**: Memory store interface definition
- **`src/devsynth/ports/memory_port.py`**: Memory system port for application interaction


### Documentation Files

- **`docs/index.md`**: Documentation home and overview
- **`docs/architecture/overview.md`**: System architecture overview
- **`docs/architecture/memory_system.md`**: Memory system architecture
- **`docs/requirements_traceability.md`**: Requirements traceability matrix


### Testing Files

- **`tests/behavior/conftest.py`**: Test fixtures for isolation and cleanliness
- **`tests/unit/test_kuzu_store.py`**: Kuzu memory store tests


## File and Symbol Naming Conventions

DevSynth follows these naming conventions:

- **Files**: Snake case (`memory_store.py`, `test_kuzu_store.py`)
- **Classes**: Pascal case (`KuzuMemoryStore`, `MemoryPort`)
- **Functions/Methods**: Snake case (`store_memory`, `get_from_context`)
- **Constants**: Upper snake case (`DEFAULT_CONFIG_PATH`)
- **Tests**: Prefixed with `test_` (`test_kuzu_store.py`)
- **BDD Features**: Descriptive naming (`additional_storage_backends.feature`)


## Metadata Tags and Traceability

- **Requirements**: Tagged with unique IDs (e.g., `REQ-001`) in the Requirements Traceability Matrix
- **Code**: Comments reference requirement IDs where applicable
- **Tests**: Test names and docstrings reference the requirements they validate


## Version Control Standards

- **Branches**: Feature branches from `main`, named as `feature/feature-name`
- **Commits**: Descriptive messages with requirement IDs where applicable
- **Pull Requests**: Reference requirement IDs and include description of changes


## Getting Started with the Repository

New contributors should:

1. Read the [Contributing Guide](developer_guides/contributing.md)
2. Set up the development environment following [Development Setup](developer_guides/development_setup.md)
3. Familiarize with the [Architecture Overview](architecture/overview.md)
4. Follow the coding standards in [Code Style Guide](developer_guides/code_style.md)


---

_Last updated: July 8, 2025_
## Implementation Status

This reference is **implemented** and reflects the current repository layout.
