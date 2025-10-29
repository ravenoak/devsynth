---

title: "DevSynth Code Style Guide"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "developer-guide"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Code Style Guide
</div>

# DevSynth Code Style Guide

This document outlines the coding standards and style guidelines for the DevSynth project. Adhering to these guidelines ensures consistency, readability, and maintainability of the codebase.

## 1. General Principles

- **Readability:** Write code that is easy to understand. Prioritize clarity over conciseness where appropriate.
- **Simplicity:** Keep solutions as simple as possible (KISS principle).
- **Consistency:** Follow the established style throughout the project.


## 2. Python Style

- **PEP 8:** All Python code MUST adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- **Formatter:** We use `black` for automated code formatting. Ensure your code is formatted with `black` before committing.
    - Configuration: (Specify if any non-default `black` configuration is used, e.g., in `pyproject.toml`)
- **Linter:** We use `flake8` and `pylint` for linting.
    - Configuration: (Specify paths to config files or relevant sections in `pyproject.toml`)
    - Aim for zero linter warnings/errors.
- **Type Hinting (PEP 484):**
    - All new code MUST include type hints.
    - Gradually add type hints to existing code, prioritizing critical modules.
    - Use `mypy` for static type checking. Configuration is in `pyproject.toml`.
- **Docstrings (PEP 257):**
    - All public modules, classes, functions, and methods MUST have docstrings.
    - Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings) for docstring format (or specify another, e.g., NumPy/SciPy, reStructuredText).
    - Docstrings should clearly explain the purpose, arguments, return values, and any exceptions raised.
- **Imports:**
    - Order imports as per PEP 8: standard library, third-party, local application/library specific.
    - Use absolute imports where possible.
- **Naming Conventions:**
    - `snake_case` for functions, methods, variables, and modules.
    - `CapWords` (PascalCase) for classes.
    - `UPPER_SNAKE_CASE` for constants.
    - Protected members should be prefixed with a single underscore (`_protected_member`).
    - Private members (name-mangled) should be prefixed with a double underscore (`__private_member`).
- **Error Handling:**
    - Use custom exceptions inheriting from `DevSynthError` (see `src/devsynth/exceptions.py`).
    - Be specific with exception handling; avoid broad `except Exception:` clauses where possible.
- **Logging:**
    - Use the centralized logger from `src/devsynth/logging_setup.py`.
    - Follow defined logging levels and conventions.


## 3. Markdown Style

- **Line Length:** Keep lines to a reasonable length (e.g., 80-120 characters) for readability, especially in documentation.
- **Headings:** Use ATX-style headings (`# Heading 1`, `## Heading 2`, etc.).
- **Lists:** Use hyphens (`-`) or asterisks (`*`) for unordered lists, and numbers (`1.`) for ordered lists.
- **Code Blocks:** Use fenced code blocks with language identifiers (e.g., ```python ... ```).
  - **Front-matter:** All Markdown documents should include front-matter metadata as defined in `docs/metadata_template.md` and validated by the `devsynth validate-metadata` command.


## 4. Gherkin (.feature file) Style

- **Clarity and Conciseness:** Scenarios should be easy to understand by both technical and non-technical stakeholders.
- **Background:** Use `Background` for steps common to all scenarios in a feature file.
- **Tags:** Use tags (`@tagname`) to categorize features and scenarios (e.g., `@smoke`, `@regression`, `@module-X`).
- **Linting:** (Specify if a Gherkin linter like `gherkin-lint` is used and its configuration).


## 5. Commit Messages

- Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- Example: `feat: add user authentication service`
- Example: `fix: resolve issue with config parsing`
- Example: `docs: update installation guide`


## 6. Updating This Guide

This guide is a living document. If you have suggestions for improvements or clarifications, please discuss them with the team or open an issue/PR.

## Implementation Status

.
