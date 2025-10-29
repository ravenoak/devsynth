---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
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
| `--memory-backend TEXT` | Memory backend to use (default: from config) |
| `--offline-mode / --no-offline-mode` | Enable or disable offline mode |
| `--features JSON` | Features to enable or disable (JSON format) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

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
| `--spec-file TEXT` | Path to the specification file (default: specs.md) |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Generate tests from the default specification file
devsynth test

# Generate tests from a custom specification file
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

### run

Run a pipeline or specific target.

**Usage:**

```bash
devsynth run [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target TEXT` | Target to run (e.g., unit-tests, integration-tests) |
| `--report JSON` | Report configuration in JSON format |
| `--auto-confirm / --no-auto-confirm` | Automatically confirm prompts (default: False) |

**Examples:**

```bash
# Run the default pipeline
devsynth run

# Run unit tests
devsynth run --target unit-tests

# Run with a custom report configuration
devsynth run --report '{"format": "html", "output": "report.html"}'
```

### config

Configure DevSynth settings.

**Usage:**

```bash
devsynth config [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--key TEXT` | Configuration key to set or get |
| `--value TEXT` | Value to set for the specified key |
| `--list-models` | List available configuration models |

**Examples:**

```bash
# View all configuration settings
devsynth config

# Set a specific configuration value
devsynth config --key model --value gpt-4

# List available configuration models
devsynth config --list-models
```

### enable-feature

Enable a specific feature in the DevSynth project.

**Usage:**

```bash
devsynth enable-feature [OPTIONS] NAME
```

**Options:**
| Option | Description |
|--------|-------------|
| `NAME` | Name of the feature to enable |

**Examples:**

```bash
# Enable the multi-agent feature
devsynth enable-feature multi-agent

# Enable the advanced-testing feature
devsynth enable-feature advanced-testing
```

### gather

Gather requirements for a project.

**Usage:**

```bash
devsynth gather [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output-file TEXT` | Path where the requirements plan will be written (default: requirements_plan.yaml) |

**Examples:**

```bash
# Gather requirements with default output
devsynth gather

# Gather requirements with custom output file
devsynth gather --output-file docs/requirements.yaml
```

### refactor

Refactor code in the project.

**Usage:**

```bash
devsynth refactor [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--path TEXT` | Path to the code to refactor (default: current directory) |

**Examples:**

```bash
# Refactor code in the current directory
devsynth refactor

# Refactor code in a specific directory
devsynth refactor --path src/module
```

### inspect

Inspect requirements or other project artifacts.

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
# Inspect requirements interactively
devsynth inspect --interactive

# Inspect a specific file
devsynth inspect --input-file requirements.md
```

### webapp

Generate a web application.

**Usage:**

```bash
devsynth webapp [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--framework TEXT` | Web framework to use (default: flask) |
| `--name TEXT` | Name of the web application (default: webapp) |
| `--path TEXT` | Path where the web application will be generated (default: current directory) |
| `--force / --no-force` | Force overwrite existing files (default: False) |

**Examples:**

```bash
# Generate a Flask web application
devsynth webapp

# Generate a Django web application
devsynth webapp --framework django --name myapp

# Generate a web application in a specific directory
devsynth webapp --path ./web
```

### serve

Serve the application.

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
# Serve the application on the default host and port
devsynth serve

# Serve the application on a specific host and port
devsynth serve --host 127.0.0.1 --port 5000
```

### dbschema

Generate a database schema.

**Usage:**

```bash
devsynth dbschema [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--db-type TEXT` | Database type (default: sqlite) |
| `--name TEXT` | Name of the database (default: database) |
| `--path TEXT` | Path where the schema will be generated (default: current directory) |
| `--force / --no-force` | Force overwrite existing files (default: False) |

**Examples:**

```bash
# Generate a SQLite database schema
devsynth dbschema

# Generate a PostgreSQL database schema
devsynth dbschema --db-type postgresql --name mydb

# Generate a schema in a specific directory
devsynth dbschema --path ./db
```

### doctor

Run diagnostics on the DevSynth installation and project.

**Usage:**

```bash
devsynth doctor [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--config-dir TEXT` | Configuration directory to check (default: config) |

**Examples:**

```bash
# Run diagnostics with default configuration
devsynth doctor

# Run diagnostics on a specific configuration directory
devsynth doctor --config-dir ./custom-config
```

### check

Check the configuration.

**Usage:**

```bash
devsynth check [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--config-dir TEXT` | Configuration directory to check (default: config) |

**Examples:**

```bash
# Check the default configuration
devsynth check

# Check a specific configuration directory
devsynth check --config-dir ./custom-config
```

### webui

Launch the web user interface.

**Usage:**

```bash
devsynth webui [OPTIONS]
```

**Options:**
No specific options.

**Examples:**

```bash
# Launch the web UI
devsynth webui
```

## Advanced Commands

### analysis

Analyze code in the project.

**Usage:**

```bash
devsynth analysis [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--path TEXT` | Path to the code to analyze (default: current directory) |
| `--output-format TEXT` | Output format (default: markdown) |

**Examples:**

```bash
# Analyze code in the current directory
devsynth analysis

# Analyze code in a specific directory with JSON output
devsynth analysis --path src/module --output-format json
```

### apispec

Generate API specifications.

**Usage:**

```bash
devsynth apispec [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--input-file TEXT` | Path to the input file |
| `--output-format TEXT` | Output format (default: openapi) |

**Examples:**

```bash
# Generate API specifications from the default input
devsynth apispec

# Generate API specifications from a specific file
devsynth apispec --input-file api_requirements.md
```

### validate

Validate project artifacts.

**Usage:**

```bash
devsynth validate [OPTIONS] [ARTIFACT_TYPE]
```

**Options:**
| Option | Description |
|--------|-------------|
| `ARTIFACT_TYPE` | Type of artifact to validate (manifest, metadata) |
| `--path TEXT` | Path to the artifact to validate |

**Examples:**

```bash
# Validate the project manifest
devsynth validate manifest

# Validate metadata in a specific file
devsynth validate metadata --path ./metadata.json
```

## Conclusion

This reference covers all available DevSynth CLI commands. For more detailed information about specific commands or workflows, refer to the corresponding user guides and tutorials.
