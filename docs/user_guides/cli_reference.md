---
title: "DevSynth CLI Reference"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "cli"
  - "reference"
  - "commands"
  - "user-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# DevSynth CLI Reference

This document provides a comprehensive reference for the DevSynth Command Line Interface (CLI). It covers all available commands, their options, and usage examples.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Command Reference](#command-reference)
  - [help](#help)
  - [init](#init)
  - [spec](#spec)
  - [test](#test)
  - [code](#code)
  - [run](#run)
  - [config](#config)
  - [memory](#memory)
  - [agent](#agent)
- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [Examples](#examples)

## Installation

The DevSynth CLI is installed automatically when you install the DevSynth package:

```bash
pip install devsynth
```

After installation, the `devsynth` command should be available in your terminal.

## Global Options

These options can be used with any command:

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable verbose output | False |
| `--quiet`, `-q` | Suppress all output except errors | False |
| `--config-file` | Path to configuration file | ~/.devsynth/config.yaml |
| `--log-level` | Set logging level (debug, info, warning, error) | info |
| `--help`, `-h` | Show help message and exit | - |

## Command Reference

### help

Display help information about DevSynth commands.

```bash
devsynth help [COMMAND]
```

**Arguments:**
- `COMMAND` (optional): The command to get help for

**Examples:**
```bash
# Show general help
devsynth help

# Show help for the 'init' command
devsynth help init
```

### init

Initialize a new DevSynth project.

```bash
devsynth init [--path PATH] [--template TEMPLATE]
```

**Options:**
- `--path`, `-p`: Path to initialize the project (default: current directory)
- `--template`, `-t`: Template to use for initialization (default: basic)

**Examples:**
```bash
# Initialize in current directory
devsynth init

# Initialize in a specific directory with a specific template
devsynth init --path ./my-project --template web-app
```

### spec

Generate specifications from requirements.

```bash
devsynth spec [--requirements-file FILE] [--output-file FILE]
```

**Options:**
- `--requirements-file`, `-r`: Path to requirements file (default: requirements.md)
- `--output-file`, `-o`: Path to output specification file (default: specifications.md)

**Examples:**
```bash
# Generate specifications from default requirements file
devsynth spec

# Generate specifications from a specific requirements file
devsynth spec --requirements-file custom_requirements.md --output-file custom_specs.md
```

### test

Generate tests from specifications.

```bash
devsynth test [--spec-file FILE] [--output-dir DIR] [--test-type TYPE]
```

**Options:**
- `--spec-file`, `-s`: Path to specification file (default: specifications.md)
- `--output-dir`, `-o`: Directory to output test files (default: tests/)
- `--test-type`, `-t`: Type of tests to generate (unit, integration, behavior) (default: all)

**Examples:**
```bash
# Generate all test types from default specification file
devsynth test

# Generate only unit tests from a specific specification file
devsynth test --spec-file custom_specs.md --test-type unit
```

### code

Generate code from tests or specifications.

```bash
devsynth code [--test-dir DIR] [--spec-file FILE] [--output-dir DIR]
```

**Options:**
- `--test-dir`, `-t`: Directory containing test files (default: tests/)
- `--spec-file`, `-s`: Path to specification file (default: specifications.md)
- `--output-dir`, `-o`: Directory to output code files (default: src/)

**Examples:**
```bash
# Generate code from tests
devsynth code

# Generate code from a specific specification file
devsynth code --spec-file custom_specs.md --output-dir custom_src/
```

### run

Execute generated code or tests.

```bash
devsynth run [--target TARGET]
```

**Options:**
- `--target`, `-t`: Target to run (unit-tests, integration-tests, behavior-tests, application) (default: application)

**Examples:**
```bash
# Run the application
devsynth run

# Run unit tests
devsynth run --target unit-tests
```

### config

Configure DevSynth settings.

```bash
devsynth config [--key KEY] [--value VALUE] [--list] [--reset]
```

**Options:**
- `--key`, `-k`: Configuration key to set or get
- `--value`, `-v`: Value to set for the specified key
- `--list`, `-l`: List all configuration settings
- `--reset`, `-r`: Reset configuration to default values

**Examples:**
```bash
# List all configuration settings
devsynth config --list

# Set a configuration value
devsynth config --key model --value gpt-4

# Get a configuration value
devsynth config --key model

# Reset configuration to defaults
devsynth config --reset
```

### memory

Manage the DevSynth memory system.

```bash
devsynth memory [--clear] [--backup FILE] [--restore FILE] [--list] [--type TYPE]
```

**Options:**
- `--clear`, `-c`: Clear the memory store
- `--backup`, `-b`: Backup memory to a file
- `--restore`, `-r`: Restore memory from a file
- `--list`, `-l`: List memory contents
- `--type`, `-t`: Memory store type (vector, document, graph, all) (default: all)

**Examples:**
```bash
# List all memory contents
devsynth memory --list

# Clear vector memory
devsynth memory --clear --type vector

# Backup all memory to a file
devsynth memory --backup memory_backup.json

# Restore memory from a file
devsynth memory --restore memory_backup.json
```

### agent

Manage and interact with DevSynth agents.

```bash
devsynth agent [--list] [--run AGENT] [--input FILE] [--output FILE]
```

**Options:**
- `--list`, `-l`: List available agents
- `--run`, `-r`: Run a specific agent
- `--input`, `-i`: Input file for the agent
- `--output`, `-o`: Output file for agent results

**Examples:**
```bash
# List all available agents
devsynth agent --list

# Run a specific agent with input and output files
devsynth agent --run documentation --input requirements.md --output docs.md
```

## Environment Variables

DevSynth uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVSYNTH_PROVIDER` | Default LLM provider | openai |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OPENAI_MODEL` | OpenAI model to use | gpt-4 |
| `LM_STUDIO_ENDPOINT` | LM Studio API endpoint | http://127.0.0.1:1234 |
| `SERPER_API_KEY` | Serper API key for web searches | None |
| `DEVSYNTH_CONFIG_PATH` | Path to configuration file | ~/.devsynth/config.yaml |
| `DEVSYNTH_MEMORY_PATH` | Path to memory storage | ~/.devsynth/memory |

## Configuration File

DevSynth uses a YAML configuration file located at `~/.devsynth/config.yaml` by default. You can specify a different location using the `--config-file` option or the `DEVSYNTH_CONFIG_PATH` environment variable.

Example configuration file:

```yaml
# LLM Provider Configuration
provider:
  name: openai
  model: gpt-4
  temperature: 0.7

# Memory Configuration
memory:
  vector_store: chromadb
  document_store: tinydb
  graph_store: rdflib
  path: ~/.devsynth/memory

# Project Configuration
project:
  default_path: ~/projects
  templates_path: ~/.devsynth/templates

# Logging Configuration
logging:
  level: info
  file: ~/.devsynth/logs/devsynth.log
```

## Examples

### Complete Workflow Example

```bash
# Initialize a new project
devsynth init --path ./my-project

# Generate specifications from requirements
devsynth spec --requirements-file requirements.md

# Generate tests from specifications
devsynth test --spec-file specifications.md

# Generate code from tests
devsynth code --test-dir tests/

# Run the tests to verify the implementation
devsynth run --target unit-tests

# Run the application
devsynth run
```

### Configuration Example

```bash
# Set the LLM model to use
devsynth config --key provider.model --value gpt-4

# Set the memory path
devsynth config --key memory.path --value ./custom_memory

# List all configuration settings
devsynth config --list
```

### Memory Management Example

```bash
# List all memory contents
devsynth memory --list

# Backup memory before making changes
devsynth memory --backup memory_backup.json

# Clear all memory
devsynth memory --clear

# Restore memory from backup
devsynth memory --restore memory_backup.json
```

---

For more information, see the [User Guide](user_guide.md) and [Configuration Guide](../technical_reference/configuration_reference.md).