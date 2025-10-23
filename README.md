---
title: "DevSynth"
date: "2025-05-20"
version: "0.1.0a1"
tags:
  - "devsynth"
  - "overview"
  - "documentation"
  - "readme"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-13"
---

> Special note: LLMs have synthesized this project, with minimal manual editing, using a dialectical HITL methodology.

# DevSynth
![Version](https://img.shields.io/badge/version-0.1.0a1-blue.svg) [![Pre‑release](https://img.shields.io/badge/status-pre--release-orange.svg)](docs/release/0.1.0-alpha.1.md)
[![Readiness Checklist](https://img.shields.io/badge/readiness-checklist-blueviolet.svg)](docs/tasks.md)
![Coverage](docs/coverage.svg)

DevSynth is an agentic software engineering platform that leverages LLMs, advanced memory systems, and dialectical reasoning to automate and enhance the software development lifecycle. The system is designed for extensibility, resilience, and traceability, supporting both autonomous and collaborative workflows.

**Pre-release notice:** DevSynth is still pre-0.1.0 and no package has been published on PyPI. Version `0.1.0a1` has been tagged as `v0.1.0a1`; see [docs/release/0.1.0-alpha.1.md](docs/release/0.1.0-alpha.1.md) and the prioritized readiness checklist at [docs/tasks.md](docs/tasks.md). All versions should be considered experimental. Version labels follow our [Semantic Versioning+ policy](docs/policies/semantic_versioning.md). Release milestones and targeted features post-`0.1.0a1` are documented in [docs/release/roadmap.md](docs/release/roadmap.md); see [docs/roadmap/CONSOLIDATED_ROADMAP.md](docs/roadmap/CONSOLIDATED_ROADMAP.md) for the broader project plan.
## Quickstart

Prerequisites
- Python 3.12.x
- Poetry

Setup (choose one)
- Recommended targeted baseline (tests without heavy GPU/LLM deps):
  - poetry install --with dev --extras "tests retrieval chromadb api"
  - If FAISS/Kuzu/ChromaDB wheels are unavailable on your platform, fall back to
    `poetry install --with dev --extras "tests"` and temporarily export
    `DEVSYNTH_RESOURCE_FAISS_AVAILABLE=false`,
    `DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false`, and
    `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false` so smoke and fast suites still
    run while coverage instrumentation remains active.
- Minimal contributor setup:
  - poetry install --with dev --extras minimal
- Full dev + docs with all extras:
  - poetry install --with dev,docs --all-extras

Sanity checks
- task env:verify  # ensure go-task and the devsynth CLI are available
- task mypy:strict  # run strict mypy for src/devsynth (append CLI args for extras)
- poetry run devsynth --help
- poetry run devsynth doctor
- poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel --maxfail=1
- Smoke mode (reduces plugin surface):
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel

## Testing Quick Start

- Fast local smoke (all fast):
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel
- Unit fast lane:
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
- Behavior fast lane:
  - poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel
- Integration fast lane:
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel
- Generate HTML test report:
  - poetry run devsynth run-tests --report
- Segmented full suite (recommended default for long runs):
  - poetry run devsynth run-tests --target all-tests --speed fast --speed medium --speed slow --no-parallel --segment --segment-size 50 --report
- Full guidance: see docs/developer_guides/testing.md
- Bypass coverage gate while iterating: see docs/developer_guides/testing.md#bypassing-coverage-gate-for-focused-runs
- Section 7 scripts (sanity+inventory, marker discipline): see docs/developer_guides/testing.md#using-section-7-helper-scripts-in-ci-and-locally
- CLI options reference: see docs/user_guides/cli_command_reference.md
- Maintainer Must-Run Sequence: see docs/tasks.md (Task 23) for the step-by-step order and commands; use Taskfile targets where provided.

Optional resources (opt-in)
- Install an extra and export the flag to enable gated tests/resources, e.g. TinyDB:
  - poetry add tinydb --group dev
  - export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
- Enable LMDB-backed memory tests and tooling:
  - poetry install --extras retrieval
  - export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=1
- DuckDB-backed memory store and vector search:
  - poetry install --extras memory  # includes duckdb and numpy dependencies
  - export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true  # set to false to skip DuckDB tests
- RDFLib knowledge graph memory backend:
  - rdflib installs with the core package; `poetry install --extras memory` keeps companion adapters aligned
  - export DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE=true  # set to false to skip RDFLib-specific tests
- Streamlit/Web UI workflows:
  - export DEVSYNTH_RESOURCE_WEBUI_AVAILABLE=1  # enable WebUI and agent HTTP interface tests
- Common flags: DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE, DEVSYNTH_RESOURCE_CLI_AVAILABLE, DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE
- Note: The run-tests CLI defaults to a stub provider and offline mode in tests unless overridden.
- See also: [Resources Matrix](docs/resources_matrix.md) for mapping extras to DEVSYNTH_RESOURCE_* flags and enablement examples.

Next steps
- Testing guidance: docs/developer_guides/testing.md (see stabilization plan: docs/plan.md and working checklist: docs/tasks.md)
- CLI options reference: docs/user_guides/cli_command_reference.md
- Release Playbook: docs/release/release_playbook.md

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
- MVUU engine for tracking Minimum Viable Utility Units
- Atomic-Rewrite workflow for fine-grained code updates
- **Adaptive Project Ingestion**: Dynamically understands and adapts to diverse project structures (including monorepos, multi-language projects, and custom layouts) using a `.devsynth/project.yaml` file and a fully integrated "Expand, Differentiate, Refine, Retrospect" (EDRR) framework. The `EDRRCoordinator` orchestrates this process across all system components. See [EDRR Assessment](docs/implementation/edrr_assessment.md) for details. The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth.
- **Cursor IDE Integration**: Seamless integration with Cursor IDE providing structured AI assistance through Rules, Commands, and Modes that align with DevSynth's EDRR framework and SDD+BDD methodologies. See [Cursor Integration Guide](.cursor/README.md) for details.

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
- [CLI Command Reference](docs/user_guides/cli_command_reference.md)
- [API Reference Generation Guide](docs/user_guides/api_reference_generation.md)
- [Dear PyGui Guide](docs/user_guides/dearpygui.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Project Analysis](docs/analysis/executive_summary.md)
- [Implementation Status Matrix](docs/implementation/feature_status_matrix.md)
- [Requirements Traceability Matrix](docs/requirements_traceability.md)
- [SDLC Policies](docs/policies/index.md)
- [Project Roadmap](docs/roadmap/CONSOLIDATED_ROADMAP.md)
- [Glossary](docs/glossary.md)

Installation instructions are covered in detail in the [Installation Guide](docs/getting_started/installation.md) and the [Quick Start Guide](docs/getting_started/quick_start_guide.md).

For instructions on configuring a development environment, see the [development setup guide](docs/developer_guides/development_setup.md).

### Environment Requirements

DevSynth requires **Python 3.12**. Using [Poetry](https://python-poetry.org/) is recommended for managing dependencies during development.

Provision the development environment by running the environment provisioning script:

```bash
bash scripts/install_dev.sh
```

> **Note:** Run this script **before** invoking any Taskfile commands to ensure the `task` runner is installed and ready.

## Installation

### Editable Install (from source)

To run DevSynth directly from a cloned repository with an editable install using Poetry, follow these steps:

1. Ensure you are using Python 3.12 and Poetry.
2. From the project root, create the virtual environment and install dependencies:

```bash
poetry install
```

3. Run the CLI to verify that imports resolve cleanly:

```bash
poetry run devsynth --help
```

If you encounter a ModuleNotFoundError:
- Make sure you are running within the Poetry virtual environment (use `poetry run` or `poetry shell`).
- Confirm that the package path is correct (the project uses `packages = [{ include = "devsynth", from = "src" }]`).
- If you plan to run tests or optional features, install the necessary extras:

```bash
# Minimal contributor setup (fast path) aligning with project guidelines
poetry install --with dev --extras minimal

# Minimal contributor setup with common tooling
poetry install --with dev --extras "tests"
# For retrieval or API examples add extras as needed
poetry install --extras retrieval --extras api
```

Basic CLI usage (e.g., `--help`, `init`, `config`) does not require optional extras. Optional providers and GUIs remain lazy‑loaded and are strictly optional.

### Installation

Pre-release note: DevSynth 0.1.0a1 is not published on PyPI. Prefer Poetry for development installs, or pipx from a local checkout or Git URL.

1. From source (development) — Poetry

   ```bash
   # Clone and enter the repository
   git clone https://github.com/ravenoak/devsynth.git
   cd devsynth

   # Install development and documentation dependencies with targeted extras
   poetry install --with dev,docs --extras "tests retrieval chromadb api"
   # Optionally include all extras
   poetry sync --all-extras --all-groups
   ```

2. pipx (isolated end-user install) — from local path or Git

   ```bash
   # From a local checkout
   pipx install .

   # Or directly from Git (pin to a tag or commit for reproducibility)
   pipx install git+https://github.com/ravenoak/devsynth.git@v0.1.0a1
   ```

3. Docker — build and run using the provided Dockerfile

   ```bash
   docker build -t devsynth .
   docker run --rm -p 8000:8000 devsynth
   ```

4. Quick GUI preview — from source extras

   ```bash
   # Enable GUI extras with Poetry
   poetry install --extras gui
   poetry run devsynth dpg
   ```

### Shell Completion

Enable tab completion for DevSynth commands:

```bash
devsynth --install-completion
# or
devsynth completion --install
```

For more on Docker deployment, see the [Deployment Guide](docs/deployment/deployment_guide.md).

## Environment Provisioning Verification

The environment provisioning script bootstraps the project and runs verification commands to ensure consistency:

```bash
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```

Use `--changed` to limit marker verification to tests modified since the last
commit:

```bash
poetry run python scripts/verify_test_markers.py --changed
```

## Development Workflow

Run all development commands inside the Poetry-managed virtual environment. A
typical workflow is:

```bash
poetry install
pre-commit install
pre-commit autoupdate
poetry run pre-commit run --files <files>
poetry run pytest
```

### Virtual Environment Best Practices

- Create the environment with `poetry install` rather than using the system
  interpreter.
- Prefix commands with `poetry run` or start an interactive session with
  `poetry shell`.
- Avoid installing packages with the global `pip`; rely on Poetry for
  dependency management.

## Optional Dependencies

Certain features use additional backends that are not installed by default. Install them if you need these capabilities:

```bash
poetry install --extras retrieval --extras chromadb --extras memory --extras llm --extras api --extras webui --extras gui
# Install GPU support if you plan to run local models
# poetry install --extras gpu
# or install from PyPI
pip install 'devsynth[retrieval,memory,llm,api,webui,gui]'
```

Install the `lmstudio` extra to enable LM Studio integration. Tests that rely on
LM Studio are skipped when the `lmstudio` package is not installed.

These extras enable optional vector stores such as **ChromaDB**, **Kuzu**,
**FAISS**, and **LMDB**, additional LLM providers, the FastAPI server with
Prometheus metrics, the NiceGUI WebUI, and the Dear PyGui interface. ChromaDB
runs in embedded mode by default.

Note on GUI extras: The NiceGUI and Dear PyGui integrations are fully optional.
If these extras are not installed, DevSynth will stub or skip GUI code paths
with friendly messages and will not import GUI frameworks at test collection
or CLI startup. Install with `poetry install --extras gui` (or `pip install
"devsynth[gui]"`) to enable these interfaces.

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
poetry install --with dev --extras "tests retrieval chromadb api"
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

### Textual Wizard Interface

Prefer a guided terminal UI? Launch the Textual-powered experience:

```bash
poetry run devsynth tui --wizard init
```

Enable the accessible palette with `--colorblind` (or `DEVSYNTH_CLI_COLORBLIND=1`). Use `--wizard requirements --requirements-output requirements.json` to drive the requirements wizard through the same Textual bridge used by the CLI.

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
- [Dear PyGui UI Example](examples/dpg_ui_example) – launch the experimental GUI

## Running Tests

For consistency with project tooling and plugins, always run tests via Poetry and the CLI wrapper:

```bash
# Fast sanity subset (recommended)
poetry run devsynth run-tests --speed=fast --no-parallel --maxfail=1

# Full unit/integration targets
poetry run devsynth run-tests --target unit-tests
poetry run devsynth run-tests --target integration-tests

# Smoke mode (reduced plugin surface)
poetry run devsynth run-tests --smoke --speed=fast

# HTML report under test_reports/
poetry run devsynth run-tests --report
```

Install dependencies using one of the presets from our guidelines:

```bash
# Targeted baseline for local testing (no heavy GPU/LLM deps)
poetry install --with dev --extras "tests retrieval chromadb api"

# Minimal contributor setup
poetry install --with dev --extras minimal

# Full dev + docs with all extras
poetry install --with dev,docs --all-extras
```

Notes:
- Tests are isolated and deterministic by default; network is disabled unless explicitly enabled.
- Optional resources (e.g., LM Studio, vector stores) are gated by env flags and extras.

For authoritative, detailed instructions (extras matrix, resource flags, smoke mode, flakiness mitigation), see the DevSynth Testing Guide:
- docs/developer_guides/testing.md

## Alignment and Manifest Validation

Use `devsynth align` and `devsynth validate-manifest` for alignment checks and
manifest validation. These CLI commands replace the legacy helper scripts and
will fully supersede them in a future release.

## Minimum Viable Utility Units (MVUU) Engine

The MVUU engine records the smallest useful change so you can trace
requirements and tests across commits. Initialize it for a project with:

```bash
devsynth mvu init
```

This command scaffolds `.devsynth/mvu.yml` and enables MVUU tracking. After
initialization you can lint commits, generate reports, or rewrite history:

```bash
devsynth mvu lint --range origin/main..HEAD
devsynth mvu report --since origin/main --format html --output report.html
devsynth mvu rewrite --path . --branch-name atomic
```

DevSynth itself continues using an ad‑hoc workflow until v0.4, so MVUU is
optional for now.

## Repository Structure

The repository is organized for clarity and systematic development, following hexagonal architecture principles. For a comprehensive technical reference, see the [Repository Structure Guide](docs/repo_structure.md).

### Key Directories
- `.devsynth/project.yaml` – Configuration file describing the shape and attributes of projects managed by DevSynth. The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth.
- `src/devsynth/schemas/project_schema.json` – The JSON schema for `.devsynth/project.yaml`.
- `src/` – Source code (modular, hexagonal architecture)
- `tests/` – Unit, integration, and behavior-driven tests
- `docs/` – User, developer, architecture, and policy documentation
- `docs/policies/` – SDLC, security, and cross-cutting policies
- `docs/roadmap/` – Roadmaps and improvement plans
- `docs/specifications/` – Current and archived specifications
- `issues/` – In-repo issue tracker with `archive/` for closed tickets ([issues/README.md](issues/README.md))
- `deployment/` – Deployment scripts and configuration

## Testing

Offline-first defaults and provider behavior
- By default, the test CLI configures offline execution to avoid accidental network activity.
- Defaults applied by `devsynth run-tests` when unset:
  - DEVSYNTH_PROVIDER=stub
  - DEVSYNTH_OFFLINE=true
  - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false
- To opt into live provider tests locally, install the appropriate extras and set:
  - For OpenAI: export DEVSYNTH_OFFLINE=false; export DEVSYNTH_PROVIDER=openai; export OPENAI_API_KEY=...; optionally set OPENAI_MODEL/OPENAI_EMBEDDINGS_MODEL.
  - For LM Studio: export DEVSYNTH_OFFLINE=false; export DEVSYNTH_PROVIDER=lmstudio; export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234; export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true.
  - For Kuzu-backed stores: export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true after installing `poetry install --extras retrieval` (or the `memory` extra) to pull in the `kuzu` dependency. Kuzu-specific tests live under `tests/integration/memory/` and are marked `@pytest.mark.requires_resource("kuzu")`.
- Resource-gated tests (`@pytest.mark.requires_resource(...)`) are skipped unless the corresponding `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true` flag is set.

Coverage aggregation guidance
- The repository enforces a global `--cov-fail-under=90` in pytest.ini.
- Avoid asserting readiness from narrow subset runs; aggregate coverage using:
  - poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report
  - or segmented runs followed by: poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json

Run the full test suite with:

```bash
poetry run devsynth run-tests
poetry run devsynth run-tests --maxfail 1  # optional early exit
```

Common, stable profiles:

```bash
# Smoke mode: disables third-party plugins and xdist; fastest, most stable
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# Unit fast segmented (reduce flakiness/memory pressure)
poetry run devsynth run-tests --target unit-tests --speed=fast --segment --segment-size=50 --maxfail=1

# Generate HTML report under test_reports/
poetry run devsynth run-tests --report

# Feature flags (maps to DEVSYNTH_FEATURE_<NAME>)
poetry run devsynth run-tests --feature EXPERIMENTAL_UI --feature SAFETY_CHECKS=false --speed=fast --no-parallel
```

Optional provider tests such as LM Studio are disabled unless explicitly
enabled. Set `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true` to opt in.

The legacy `scripts/run_all_tests.py` wrapper remains for backward compatibility but will be removed in a future release.

### Updating the coverage badge

Run tests with coverage to determine the current percentage:

```bash
poetry run pytest --speed=fast --cov=src/devsynth --cov-report=term
```

Take the reported percentage and update the badge at the top of this README using a Shields.io URL such as:

```markdown
![Coverage](https://img.shields.io/badge/coverage-<percentage>%25-<color>.svg)
```

Replace `<percentage>` with the rounded coverage value and choose an appropriate `<color>` (e.g., red, yellow, or green).

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

_Last updated: August 25, 2025_

## Troubleshooting (Quick Links)
- Testing guide and fixtures: docs/developer_guides/testing.md
- Common issues: docs/getting_started/troubleshooting.md
- Open issues and analyses: issues/
- If tests hang or plugins conflict: try smoke mode
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
