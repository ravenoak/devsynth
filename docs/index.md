---

title: DevSynth Documentation
date: 2025-07-07
version: "0.1.0a1"
tags:
- documentation
- overview
- index

status: published
author: DevSynth Team
last_reviewed: "2025-08-02"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; DevSynth Documentation
</div>

# DevSynth Documentation

![Test Coverage](coverage.svg)

Welcome to the DevSynth documentation! This site provides comprehensive guides, references, and policies for users and contributors. Use the navigation to explore getting started guides, user and developer documentation, architecture, technical references, specifications, and the project roadmap.

## Quick Links

- [Quick Start Guide](getting_started/quick_start_guide.md)
- [User Guide](user_guides/user_guide.md)
- [Developer Guides](developer_guides/contributing.md)
- [Architecture Overview](architecture/overview.md)
- [Recursive EDRR Architecture](architecture/recursive_edrr_architecture.md)
- [API Reference](technical_reference/api_reference/index.md)
- [Project Analysis](analysis/executive_summary.md)
- [Implementation Status](implementation/feature_status_matrix.md)
- [Project Roadmap](roadmap/CONSOLIDATED_ROADMAP.md)
- [Glossary](glossary.md)

## Complete Documentation Index

For a comprehensive listing of all documentation files, see the [Documentation Index](documentation_index.md) (automatically generated from all 578+ documentation files).


## Project Policies

See [Documentation Policies](policies/documentation_policies.md) and [Contributing Guide](developer_guides/contributing.md) for standards and review processes.

## SDLC Policies and Documentation Framework

DevSynth is governed by a comprehensive set of SDLC policies and documentation artifacts designed for both human and agentic contributors. These policies ensure structure, boundaries, and direction across all SDLC phases, supporting multi-agent collaboration, compliance, safety, and productivity. Key elements include:

- **Requirements Documentation**: Product Requirements Document (PRD), domain glossary, and requirements traceability matrix ([requirements_traceability.md](requirements_traceability.md))
- **Design Documentation**: Architecture specs, design principles, API/data schemas, and security design ([architecture/overview.md](architecture/overview.md))
- **Development Protocols**: Contribution guide, code style, module ownership, secure coding, and peer review ([developer_guides/contributing.md](developer_guides/contributing.md), [developer_guides/code_style.md](developer_guides/code_style.md))
- **Testing Strategy**: Test plan, unit/integration/property-based/regression tests, CI coverage, and testing documentation ([developer_guides/testing.md](developer_guides/testing.md))
- **Deployment & Maintenance**: Infrastructure-as-code, deployment workflow, access control, observability, rollback, and maintenance plan ([policies/deployment.md](policies/deployment.md), [policies/maintenance.md](policies/maintenance.md))
- **Repository Structure & Metadata**: Predictable directory layout, file/symbol annotations, metadata tags, and an automated knowledge base for agentic retrieval ([policies/documentation_policies.md](policies/documentation_policies.md))


For a detailed rationale and best practices for agentic LLM projects, see [SDLC Policies and Repository Artifacts for Agentic LLM Projects](policies/sdlc_policies_for_agentic_llm_projects.md).

## Documentation Navigation

The documentation is organized for clarity and systematic access. For detailed structure information, see the [Repository Structure Guide](repo_structure.md) and [Documentation Policies](policies/documentation_policies.md).


The [mkdocs.yml](../mkdocs.yml) file provides a navigable structure for all documentation. The [Repository Structure](repo_structure.md) document provides a comprehensive map of the repository for both human and agentic contributors.

## Documentation Quality & Continuous Improvement

- All requirements, code, and tests are linked via the [Requirements Traceability Matrix](requirements_traceability.md)
- Documentation, code, and tests are kept in sync through regular audits, metadata tagging, and automated CI/CD
- Changelog and semantic versioning ensure all changes are tracked ([../CHANGELOG.md](../CHANGELOG.md))
- Documentation review, testing, and style policies are enforced ([policies/documentation_policies.md](policies/documentation_policies.md))


## Current Limitations

Several capabilities remain experimental. WSDE collaboration, dialectical reasoning,
and automated EDRR management are only partially implemented and disabled by
default in `config/default.yml`. Generation features often need manual oversight.
See the [Implementation Status](implementation/feature_status_matrix.md) for the
latest progress.

---

For more information, visit the [DevSynth GitHub repository](https://github.com/ravenoak/devsynth).
