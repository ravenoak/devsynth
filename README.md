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

## SDLC Policies and Documentation Framework

DevSynth is governed by a comprehensive set of SDLC policies and documentation artifacts designed for both human and agentic contributors. These policies ensure structure, boundaries, and direction across all SDLC phases, supporting multi-agent collaboration, compliance, safety, and productivity. Key elements include:

- **Requirements Documentation**: Product Requirements Document (PRD), domain glossary, and requirements traceability matrix ([docs/requirements_traceability.md](docs/requirements_traceability.md))
- **Design Documentation**: Architecture specs, design principles, API/data schemas, and security design ([docs/architecture/overview.md](docs/architecture/overview.md))
- **Development Protocols**: Contribution guide, code style, module ownership, secure coding, and peer review ([docs/developer_guides/contributing.md](docs/developer_guides/contributing.md), [docs/developer_guides/code_style.md](docs/developer_guides/code_style.md))
- **Testing Strategy**: Test plan, unit/integration/property-based/regression tests, CI coverage, and testing documentation ([docs/developer_guides/testing.md](docs/developer_guides/testing.md))
- **Deployment & Maintenance**: Infrastructure-as-code, deployment workflow, access control, observability, rollback, and maintenance plan ([docs/policies/deployment.md](docs/policies/deployment.md), [docs/policies/maintenance.md](docs/policies/maintenance.md))
- **Repository Structure & Metadata**: Predictable directory layout, file/symbol annotations, metadata tags, and an automated knowledge base for agentic retrieval ([docs/roadmap/documentation_plan.md](docs/roadmap/documentation_plan.md))

For a detailed rationale and best practices for agentic LLM projects, see [SDLC Policies and Repository Artifacts for Agentic LLM Projects](docs/scratch_2.md).

## Documentation

Full documentation is available in the [docs/](docs/index.md) directory and online at [DevSynth Docs](docs/index.md). Key sections:
- [Quick Start Guide](docs/getting_started/quick_start_guide.md)
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
DevSynth is released under the MIT License. See [LICENSE](LICENSE) for details.

---

_Last updated: May 2025_
