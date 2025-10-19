---

title: DevSynth CLI Command Clarification
date: 2025-08-02
version: "0.1.0-alpha.1"
tags:
- cli
- commands
- clarification
- documentation
status: published
author: DevSynth Team
last_reviewed: "2025-08-02"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth CLI Command Clarification
</div>

# DevSynth CLI Command Clarification

This document clarifies inconsistencies in command naming across the DevSynth documentation to help users understand the correct commands to use.

## Command Naming Inconsistencies

During a documentation review, we identified inconsistencies in how certain CLI commands are referenced across different documentation files. This document aims to clarify these inconsistencies and provide definitive guidance on the correct commands to use.

### Test Generation Commands

#### Inconsistency

In some documentation, the command for generating tests from specifications is referred to as:
- `devsynth test` (e.g., in README.md and some quick start guides)

In other documentation, the same functionality is described using:
- `devsynth run-pipeline` (e.g., in CLI reference documentation)

#### Clarification

Both commands can be used for test generation, but they have different scopes:

- **`devsynth test`**: A focused command specifically for generating tests from specifications. This is the recommended command for users who want to explicitly generate tests.

- **`devsynth run-pipeline`**: A multi-purpose command that can perform different tasks depending on the context and options provided. It can generate tests, run tests, or run the application based on the `--target` option.

#### Recommended Usage

- For test generation only: Use `devsynth test`
- For a complete workflow or when you need more control: Use `devsynth run-pipeline` with appropriate options

### Running Generated Code

#### Inconsistency

The command for running generated code is sometimes referred to as:
- `devsynth run` (in some older documentation)
- `devsynth run-pipeline` (in current documentation)

#### Clarification

- **`devsynth run-pipeline`** is the correct and current command for running generated code.
- The `--target` option specifies what to run:
  - `--target unit-tests`: Run unit tests
  - `--target integration-tests`: Run integration tests
  - `--target behavior-tests`: Run behavior tests
  - `--target application`: Run the application

#### Recommended Usage

```bash
# Run unit tests
devsynth run-pipeline --target unit-tests

# Run the application
devsynth run-pipeline --target application
```

## Command Aliases and Shortcuts

For convenience, DevSynth provides several command aliases:

| Primary Command | Aliases |
|----------------|---------|
| `devsynth spec` | `devsynth specification`, `devsynth generate-spec` |
| `devsynth test` | `devsynth generate-tests` |
| `devsynth code` | `devsynth generate-code`, `devsynth implementation` |

These aliases provide the same functionality as their primary commands and can be used interchangeably.

## Complete Workflow Example

For clarity, here is the complete workflow with the recommended commands:

```bash
# Initialize a new project
devsynth init --path ./my-project
cd my-project

# Generate specifications from requirements
devsynth spec --requirements-file requirements.md

# Generate tests from specifications
devsynth test

# Generate implementation code
devsynth code

# Run the tests
devsynth run-pipeline --target unit-tests

# Run the application
devsynth run-pipeline --target application
```

## Future Command Standardization

As part of our ongoing documentation improvement efforts, we are standardizing command naming across all documentation. In future releases, command references will be consistent across all documentation files.

If you encounter any other command inconsistencies or have questions about the correct commands to use, please refer to the [CLI Reference Documentation](cli_reference.md) or open an issue on the [GitHub repository](https://github.com/ravenoak/devsynth/issues).

---

*Last updated: August 2, 2025*
