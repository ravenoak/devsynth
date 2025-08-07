# AGENTS.md

> Special note: the environment that ChatGPT Codex operates in executes `scripts/codex_setup.sh` **while network access is enabled**. Network access is dropped once setup is complete and the environment is handed off to the agent. If the script fails for any reason, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created.

Because network access is only available during the setup phase, rerunning the script offline may not succeed if it still needs to fetch packages. Any changes you make to `scripts/codex_setup.sh` will only be fully applied when the next environment setup is triggered.

## Introduction

This document provides a comprehensive guide to the agent-based components within the DevSynth project. It outlines the structure, conventions, configuration, and operational guidelines for developing, testing, and maintaining agents in this codebase.

## Scope

This file covers all AI and service agents implemented in the `src/devsynth/` directory and related scripts in `scripts/` that embody agentic behavior.

## Quick Start

Always lint and test before committing.

### Linting

```bash
poetry run pre-commit run --files path/to/file1.py [path/to/file2.py ...]
```

### Tests

```bash
poetry run pytest
```

Running hooks and tests through `poetry run` ensures they execute inside the project's virtual environment and prevents missing-package errors. Always invoke the pre-commit hooks on the files you are about to commit using the `--files` option shown above.

## Module-Level AGENTS.md Files

Some directories include their own `AGENTS.md` with additional, more specific instructions. To locate them:

```bash
find . -name AGENTS.md
```

Instructions in a nested `AGENTS.md` override guidance from parent directories for files within their scope.

## Environment Setup

**Important:** `scripts/codex_setup.sh` exclusively provisions the Codex environment. Never reference or duplicate its logic outside of this file.

The automated Codex environment runs the setup script as:

```bash
scripts/codex_setup.sh || touch CODEX_ENVIRONMENT_SETUP_FAILED
```

The script is executed **before** network access is disabled. If it fails, a
file named `CODEX_ENVIRONMENT_SETUP_FAILED` will appear in the repository root.
Only rerun `scripts/codex_setup.sh` if `CODEX_ENVIRONMENT_SETUP_FAILED` is present.
Example:

```bash
if [ -f CODEX_ENVIRONMENT_SETUP_FAILED ]; then bash scripts/codex_setup.sh; fi
```
Fix the script and rerun it offline to finish provisioning:

1. Review and update `scripts/codex_setup.sh` so it installs all project
   dependencies with `poetry install --with dev,docs --all-extras` (or the
   `--minimal` variant) and verifies key packages such as `pytest-bdd` are
   available.
2. Run `bash scripts/codex_setup.sh` (without network access) until it completes
   without errors. After it finishes, verify the environment, dependencies,
   and extras:

 ```bash
  poetry env info --path
  poetry run pip check
  # Ensure extras required for tests are installed. These imports
  # confirm retrieval, chromadb, GUI, and API extras are available offline.
  poetry run python - <<'EOF'
import importlib, sys
for pkg in (
    "fastapi",
    "streamlit",
    "lmstudio",
    "tinydb",
    "duckdb",
    "lmdb",
    "chromadb",
    "kuzu",
    "faiss",
    "prometheus_client",
    "httpx",
    "dearpygui",
):
    importlib.import_module(pkg)
EOF
  poetry run pip list | grep pytest-bdd
  ```
3. Remove the failure marker with `rm CODEX_ENVIRONMENT_SETUP_FAILED`.
4. Execute `poetry run pytest --maxfail=1` to verify the environment quickly.
5. If the tests fail, rerun the setup script and repeat until
   `poetry run pytest --maxfail=1` succeeds.

Changes to the setup script only take effect the next time Codex provisions an
environment. OpenAI disables network access during execution, so `scripts/codex_setup.sh`
runs first with network access to install dependencies before the sandbox is
handed to the agent.

Development and test commands may fail until the setup script completes
successfully, the marker file is removed, and the tests pass.


### pipx installation

- `scripts/codex_setup.sh` installs `pipx`.
- The DevSynth CLI is installed using `pipx install --editable .`.
- The script adds `~/.local/bin` to `PATH` so the `devsynth` command is available.
- Contributors must keep the `pipx` installation steps in sync with project requirements.

## Project Structure

```
src/devsynth/           # Core agent implementations
scripts/                # Utility and agent-related scripts
docs/                   # Documentation
docs/architecture/      # Agent system architecture docs
docs/analysis/          # Agent analysis and evaluation
docs/developer_guides/  # Developer guides and best practices
docs/implementation/    # Implementation details and guides
docs/policies/          # Project policies and guidelines
docs/roadmap/           # Project roadmap and milestones
docs/specifications/    # Technical specifications
tests/                  # Unit, integration, and behavior tests for agents
```

Refer to `docs/architecture/agent_system.md` and `docs/architecture/wsde_agent_model.md` for detailed architectural overviews.

## Agent Configuration

- **Dependencies:** Managed exclusively with Poetry (`pyproject.toml`). Do **not** run `pip install` directly except when installing from PyPI with `pip` or `pipx`. Use `poetry install` or `poetry sync` so all packages are installed in the Poetry-managed virtual environment.
- **Environment:** Use the provided `config/` files for environment-specific settings.
- **Setup:**
  1. Install dependencies with `poetry install` or `poetry sync --all-extras --all-groups` for the full development environment.
  2. Activate the virtual environment using `poetry shell` (or prefix commands with `poetry run`).
  3. Configure environment variables as needed (see `config/`).

## Coding Conventions

- **Naming:**
  - Agent classes: `*Agent` (e.g., `SearchAgent`)
  - Files: `snake_case.py`
- **Formatting:**
  - Follow [PEP8](https://peps.python.org/pep-0008/) and project `docs/developer_guides/code_style.md`.
  - Use [Black](https://black.readthedocs.io/) for code formatting.
- **Documentation:**
  - Use docstrings for all public classes and methods.
  - Reference `docs/developer_guides/code_style.md` for comment style.

## Agent Lifecycle & Operation

- Agents are instantiated and managed within the `src/devsynth/` package.
- Communication may use direct method calls, events, or message passing (see `docs/architecture/agent_system.md`).
- Logging should use the standard logging library and follow `docs/developer_guides/error_handling.md`.

## Testing Protocols

- **Framework:** [pytest](https://docs.pytest.org/)
- **Test Locations:** `tests/unit/`, `tests/integration/`, `tests/behavior/`
- **Coverage:** Aim for >90% coverage on agent logic.
- **Running Tests:**
  - `poetry run pytest tests/`
  - See `docs/developer_guides/hermetic_testing.md` for isolation practices.
  - Running the full suite requires the `minimal`, `retrieval`, `memory`, `llm`,
    `api`, `webui`, and `lmstudio` extras.

## Pull Request (PR) Guidelines

- Follow the process in `CONTRIBUTING.md` and `docs/developer_guides/cross_functional_review_process.md`.
- All PRs must include:
  - Relevant tests
  - Updated documentation
  - Passing CI checks
- Use feature branches and submit PRs to `main` or as specified in the roadmap.

## Best Practices

- Avoid hardcoding configuration; use `config/`.
- Write modular, composable agents.
- Use logging and error handling as per guidelines.
- Profile and optimize for performance where needed.
- See `docs/analysis/critical_recommendations.md` for common pitfalls.

## Examples and Use Cases

- See `docs/architecture/agent_system.md` for agent interaction diagrams.
- Example agent implementation: `src/devsynth/example_agent.py` (if available).
- Example test: `tests/unit/test_example_agent.py`.

## Contributing Guidelines

- See `CONTRIBUTING.md` and `docs/developer_guides/contributing.md`.
- Contributions should follow the structure and conventions outlined here.

## References and Resources

- [PEP8](https://peps.python.org/pep-0008/)
- [Black](https://black.readthedocs.io/)
- [pytest](https://docs.pytest.org/)
- Project documentation in `docs/`
- [Agent Tools Guide](docs/developer_guides/agent_tools.md) - Using the tool registry and adding new tools
- Agent architecture: `docs/architecture/agent_system.md`, `docs/architecture/wsde_agent_model.md`

## Feedback

For questions or suggestions regarding agents, open an issue or contact the maintainers as described in `CONTRIBUTING.md`.

---

*Keep this file up to date as the agent system evolves.*
