---
title: "DevSynth"
date: "2025-05-20"
version: "1.0.0"
tags:
  - "devsynth"
  - "overview"
  - "documentation"
  - "readme"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-05-20"
---

# DevSynth

DevSynth is an agentic software engineering platform that leverages LLMs, advanced memory systems, and dialectical reasoning to automate and enhance the software development lifecycle. The system is designed for extensibility, resilience, and traceability, supporting both autonomous and collaborative workflows.

## Key Features
- Modular, hexagonal architecture for extensibility and testability
- Unified memory system with ChromaDB, SQLite, and JSON backends
- Agent system powered by LangGraph for orchestrated workflows
- Advanced code analysis using NetworkX
- Provider abstraction for OpenAI, LM Studio, and more
- Comprehensive SDLC policy corpus for agentic and human contributors
- Automated documentation, testing, and CI/CD pipelines
- **Adaptive Project Ingestion**: Dynamically understands and adapts to diverse project structures (including monorepos, multi-language projects, and custom layouts) using a `manifest.yaml` file and an "Expand, Differentiate, Refine, Retrospect" process to keep its knowledge current.

## SDLC Policies and Documentation Framework

DevSynth is governed by a comprehensive set of SDLC policies and documentation artifacts designed for both human and agentic contributors. These policies ensure structure, boundaries, and direction across all SDLC phases, supporting multi-agent collaboration, compliance, safety, and productivity. Key elements include:

- **Project Manifest (`manifest.yaml`)**: A user-configurable file at the project root, defined by `docs/manifest_schema.json`, detailing the project's specific structure (e.g., monorepo, submodules, custom paths), components, and primary language. This is the cornerstone of DevSynth's "Expand, Differentiate, Refine, Retrospect" ingestion and adaptation mechanism.
- **Requirements Documentation**: Product Requirements Document (PRD), domain glossary, and requirements traceability matrix ([docs/requirements_traceability.md](docs/requirements_traceability.md))
- **Design Documentation**: Architecture specs, design principles, API/data schemas, and security design ([docs/architecture/overview.md](docs/architecture/overview.md))
- **Development Protocols**: Contribution guide, code style, module ownership, secure coding, and peer review ([docs/developer_guides/contributing.md](docs/developer_guides/contributing.md), [docs/developer_guides/code_style.md](docs/developer_guides/code_style.md))
- **Testing Strategy**: Test plan, unit/integration/property-based/regression tests, CI coverage, and testing documentation ([docs/developer_guides/testing.md](docs/developer_guides/testing.md))
- **Deployment & Maintenance**: Infrastructure-as-code, deployment workflow, access control, observability, rollback, and maintenance plan ([docs/policies/deployment.md](docs/policies/deployment.md), [docs/policies/maintenance.md](docs/policies/maintenance.md))
- **Repository Structure & Metadata**: Predictable directory layout, file/symbol annotations, metadata tags, a `manifest.yaml` for project structure definition, and an automated knowledge base for agentic retrieval ([docs/roadmap/documentation_plan.md](docs/roadmap/documentation_plan.md), `manifest.yaml`, `docs/manifest_schema.json`)

## Documentation

Full documentation is available in the [docs/](docs/index.md) directory and online at [DevSynth Docs](docs/index.md). Key sections:
- [Quick Start Guide](docs/quick_start_guide.md)
- [User Guide](docs/user_guides/user_guide.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Memory System](docs/architecture/memory_system.md)
- [Requirements Traceability Matrix](docs/requirements_traceability.md)
- [SDLC Policies](docs/policies/README.md)

## Documentation Restructuring & Navigation

The documentation corpus is organized for clarity and agentic navigation, following the [Documentation Restructuring Plan](docs/roadmap/documentation_plan.md). Key directories:

- `getting_started/` – Quick start, installation, and basic usage
- `user_guides/` – User guide, CLI reference, configuration
- `developer_guides/` – Contributing, development setup, testing, code style
- `architecture/` – System, agent, memory, and reasoning architecture
- `technical_reference/` – API, error handling, performance
- `specifications/` – Current and archived specifications
- `roadmap/` – Roadmaps and improvement plans
- `policies/` – SDLC, security, testing, and maintenance policies

The [mkdocs.yml](mkdocs.yml) file provides a navigable structure for all documentation.

## Repository Structure
- `manifest.yaml` – Defines project structure and artifacts for DevSynth ingestion.
- `docs/manifest_schema.json` – The JSON schema for `manifest.yaml`.
- `src/` – Source code (modular, hexagonal architecture)
- `tests/` – Unit, integration, and behavior-driven tests
- `docs/` – User, developer, architecture, and policy documentation
- `policies/` – SDLC, security, and cross-cutting policies
- `roadmap/` – Roadmaps and improvement plans
- `specifications/` – Current and archived specifications
- `deployment/` – Deployment scripts and configuration

## Traceability & Continuous Improvement

- All requirements, code, and tests are linked via the [Requirements Traceability Matrix](docs/requirements_traceability.md)
- Documentation, code, and tests are kept in sync through regular audits, metadata tagging, and automated CI/CD
- Changelog and semantic versioning ensure all changes are tracked ([CHANGELOG.md](CHANGELOG.md))

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/developer_guides/contributing.md](docs/developer_guides/contributing.md) for guidelines, code style, and development setup.

## License
DevSynth is released under the MIT License. See [LICENSE.md](LICENSE.md) for details.

---

_Last updated: May 2025_
