---

author: DevSynth Team
date: '2025-07-30'
last_reviewed: "2025-07-30"
status: published
tags:
- user-guide
- cli
- reference

title: DevSynth CLI Command Reference
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth CLI Command Reference
</div>

# DevSynth CLI Command Reference

## Introduction

This document provides a comprehensive reference for all DevSynth CLI commands. Each command is explained in detail, including its purpose, options, and usage examples.

## Global Options

These options are available for all DevSynth commands:

| Option | Description |
|--------|-------------|
| `--help` | Show help information for the command |
| `--verbose` | Enable verbose output |
| `--quiet` | Suppress non-essential output |
| `--config FILE` | Specify a custom configuration file |

## Core Commands

### init

Initialize a new DevSynth project or configure an existing one.

**Usage:**

```bash
devsynth init [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--wizard / --no-wizard` | Run in interactive wizard mode (default: False) |
| `--root TEXT` | Root directory of the project (default: current directory) |
| `--language TEXT` | Primary programming language for the project |
| `--goals TEXT` | High-level goals or description of the project |
| `--memory-backend [memory\|file\|kuzu\|chromadb]` | Memory backend to use |
| `--offline-mode / --no-offline-mode` | Enable or disable offline mode |
| `--features JSON` | Features to enable or disable (JSON format) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts |
| `--defaults` | Use default values for all prompts |
| `--non-interactive` | Run without interactive prompts |
| `--metrics-dashboard` | Print instructions for launching metrics dashboards |

**Examples:**

```bash
# Initialize a new project in the current directory
devsynth init

# Initialize a new Python project in ./my-project
devsynth init --root ./my-project --language python

# Initialize a project with specific goals
devsynth init --goals "A CLI tool for managing tasks"

# Initialize a project with the interactive wizard
devsynth init --wizard
```

During initialization, DevSynth shows progress indicators and enhanced error messages. Optional metrics dashboards can be explored with `devsynth mvuu-dashboard`.

### spec

Generate specifications from requirements.

**Usage:**

```bash
devsynth spec [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--requirements-file TEXT` | Path to the requirements file (default: requirements.md) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Generate specifications from the default requirements file
devsynth spec

# Generate specifications from a custom requirements file
devsynth spec --requirements-file docs/requirements.md

# Generate specifications with automatic confirmation
devsynth spec --auto-confirm
```

### test

Generate tests from specifications.

**Usage:**

```bash
devsynth test [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--spec-file TEXT` | Path to the specifications file (default: specs.md) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Generate tests from the default specifications file
devsynth test

# Generate tests from a custom specifications file
devsynth test --spec-file docs/specs.md

# Generate tests with automatic confirmation
devsynth test --auto-confirm
```

### code

Generate code from tests.

**Usage:**

```bash
devsynth code [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Generate code from tests
devsynth code

# Generate code with automatic confirmation
devsynth code --auto-confirm
```

### run-pipeline

Run the complete synthesis pipeline (spec, test, code).

**Usage:**

```bash
devsynth run-pipeline [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target TEXT` | Target component to synthesize (default: None) |
| `--report JSON` | Report configuration (JSON format) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Run the complete pipeline
devsynth run-pipeline

# Run the pipeline for a specific target
devsynth run-pipeline --target unit-tests

# Run the pipeline with automatic confirmation
devsynth run-pipeline --auto-confirm
```

### config

View or modify DevSynth configuration.

**Usage:**

```bash
devsynth config [OPTIONS] [KEY] [VALUE]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--key TEXT` | Configuration key to get or set |
| `--value TEXT` | Value to set for the configuration key |
| `--list-models / --no-list-models` | List available configuration models (default: False) |

**Examples:**

```bash
# List all configuration settings
devsynth config

# Set the default language
devsynth config language python

# Get a specific configuration value
devsynth config provider

# List available configuration models
devsynth config --list-models
```

### completion

Generate or install shell completion scripts.

**Usage:**

```bash
devsynth completion [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--shell [bash\|zsh\|fish]` | Target shell (auto-detected by default) |
| `--install` | Install completion for the selected shell |
| `--output TEXT` | Write completion script to a file |

**Examples:**

```bash
# Install completion for the current shell
devsynth completion --install

# Generate zsh completion script to a file
devsynth completion --shell zsh --output devsynth.zsh
```

## Advanced Commands

### gather

Run the requirements gathering wizard.

**Usage:**

```bash
devsynth gather [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output-file TEXT` | Path where the requirements will be written (default: requirements_plan.yaml) |

**Examples:**

```bash
# Run the requirements gathering wizard
devsynth gather

# Run the wizard and save to a custom file
devsynth gather --output-file docs/requirements.yaml
```

### refactor

Suggest refactoring improvements for code.

**Usage:**

```bash
devsynth refactor [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--path TEXT` | Path to the file or directory to refactor |

**Examples:**

```bash
# Suggest refactoring improvements for the current project
devsynth refactor

# Suggest refactoring improvements for a specific file
devsynth refactor --path src/main.py

# Suggest refactoring improvements for a specific directory
devsynth refactor --path src/models
```

### inspect

Inspect and analyze requirements or code.

**Usage:**

```bash
devsynth inspect [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--input-file TEXT` | Path to the file to inspect |
| `--interactive / --no-interactive` | Run in interactive mode (default: False) |

**Examples:**

```bash
# Inspect the current project
devsynth inspect

# Inspect a specific file
devsynth inspect --input-file requirements.md

# Inspect a file in interactive mode
devsynth inspect --input-file src/main.py --interactive
```

### webapp

Generate a web application scaffold.

**Usage:**

```bash
devsynth webapp [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--framework TEXT` | Web framework to use (default: flask) |
| `--name TEXT` | Name of the web application (default: webapp) |
| `--path TEXT` | Path where the web application will be generated (default: .) |
| `--force / --no-force` | Force overwrite existing files (default: False) |

**Examples:**

```bash
# Generate a Flask web application
devsynth webapp

# Generate a Django web application
devsynth webapp --framework django

# Generate a web application with a custom name
devsynth webapp --name my_webapp

# Generate a web application in a specific directory
devsynth webapp --path apps
```

### serve

Start the DevSynth API server.

**Usage:**

```bash
devsynth serve [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--host TEXT` | Host to bind to (default: 0.0.0.0) |
| `--port INTEGER` | Port to bind to (default: 8000) |

**Examples:**

```bash
# Start the API server
devsynth serve

# Start the API server on a custom host and port
devsynth serve --host 127.0.0.1 --port 9000
```

### dbschema

Generate database schema from models.

**Usage:**

```bash
devsynth dbschema [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--db-type TEXT` | Database type (default: sqlite) |
| `--name TEXT` | Name of the database (default: database) |
| `--path TEXT` | Path where the schema will be generated (default: .) |
| `--force / --no-force` | Force overwrite existing files (default: False) |

**Examples:**

```bash
# Generate a SQLite schema
devsynth dbschema

# Generate a PostgreSQL schema
devsynth dbschema --db-type postgresql

# Generate a schema with a custom name
devsynth dbschema --name my_database

# Generate a schema in a specific directory
devsynth dbschema --path db
```

## Diagnostic Commands

### doctor

Check the health of your DevSynth installation and project.

**Usage:**

```bash
devsynth doctor [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--config-dir TEXT` | Path to the configuration directory (default: config) |

**Examples:**

```bash
# Check the health of the current project
devsynth doctor

# Check the health with a custom configuration directory
devsynth doctor --config-dir custom_config
```

### check

Check the configuration of your DevSynth project.

**Usage:**

```bash
devsynth check [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--config-dir TEXT` | Path to the configuration directory (default: config) |

**Examples:**

```bash
# Check the configuration of the current project
devsynth check

# Check the configuration with a custom configuration directory
devsynth check --config-dir custom_config
```

### webui

Start the DevSynth Web UI.

**Usage:**

```bash
devsynth webui [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| No specific options |

**Examples:**

```bash
# Start the Web UI
devsynth webui
```

### edrr-cycle

Run an Expand-Differentiate-Refine-Reflect cycle.

**Usage:**

```bash
devsynth edrr-cycle [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| No specific options documented in the implementation |

**Examples:**

```bash
# Run an EDRR cycle
devsynth edrr-cycle
```

## Environment Variables

DevSynth respects the following environment variables:

| Variable | Description |
|----------|-------------|
| `DEVSYNTH_CONFIG` | Path to the configuration file |
| `DEVSYNTH_PROVIDER` | Default Provider to use |
| `OPENAI_API_KEY` | API key for OpenAI |
| `ANTHROPIC_API_KEY` | API key for Anthropic |
| `DEVSYNTH_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `DEVSYNTH_CACHE_DIR` | Directory for caching data |
| `DEVSYNTH_DISABLE_TELEMETRY` | Disable telemetry (set to any value) |

## Configuration File

DevSynth uses a YAML configuration file located at `.devsynth/config.yaml` by default. The configuration file can be modified using the `config` command or by editing it directly.

Example configuration file:

```yaml
# DevSynth Configuration
project:
  name: my-project
  language: python
  version: 0.1.0

llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000

features:
  dialectical_reasoning: true
  peer_review: true
  EDRR: true
  WSDE: true

paths:
  requirements: requirements.md
  specs: specs.md
  tests: tests
  code: src
  docs: docs
```

## Command Cheat Sheet

| Command | Description | Common Options |
|---------|-------------|----------------|
| `init` | Initialize a project | `--wizard`, `--root`, `--language` |
| `spec` | Generate specifications | `--requirements-file` |
| `test` | Generate tests | `--spec-file` |
| `code` | Generate code | |
| `run-pipeline` | Run complete pipeline | `--target` |
| `config` | Configure settings | `--key`, `--value` |
| `gather` | Gather requirements | `--output-file` |
| `refactor` | Suggest refactorings | `--path` |
| `inspect` | Analyze requirements/code | `--input-file`, `--interactive` |
| `webapp` | Generate web application | `--framework`, `--name`, `--path` |
| `serve` | Start API server | `--host`, `--port` |
| `dbschema` | Generate database schema | `--db-type`, `--name`, `--path` |
| `doctor` | Check installation health | `--config-dir` |
| `check` | Check configuration | `--config-dir` |
| `webui` | Start Web UI | |
| `edrr-cycle` | Run EDRR cycle | |

## Common Workflows

### Basic Project Setup

```bash
# Provision the environment (installs go-task and ensures devsynth CLI)
bash scripts/install_dev.sh

# Initialize a new project
devsynth init --wizard

# Gather requirements
devsynth gather

# Generate specifications, tests, and code
devsynth run-pipeline
```

### Incremental Development

```bash
# Update specifications from requirements
devsynth spec

# Generate tests from updated specifications
devsynth test

# Generate code from updated tests
devsynth code
```

### Project Analysis

```bash
# Check project health
devsynth doctor

# Inspect requirements
devsynth inspect --input-file requirements.md

# Suggest refactoring improvements
devsynth refactor
```

### Web Development

```bash
# Generate a web application
devsynth webapp --framework flask

# Generate a database schema
devsynth dbschema --db-type postgresql

# Start the API server
devsynth serve
```

## Conclusion

This reference covers all the DevSynth CLI commands and their options. For more detailed information about specific features or workflows, refer to the DevSynth documentation or use the `--help` option with any command.
