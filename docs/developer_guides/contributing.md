---

author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-07-10"
status: published
tags:

- contributing
- development
- guidelines
- process

title: Contributing Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Contributing Guide
</div>

# Contributing Guide

Thank you for your interest in contributing to DevSynth! This document provides guidelines and instructions for contributing to the project.

See also: [Development Setup](development_setup.md), [Code Style](code_style.md), [Testing](testing.md), [Documentation Policies](../policies/documentation_policies.md)

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)


## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Be collaborative
- Be clear and constructive when providing feedback
- Focus on what is best for the community
- Show empathy towards other community members


## Getting Started

### Fork and Clone the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/YOUR-USERNAME/devsynth.git
   cd devsynth
   ```

3. Add the original repository as an upstream remote:

   ```bash
   git remote add upstream https://github.com/ravenoak/devsynth.git
   ```

4. Create a new branch for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)


### Setup

1. Install dependencies using Poetry:

   ```bash
   # Install development dependencies and required extras
   poetry install --with dev --extras "tests retrieval chromadb api"

   # Enable GPU features if required
   # poetry install --extras gpu
   ```

2. Activate the Poetry virtual environment:

   ```bash
   poetry shell
   ```

3. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

   The pre-commit hooks will run automatically when you commit changes. They include:
   - Code formatting (Black, isort)
   - Linting (flake8)
   - Type checking (mypy)
   - Test-first development check (ensures tests exist before implementing functionality)
   - Commit message linting for MVUU compliance


   The test-first check enforces the TDD/BDD approach by verifying that new or modified Python files have corresponding test files. This ensures that you write tests before implementing functionality.

## Coding Standards

DevSynth follows these coding standards:

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for documentation
- Maximum line length is 88 characters (compatible with Black)
- Use meaningful variable and function names
- Write self-documenting code where possible


### Code Formatting

We use the following tools to enforce code style:

- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [flake8](https://flake8.pycqa.org/) for linting


You can run these tools manually:

```bash

# Format code with Black

poetry run black src tests

# Sort imports with isort

poetry run isort src tests

# Lint with flake8

poetry run flake8 src tests
```

## Type Hints

- Use type hints for all function parameters and return values
- Use the `typing` module for complex types
- Run mypy to check type correctness:

  ```bash
  poetry run mypy src
  ```

### Architecture Guidelines

- Follow the hexagonal architecture pattern
- Keep domain logic free of external dependencies
- Use interfaces (abstract base classes) to define contracts
- Implement adapters for external systems
- Use dependency injection for better testability


## Testing Requirements

Note: This section summarizes contributor expectations. For canonical testing instructions, fixtures, speed markers, and CLI options, see docs/developer_guides/testing.md.

DevSynth uses pytest for unit testing and pytest-bdd for behavior-driven tests.

### Writing Tests

- **Follow the test-first development approach (TDD/BDD)**:
  - Write tests before implementing functionality
  - Run tests to verify they fail (Red)
  - Implement the minimum code to make tests pass (Green)
  - Refactor the code while keeping tests passing (Refactor)
- Write unit tests for all new functionality
- Write behavior tests (BDD) for user-facing features
- Aim for at least 80% code coverage
- Follow the arrange-act-assert pattern
- Use descriptive test names that explain what is being tested
- Use fixtures for common setup and teardown


### Running Tests

For end-to-end guidance (speed markers, resources, smoke mode, segmentation), refer to the canonical testing guide: docs/developer_guides/testing.md.

```bash

# Run all tests

poetry run pytest

# Run unit tests only

poetry run pytest tests/unit/

# Run behavior tests only

poetry run pytest tests/behavior/

# Run tests with coverage report

poetry run pytest --cov=src --cov-report=term-missing
```

## Test Requirements

- All tests must pass before submitting a pull request
- **Tests must be written before implementing functionality (TDD/BDD approach)**
- New features must include appropriate tests (unit tests and BDD tests for user-facing features)
- Bug fixes should include tests that reproduce the bug
- No significant decrease in code coverage
- Mark each test with exactly one speed marker:
  - `@pytest.mark.fast` – under 1 second
  - `@pytest.mark.medium` – under 5 seconds
  - `@pytest.mark.slow` – 5 seconds or more
- Gate high-memory tests with `@pytest.mark.memory_intensive`
- Pre-commit hooks will enforce the test-first approach by checking for test files


## Documentation

Good documentation is essential for the project. Please follow these guidelines:

### Code Documentation

- Add docstrings to all public classes and methods
- Include parameter descriptions and return value information
- Document exceptions that may be raised
- Add inline comments for complex logic


### Project Documentation

- Update relevant documentation for new features or changes
- Keep the README.md up to date
- Add examples for new functionality
- Document API changes
- Record MVUU details using `docs/specifications/mvuuschema.json` (see `mvuu_example.json` for structure)


## Pull Request Process

1. **Update your fork**: Before creating a pull request, make sure your fork is up to date with the main repository:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**: Ensure all tests pass locally:

   ```bash
   poetry run pytest
   ```

3. **Format code**: Run the code formatters:

   ```bash
   poetry run black src tests
   poetry run isort src tests
   ```

4. **Create a pull request**: Push your changes to your fork and create a pull request:

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Pull request description**: Include the following in your pull request description:
   - A clear description of the changes
   - The motivation for the changes
   - Any breaking changes
   - Screenshots or examples if applicable
   - Reference to related issues

6. **Review process**: Be responsive to feedback and make requested changes
   - Address all review comments
   - Update your branch as needed
   - Re-request review when ready

7. **Merge**: Once approved, your pull request will be merged


## Issue Reporting

If you find a bug or have a feature request, please create an issue on GitHub:

1. Check if the issue already exists
2. Use the appropriate issue template
3. Provide as much detail as possible:
   - For bugs: steps to reproduce, expected behavior, actual behavior, environment details
   - For features: clear description, use cases, benefits


## Commit Guidelines

- Use clear and descriptive commit messages
- Reference issue numbers in commit messages when applicable
- Keep commits focused on a single change
- Use present tense ("Add feature" not "Added feature")

Every commit message must include an MVUU JSON block that documents the utility,
affected files, tests, traceability information, and confirms MVUU usage along
with the related issue. See the [docs/specifications/mvuuschema.json](../specifications/mvuuschema.json)
for the full specification.

### Commit template

```text
type(scope): short summary

Optional detailed description
```

```json
{
  "MVUU": {
    "utility_statement": "Explain the utility provided by this change.",
    "affected_files": ["path/to/file"],
    "tests": ["poetry run pytest tests/..."],
    "TraceID": "DSY-0000",
    "mvuu": true,
    "issue": "#123"
  }
}
```


Lint commit messages locally with the dedicated linter:

```bash
python scripts/commit_linter.py --range origin/main..HEAD
```

The script validates Conventional Commit headers and the MVUU JSON block and
is also executed automatically via a `commit-msg` pre-commit hook.


Example commit message:

```text
feat(tracking): add token usage instrumentation

- Implement TokenTracker class
- Add token counting to LLMAdapter
- Update documentation with token usage examples
```

```json
{
  "MVUU": {
    "utility_statement": "Adds token tracking for better cost estimation.",
    "affected_files": [
      "src/devsynth/token_tracker.py",
      "docs/usage.md"
    ],
    "tests": [
      "poetry run pytest tests/unit/test_token_tracker.py"
    ],
    "TraceID": "DSY-1234",
    "mvuu": true,
    "issue": "#123"
  }
}
```

## Issue Traceability Automation

Commits that reference GitHub issues (for example, `#123`) can be automatically processed on `main` by enabling the `update_issue_links` workflow found under `.github/workflows.disabled/update_issue_links.yml`. When activated, the workflow runs `scripts/update_issue_links.py` to post the commit URL as a comment on each referenced issue and requires access to the repository `GITHUB_TOKEN`.

To run the script locally, provide a token with permission to comment on issues:

```bash
export GITHUB_TOKEN=<your-token>
python scripts/update_issue_links.py --commit <commit-sha>
```

The script reads `GITHUB_TOKEN` or `GH_TOKEN` from the environment to authenticate with the GitHub API.

## Versioning

DevSynth follows [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backward-compatible manner
- PATCH version for backward-compatible bug fixes


## License

By contributing to DevSynth, you agree that your contributions will be licensed under the project's [MIT License](../LICENSE).

## Questions?

If you have any questions about contributing, please open an issue or reach out to the maintainers.

Thank you for contributing to DevSynth!
## Implementation Status

- Status: documentation upkeep ongoing
