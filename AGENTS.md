# AGENTS.md

> Special note: the environment that ChatGPT Codex operates in executes `scripts/codex_setup.sh` as the setup script **while network access is enabled**. If the script fails for any reason, a `CODEX_ENVIRONMENT_SETUP_FAILED` file will be created. After provisioning finishes, network access is disabled.

## Introduction

This document provides a comprehensive guide to the agent-based components within the DevSynth project. It outlines the structure, conventions, configuration, and operational guidelines for developing, testing, and maintaining agents in this codebase.

## Scope

This file covers all AI and service agents implemented in the `src/devsynth/` directory and related scripts in `scripts/` that embody agentic behavior.

## Environment Setup

The automated Codex environment runs the setup script as:

```bash
scripts/codex_setup.sh || touch CODEX_ENVIRONMENT_SETUP_FAILED
```

If `scripts/codex_setup.sh` fails, a file named `CODEX_ENVIRONMENT_SETUP_FAILED`
will appear in the repository root. After the initial provisioning, network
access is disabled, so you may need to adjust the script or install packages
manually to make it succeed. To fix your environment:

1. Review and update `scripts/codex_setup.sh` so it succeeds in your
   environment. You may need to install packages manually or modify the script.
2. Run `bash scripts/codex_setup.sh` (without network access) until it completes
   without errors.
3. Remove the failure marker with `rm CODEX_ENVIRONMENT_SETUP_FAILED`.

Development and test commands may fail until the setup script completes successfully and the marker file is removed.

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
- Agent architecture: `docs/architecture/agent_system.md`, `docs/architecture/wsde_agent_model.md`

## Feedback

For questions or suggestions regarding agents, open an issue or contact the maintainers as described in `CONTRIBUTING.md`.

---

*Keep this file up to date as the agent system evolves.*
