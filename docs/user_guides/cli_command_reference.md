---
author: DevSynth Team
date: '2025-07-07'
last_reviewed: '2025-07-07'
status: published
tags:

- user-guide
- cli
- reference

title: DevSynth CLI Command Reference
version: 1.0.0
---

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
| `--path TEXT` | Path where the project will be initialized (default: current directory) |
| `--project-root TEXT` | Root directory of the project (if different from path) |
| `--language TEXT` | Primary programming language for the project |
| `--goals TEXT` | High-level goals or description of the project |

**Examples:**

```bash

# Initialize a new project in the current directory

devsynth init

# Initialize a new Python project in ./my-project

devsynth init --path ./my-project --language python

# Initialize a project with specific goals

devsynth init --goals "A CLI tool for managing tasks"
```

## spec

Generate specifications from requirements.

**Usage:**

```bash
devsynth spec [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--requirements-file TEXT` | Path to the requirements file (default: requirements.md) |
| `--output-file TEXT` | Path where the specifications will be written (default: specs.md) |
| `--format TEXT` | Output format (markdown, json, yaml) (default: markdown) |

**Examples:**

```bash

# Generate specifications from the default requirements file

devsynth spec

# Generate specifications from a custom requirements file

devsynth spec --requirements-file docs/requirements.md

# Generate specifications in JSON format

devsynth spec --format json
```

## test

Generate tests from specifications.

**Usage:**

```bash
devsynth test [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--spec-file TEXT` | Path to the specifications file (default: specs.md) |
| `--output-dir TEXT` | Directory where the tests will be generated (default: tests) |
| `--framework TEXT` | Test framework to use (pytest, unittest) (default: pytest) |

**Examples:**

```bash

# Generate tests from the default specifications file

devsynth test

# Generate tests from a custom specifications file

devsynth test --spec-file docs/specs.md

# Generate tests using unittest framework

devsynth test --framework unittest
```

## code

Generate code from tests.

**Usage:**

```bash
devsynth code [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output-dir TEXT` | Directory where the code will be generated (default: src) |
| `--language TEXT` | Programming language to use (default: from project config) |

**Examples:**

```bash

# Generate code from tests

devsynth code

# Generate code in a custom directory

devsynth code --output-dir lib

# Generate code in a specific language

devsynth code --language typescript
```

## run-pipeline

Run the complete synthesis pipeline (spec, test, code).

**Usage:**

```bash
devsynth run-pipeline [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target TEXT` | Target component to synthesize (unit, integration, all) |
| `--requirements-file TEXT` | Path to the requirements file (default: requirements.md) |

**Examples:**

```bash

# Run the complete pipeline

devsynth run-pipeline

# Run the pipeline for unit tests only

devsynth run-pipeline --target unit

# Run the pipeline with a custom requirements file

devsynth run-pipeline --requirements-file docs/requirements.md
```

## config

View or modify DevSynth configuration.

**Usage:**

```bash
devsynth config [OPTIONS] [KEY] [VALUE]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--list` | List all configuration settings |
| `--reset` | Reset configuration to default values |
| `--file TEXT` | Path to the configuration file (default: .devsynth/config.yaml) |

**Examples:**

```bash

# List all configuration settings

devsynth config --list

# Set the default language

devsynth config language python

# Reset configuration to default values

devsynth config --reset
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
| `--interactive` | Run in interactive mode (default: True) |

**Examples:**

```bash

# Run the requirements gathering wizard

devsynth gather

# Run the wizard and save to a custom file

devsynth gather --output-file docs/requirements.yaml
```

## inspect

Inspect and analyze requirements or code.

**Usage:**

```bash
devsynth inspect [OPTIONS] [FILE]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--interactive` | Run in interactive mode (default: False) |
| `--output-file TEXT` | Path where the analysis will be written |

**Examples:**

```bash

# Inspect a requirements file

devsynth inspect requirements.md

# Inspect a code file interactively

devsynth inspect src/main.py --interactive

# Inspect a requirements file and save the analysis

devsynth inspect requirements.md --output-file analysis.md
```

## refactor

Suggest refactoring improvements for code.

**Usage:**

```bash
devsynth refactor [OPTIONS] [FILE]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output-file TEXT` | Path where the refactored code will be written |
| `--apply` | Apply the suggested refactorings (default: False) |

**Examples:**

```bash

# Suggest refactoring improvements for a file

devsynth refactor src/main.py

# Apply refactoring improvements to a file

devsynth refactor src/main.py --apply

# Save refactored code to a new file

devsynth refactor src/main.py --output-file src/main_refactored.py
```

## webapp

Generate a web application scaffold.

**Usage:**

```bash
devsynth webapp [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--framework TEXT` | Web framework to use (flask, django, fastapi) |
| `--output-dir TEXT` | Directory where the web application will be generated (default: webapp) |

**Examples:**

```bash

# Generate a Flask web application

devsynth webapp --framework flask

# Generate a Django web application in a custom directory

devsynth webapp --framework django --output-dir my_webapp
```

## serve

Start the DevSynth API server.

**Usage:**

```bash
devsynth serve [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--host TEXT` | Host to bind to (default: 127.0.0.1) |
| `--port INTEGER` | Port to bind to (default: 8000) |
| `--reload` | Enable auto-reload on code changes (default: False) |

**Examples:**

```bash

# Start the API server

devsynth serve

# Start the API server on a custom host and port

devsynth serve --host 0.0.0.0 --port 9000

# Start the API server with auto-reload

devsynth serve --reload
```

## dbschema

Generate database schema from models.

**Usage:**

```bash
devsynth dbschema [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--models-dir TEXT` | Directory containing the models (default: src/models) |
| `--output-file TEXT` | Path where the schema will be written (default: schema.sql) |
| `--dialect TEXT` | SQL dialect to use (sqlite, postgresql, mysql) (default: sqlite) |

**Examples:**

```bash

# Generate a SQLite schema from models

devsynth dbschema

# Generate a PostgreSQL schema from models in a custom directory

devsynth dbschema --models-dir app/models --dialect postgresql

# Generate a schema and save it to a custom file

devsynth dbschema --output-file db/schema.sql
```

## webui

Start the DevSynth Web UI.

**Usage:**

```bash
devsynth webui [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--port INTEGER` | Port to bind to (default: 8501) |
| `--browser` | Open the Web UI in a browser (default: True) |

**Examples:**

```bash

# Start the Web UI

devsynth webui

# Start the Web UI on a custom port

devsynth webui --port 9501

# Start the Web UI without opening a browser

devsynth webui --browser=False
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
| `--path TEXT` | Path to the project directory (default: current directory) |
| `--fix` | Attempt to fix issues automatically (default: False) |

**Examples:**

```bash

# Check the health of the current project

devsynth doctor

# Check the health of a project in a custom directory

devsynth doctor --path ./my-project

# Check the health and fix issues automatically

devsynth doctor --fix
```

## EDRR-cycle

Run an Expand-Differentiate-Refine-Reflect cycle.

**Usage:**

```bash
devsynth EDRR-cycle [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--prompt TEXT` | Prompt for the EDRR |
| `--context TEXT` | Additional context for the EDRR |
| `--max-iterations INTEGER` | Maximum number of iterations (default: 3) |

**Examples:**

```bash

# Run an EDRR with a prompt

devsynth EDRR-cycle --prompt "Improve error handling in the API endpoints"

# Run an EDRR with a prompt and context

devsynth EDRR-cycle --prompt "Optimize database queries" --context "Focus on reducing N+1 queries"

# Run an EDRR with a custom number of iterations

devsynth EDRR-cycle --prompt "Refactor the authentication system" --max-iterations 5
```

## align

Align code with requirements.

**Usage:**

```bash
devsynth align [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--code-dir TEXT` | Directory containing the code (default: src) |
| `--requirements-file TEXT` | Path to the requirements file (default: requirements.md) |
| `--output-file TEXT` | Path where the alignment report will be written (default: alignment.md) |

**Examples:**

```bash

# Check alignment between code and requirements

devsynth align

# Check alignment with custom paths

devsynth align --code-dir app --requirements-file docs/requirements.md

# Check alignment and save the report to a custom file

devsynth align --output-file reports/alignment.md
```

## alignment-metrics

Generate metrics for code-requirements alignment.

**Usage:**

```bash
devsynth alignment-metrics [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--code-dir TEXT` | Directory containing the code (default: src) |
| `--requirements-file TEXT` | Path to the requirements file (default: requirements.md) |
| `--output-file TEXT` | Path where the metrics will be written (default: metrics.json) |
| `--format TEXT` | Output format (json, yaml, markdown) (default: json) |

**Examples:**

```bash

# Generate alignment metrics

devsynth alignment-metrics

# Generate alignment metrics with custom paths

devsynth alignment-metrics --code-dir app --requirements-file docs/requirements.md

# Generate alignment metrics in markdown format

devsynth alignment-metrics --format markdown
```

## inspect-config

Inspect and analyze project configuration.

**Usage:**

```bash
devsynth inspect-config [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output-file TEXT` | Path where the analysis will be written |

**Examples:**

```bash

# Inspect project configuration

devsynth inspect-config

# Inspect project configuration and save the analysis

devsynth inspect-config --output-file config_analysis.md
```

## validate-manifest

Validate the Project Configuration.

**Usage:**

```bash
devsynth validate-manifest [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--manifest-file TEXT` | Path to the manifest file (default: .devsynth/Project Configuration) |
| `--fix` | Attempt to fix issues automatically (default: False) |

**Examples:**

```bash

# Validate the Project Configuration

devsynth validate-manifest

# Validate a custom manifest file

devsynth validate-manifest --manifest-file custom_manifest.yaml

# Validate the manifest and fix issues automatically

devsynth validate-manifest --fix
```

## validate-metadata

Validate the project metadata.

**Usage:**

```bash
devsynth validate-metadata [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--metadata-file TEXT` | Path to the metadata file (default: .devsynth/metadata.yaml) |
| `--fix` | Attempt to fix issues automatically (default: False) |

**Examples:**

```bash

# Validate the project metadata

devsynth validate-metadata

# Validate a custom metadata file

devsynth validate-metadata --metadata-file custom_metadata.yaml

# Validate the metadata and fix issues automatically

devsynth validate-metadata --fix
```

## test-metrics

Generate metrics for test coverage and quality.

**Usage:**

```bash
devsynth test-metrics [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--tests-dir TEXT` | Directory containing the tests (default: tests) |
| `--code-dir TEXT` | Directory containing the code (default: src) |
| `--output-file TEXT` | Path where the metrics will be written (default: test_metrics.json) |
| `--format TEXT` | Output format (json, yaml, markdown) (default: json) |

**Examples:**

```bash

# Generate test metrics

devsynth test-metrics

# Generate test metrics with custom paths

devsynth test-metrics --tests-dir custom_tests --code-dir app

# Generate test metrics in markdown format

devsynth test-metrics --format markdown
```

## generate-docs

Generate documentation from code.

**Usage:**

```bash
devsynth generate-docs [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--code-dir TEXT` | Directory containing the code (default: src) |
| `--output-dir TEXT` | Directory where the documentation will be generated (default: docs) |
| `--format TEXT` | Output format (markdown, html, pdf) (default: markdown) |

**Examples:**

```bash

# Generate documentation from code

devsynth generate-docs

# Generate documentation with custom paths

devsynth generate-docs --code-dir app --output-dir api_docs

# Generate documentation in HTML format

devsynth generate-docs --format html
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

## Conclusion

This reference covers all the DevSynth CLI commands and their options. For more detailed information about specific features or workflows, refer to the DevSynth documentation or use the `--help` option with any command.