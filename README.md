---
title: "DevSynth"
date: "2025-05-20"
version: "0.1.0"
tags:
  - "devsynth"
  - "overview"
  - "documentation"
  - "readme"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---

> Special note: LLMs have synthesized this project, with minimal manual editing, using a dialectical HITL methodology.

# DevSynth
![Coverage](https://img.shields.io/badge/coverage-13%25-red.svg)

DevSynth is an agentic software engineering platform that leverages LLMs, advanced memory systems, and dialectical reasoning to automate and enhance the software development lifecycle. The system is designed for extensibility, resilience, and traceability, supporting both autonomous and collaborative workflows.

**Pre-release notice:** DevSynth is still pre-0.1.0 and no package has been published on PyPI. All versions should be considered experimental. Version labels follow our [Semantic Versioning+ policy](docs/policies/semantic_versioning.md), and release milestones are tracked in [docs/roadmap/ROADMAP.md](docs/roadmap/ROADMAP.md).
## Key Features
- Modular, hexagonal architecture for extensibility and testability
- Unified memory system with Kuzu, TinyDB, RDFLib, and JSON backends
- Agent system powered by LangGraph for orchestrated workflows
- Advanced code analysis using NetworkX
- Provider abstraction for OpenAI, LM Studio, and more
- Anthropic API integration with streaming support
- Comprehensive SDLC policy corpus for agentic and human contributors
- Automated documentation, testing, and CI/CD pipelines
- Interactive `init` wizard for onboarding existing projects
- Command names updated (`refactor`, `inspect`, `run-pipeline`, `retrace`)
- Unified YAML/TOML configuration loader
- Diagnostic command `doctor`/`check` for environment validation
- CLI/WebUI bridge groundwork for future web interface
- **Worker Self-Directed Enterprise (WSDE) Model**: Sophisticated multi-agent collaboration framework with role management, dialectical reasoning, consensus building, and knowledge integration capabilities
- Dialectical reasoning hooks automatically analyze new solutions added to a WSDE team
- AST-based code transformations via `AstTransformer`
- Prompt auto-tuning for optimized LLM prompts
- **Adaptive Project Ingestion**: Dynamically understands and adapts to diverse project structures (including monorepos, multi-language projects, and custom layouts) using a `.devsynth/project.yaml` file and a fully integrated "Expand, Differentiate, Refine, Retrospect" (EDRR) framework. The `EDRRCoordinator` orchestrates this process across all system components. See [EDRR Assessment](docs/implementation/edrr_assessment.md) for details. The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth.

## SDLC Policies and Documentation Framework

DevSynth is governed by a comprehensive set of SDLC policies and documentation artifacts designed for both human and agentic contributors. These policies ensure structure, boundaries, and direction across all SDLC phases, supporting multi-agent collaboration, compliance, safety, and productivity. Key elements include:

- **`.devsynth/project.yaml`**: A user-configurable file in the `.devsynth` directory, defined by `src/devsynth/schemas/project_schema.json`, detailing the project's shape and attributes (e.g., structure type, components, primary language). This configuration file is minimal but functional, featureful, and human-friendly. It is only present in projects that are managed by DevSynth, as the presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth. This is the cornerstone of DevSynth's "Expand, Differentiate, Refine, Retrospect" ingestion and adaptation mechanism.
- **Requirements Documentation**: Product Requirements Document (PRD), domain glossary, and requirements traceability matrix ([docs/requirements_traceability.md](docs/requirements_traceability.md))
- **Design Documentation**: Architecture specs, design principles, API/data schemas, and security design ([docs/architecture/overview.md](docs/architecture/overview.md))
- **Development Protocols**: Contribution guide, code style, module ownership, secure coding, and peer review ([docs/developer_guides/contributing.md](docs/developer_guides/contributing.md), [docs/developer_guides/code_style.md](docs/developer_guides/code_style.md))
- **Testing Strategy**: Test plan, unit/integration/property-based/regression tests, CI coverage, and testing documentation ([docs/developer_guides/testing.md](docs/developer_guides/testing.md))
- **Deployment & Maintenance**: Infrastructure-as-code, deployment workflow, access control, observability, rollback, and maintenance plan ([docs/policies/deployment.md](docs/policies/deployment.md), [docs/policies/maintenance.md](docs/policies/maintenance.md), [docs/developer_guides/maintenance_strategy.md](docs/developer_guides/maintenance_strategy.md))
- **Repository Structure & Metadata**: Predictable directory layout, file/symbol annotations, metadata tags, a `.devsynth/project.yaml` for project configuration (in projects managed by DevSynth), and an automated knowledge base for agentic retrieval ([docs/specifications/documentation_plan.md](docs/specifications/documentation_plan.md), `.devsynth/project.yaml`, `src/devsynth/schemas/project_schema.json`)

## Documentation

Full documentation is available in the [docs/](docs/index.md) directory and online at [DevSynth Docs](docs/index.md). Key sections:
- [Quick Start Guide](docs/getting_started/quick_start_guide.md)
- [Installation Guide](docs/getting_started/installation.md) *(includes pipx instructions)*
- [User Guide](docs/user_guides/user_guide.md)
- [Progressive Feature Setup](docs/user_guides/progressive_setup.md)
- [CLI Reference](docs/user_guides/cli_reference.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Project Analysis](docs/analysis/executive_summary.md)
- [Implementation Status Matrix](docs/implementation/feature_status_matrix.md)
- [Requirements Traceability Matrix](docs/requirements_traceability.md)
- [SDLC Policies](docs/policies/index.md)
- [Project Roadmap](docs/roadmap/ROADMAP.md)

Installation instructions are covered in detail in the [Installation Guide](docs/getting_started/installation.md) and the [Quick Start Guide](docs/getting_started/quick_start_guide.md).

For instructions on configuring a development environment, see the [development setup guide](docs/developer_guides/development_setup.md).

### Environment Requirements

DevSynth requires **Python 3.12 or higher**. Using [Poetry](https://python-poetry.org/) is recommended for managing dependencies during development.

## Installation

You can install DevSynth in a few different ways:

1. **Poetry** – install from PyPI

   ```bash
   poetry add devsynth
   ```

2. **pipx** *(end-user install)* – keep DevSynth isolated from system Python

   ```bash
   pipx install devsynth
   ```

3. **Docker** – build and run using the provided Dockerfile

   ```bash
   docker build -t devsynth .
   docker run --rm -p 8000:8000 devsynth
   ```

4. **From Source for Development** – use Poetry

   ```bash
   # Install development and documentation dependencies
   poetry install --with dev,docs
   # Optionally include all extras
   poetry sync --all-extras --all-groups
   ```

   Use pip or pipx only when installing from PyPI.

For more on Docker deployment, see the [Deployment Guide](docs/deployment/deployment_guide.md).

## Optional Dependencies

Certain features use additional backends that are not installed by default. Install them if you need these capabilities:

```bash
poetry install --extras retrieval --extras memory --extras llm --extras api --extras webui
# Install GPU support if you plan to run local models
# poetry install --extras gpu
# or install from PyPI
pip install 'devsynth[retrieval,memory,llm,api,webui]'
```

These extras enable optional vector stores such as **ChromaDB**, **Kuzu**, **FAISS**, and **LMDB**, additional LLM providers, the FastAPI server with Prometheus metrics, and the Streamlit WebUI. ChromaDB runs in embedded mode by default.

### Offline Mode

Set `offline_mode: true` in your project configuration to run DevSynth without
network access. When enabled the CLI automatically uses the built-in
OfflineProvider, which generates deterministic text and embeddings or loads a
local model defined by `offline_provider.model_path`. Install the `gpu` extra to
enable hardware acceleration. See
[Offline Provider details](docs/technical_reference/llm_integration.md#offline-provider)
for more information.

## Minimal Project Example

Follow these steps to try DevSynth on a small project:

```bash
# Create a new project
devsynth init demo_project
cd demo_project

# Add a few requirements (edit requirements.md)

# Generate specs, tests, and code
devsynth spec
devsynth test
devsynth code

# Install development dependencies
poetry install --with dev --extras minimal
# Enable GPU support if desired
# poetry install --extras gpu
# Install every optional feature and group (required for the full test suite)
poetry install --all-extras --all-groups

# Run the tests or execute the app
poetry run pytest
# or
devsynth run-pipeline
```

Use [`templates/project.yaml`](templates/project.yaml) as a reference for your `.devsynth/project.yaml`. If you run into issues, see [docs/getting_started/troubleshooting.md](docs/getting_started/troubleshooting.md).

## Examples

The repository includes runnable examples that walk through common workflows:

- [Calculator](examples/calculator) – basic CLI-driven project generation
- [Full Workflow](examples/full_workflow) – demonstrates the refactor workflow
- [Agent Adapter](docs/getting_started/agent_adapter_example.md) – shows how to
  use the `AgentAdapter` directly from Python
- [Init Example](examples/init_example) – project setup using `devsynth init`
- [Spec Example](examples/spec_example) – generate specifications from requirements
- [Test Example](examples/test_example) – create tests from specs
- [Code Example](examples/code_example) – produce code that passes the tests
- [EDRR Cycle Example](examples/edrr_cycle_example) – run the Expand–Differentiate–Refine–Retrospect workflow
- [End-to-End CLI Example](examples/e2e_cli_example) – complete workflow using the CLI
- [End-to-End WebUI Example](examples/e2e_webui_example) – complete workflow using the WebUI

## Running Tests

Always execute tests with `poetry run pytest`. Invoking plain `pytest`
may fail because required plugins are installed only in the Poetry
virtual environment. Environment provisioning is handled automatically
in Codex environments. For manual setups, run `poetry install` to
install all dependencies before running the tests.

Before running the test suite manually, you **must** install DevSynth with its development extras:

```bash
# Minimal setup for contributors
poetry install --with dev --extras minimal

# Enable GPU support if needed
# poetry install --extras gpu
```

Running the **full** test suite additionally requires the optional extras `minimal`, `retrieval`, `memory`, `llm`, `api`, `webui`, `lmstudio`, and `chromadb`:

```bash
poetry install --extras minimal --extras retrieval --extras memory \
  --extras llm --extras api --extras webui --extras lmstudio \
  --extras chromadb
```
Alternatively, install them all at once:

```bash
poetry install --all-extras --all-groups
```

The Codex environment runs a similar command automatically:

```bash
poetry install \
  --with dev,docs \
  --all-extras \
  --no-interaction
```

To recreate the Codex provisioning steps locally, run the helper script:

```bash
bash scripts/codex_setup.sh
```
If the setup fails, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created.
Delete the file after resolving the issue and rerun the script until it
completes successfully.

The test suite runs entirely in isolated temporary directories.  Ingestion and
WSDE tests no longer require special environment variables and are executed by
default when running `poetry run pytest`.

Use pip only for installing from PyPI, not for local development.

Some tests and features rely on optional vector store backends such as **ChromaDB**, **Kuzu**, **FAISS**, and **LMDB**. Install these packages if you plan to use them:

```bash
poetry install --extras retrieval
# or install from PyPI
pip install 'devsynth[retrieval]'
```

For a minimal install without optional extras:

```bash
poetry install --without dev --without docs
```

You can later enable specific features with `poetry install --extras retrieval --extras api`.

After installation, execute the tests with:
```bash
poetry run pytest
```
If `pytest` reports missing packages, run `poetry install` to ensure all
dependencies are installed.

You can also use the helper script `scripts/run_all_tests.py` to run the entire
suite or specific groups of tests and optionally generate an HTML report:

```bash
./scripts/run_all_tests.py         # run all tests
./scripts/run_all_tests.py --unit  # run only unit tests
./scripts/run_all_tests.py --report  # generate HTML report under test_reports/
```

See [docs/developer_guides/testing.md](docs/developer_guides/testing.md) for detailed testing guidance.

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
- `src/devsynth/schemas/project_schema.json` – The JSON schema for `.devsynth/project.yaml`.
- `src/` – Source code (modular, hexagonal architecture)
- `tests/` – Unit, integration, and behavior-driven tests
- `docs/` – User, developer, architecture, and policy documentation
- `docs/policies/` – SDLC, security, and cross-cutting policies
- `docs/roadmap/` – Roadmaps and improvement plans
- `docs/specifications/` – Current and archived specifications
- `deployment/` – Deployment scripts and configuration

## Current Limitations

DevSynth is under active development. Collaborative WSDE features, dialectical reasoning,
and automated EDRR cycle orchestration are only partially implemented. These capabilities
are disabled by default via flags in `config/default.yml`. Code, test, and documentation
generation work but often require manual review. See the
[Implementation Status](docs/implementation/feature_status_matrix.md) for detailed progress.

Use `devsynth config enable-feature <name>` to toggle optional capabilities in your
project configuration.

## Traceability & Continuous Improvement

- All requirements, code, and tests are linked via the [Requirements Traceability Matrix](docs/requirements_traceability.md)
- Documentation, code, and tests are kept in sync through regular audits, metadata tagging, and automated CI/CD
- Changelog and semantic versioning ensure all changes are tracked ([CHANGELOG.md](CHANGELOG.md))

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/developer_guides/contributing.md](docs/developer_guides/contributing.md) for guidelines, code style, and development setup.

## License
DevSynth is released under the MIT License. See [LICENSE](LICENSE) for details.

---

_Last updated: July 23, 2025
