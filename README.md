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
last_reviewed: "2025-05-30"
---

> Special note: LLMs have synthesized this project, with minimal manual editing, using a dialectical HITL methodology.

# DevSynth

DevSynth is an agentic software engineering platform that leverages LLMs, advanced memory systems, and dialectical reasoning to automate and enhance the software development lifecycle. The system is designed for extensibility, resilience, and traceability, supporting both autonomous and collaborative workflows.

## Key Features
- Modular, hexagonal architecture for extensibility and testability
- Unified memory system with ChromaDB, TinyDB, RDFLib, and JSON backends
- Agent system powered by LangGraph for orchestrated workflows
- Advanced code analysis using NetworkX
- Provider abstraction for OpenAI, LM Studio, and more
- Comprehensive SDLC policy corpus for agentic and human contributors
- Automated documentation, testing, and CI/CD pipelines
- **Worker Self-Directed Enterprise (WSDE) Model**: Sophisticated multi-agent collaboration framework with role management, dialectical reasoning, consensus building, and knowledge integration capabilities
- **Adaptive Project Ingestion**: Dynamically understands and adapts to diverse project structures (including monorepos, multi-language projects, and custom layouts) using a `.devsynth/project.yaml` file and an "Expand, Differentiate, Refine, Retrospect" (EDRR) framework to keep its knowledge current. The EDRR framework is implemented through the EDRRCoordinator but is not yet fully integrated with all system components. The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth.

## SDLC Policies and Documentation Framework

DevSynth is governed by a comprehensive set of SDLC policies and documentation artifacts designed for both human and agentic contributors. These policies ensure structure, boundaries, and direction across all SDLC phases, supporting multi-agent collaboration, compliance, safety, and productivity. Key elements include:

- **Project Configuration (`.devsynth/project.yaml`)**: A user-configurable file in the `.devsynth` directory, defined by `src/devsynth/schemas/project_schema.json`, detailing the project's shape and attributes (e.g., structure type, components, primary language). This configuration file is minimal but functional, featureful, and human-friendly. It is only present in projects that are managed by DevSynth, as the presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth. This is the cornerstone of DevSynth's "Expand, Differentiate, Refine, Retrospect" ingestion and adaptation mechanism.
- **Requirements Documentation**: Product Requirements Document (PRD), domain glossary, and requirements traceability matrix ([docs/requirements_traceability.md](docs/requirements_traceability.md))
- **Design Documentation**: Architecture specs, design principles, API/data schemas, and security design ([docs/architecture/overview.md](docs/architecture/overview.md))
- **Development Protocols**: Contribution guide, code style, module ownership, secure coding, and peer review ([docs/developer_guides/contributing.md](docs/developer_guides/contributing.md), [docs/developer_guides/code_style.md](docs/developer_guides/code_style.md))
- **Testing Strategy**: Test plan, unit/integration/property-based/regression tests, CI coverage, and testing documentation ([docs/developer_guides/testing.md](docs/developer_guides/testing.md))
- **Deployment & Maintenance**: Infrastructure-as-code, deployment workflow, access control, observability, rollback, and maintenance plan ([docs/policies/deployment.md](docs/policies/deployment.md), [docs/policies/maintenance.md](docs/policies/maintenance.md))
- **Repository Structure & Metadata**: Predictable directory layout, file/symbol annotations, metadata tags, a `.devsynth/project.yaml` for project configuration (in projects managed by DevSynth), and an automated knowledge base for agentic retrieval ([docs/roadmap/documentation_plan.md](docs/roadmap/documentation_plan.md), `.devsynth/project.yaml`, `src/devsynth/schemas/project_schema.json`)

## Documentation

Full documentation is available in the [docs/](docs/index.md) directory and online at [DevSynth Docs](docs/index.md). Key sections:
- [Quick Start Guide](docs/getting_started/quick_start_guide.md)
- [User Guide](docs/user_guides/user_guide.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Project Analysis](docs/analysis/executive_summary.md)
- [Implementation Status](docs/implementation/feature_status_matrix.md)
- [Requirements Traceability Matrix](docs/requirements_traceability.md)
- [SDLC Policies](docs/policies/index.md)

## Documentation Structure

The documentation is organized for clarity and ease of navigation, following a comprehensive structure. Key directories:

- `getting_started/` – Quick start, installation, and basic usage
- `user_guides/` – User guide, CLI reference, configuration
- `developer_guides/` – Contributing, development setup, testing, code style
- `architecture/` – System, agent, memory, and reasoning architecture
- `technical_reference/` – API, error handling, performance
- `analysis/` – Project analysis, executive summary, critical recommendations
- `implementation/` – Implementation status, feature matrix, assessments
- `specifications/` – Current and archived specifications
- `roadmap/` – Roadmaps and improvement plans
- `policies/` – SDLC, security, testing, and maintenance policies

The [Repository Structure](docs/repo_structure.md) document provides a comprehensive map of the repository for both human and agentic contributors.

## Repository Structure
- `.devsynth/project.yaml` – Configuration file describing the shape and attributes of projects managed by DevSynth. The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth.
- `docs/manifest_schema.json` – The JSON schema for `.devsynth/project.yaml`.
- `src/` – Source code (modular, hexagonal architecture)
- `tests/` – Unit, integration, and behavior-driven tests
- `docs/` – User, developer, architecture, and policy documentation
- `docs/policies/` – SDLC, security, and cross-cutting policies
- `docs/roadmap/` – Roadmaps and improvement plans
- `docs/specifications/` – Current and archived specifications
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

_Last updated: May 30, 2025_
