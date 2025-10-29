---

author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-07-10"
status: published
tags:

- cli
- reference
- commands
- user-guide

title: DevSynth CLI Reference
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth CLI Reference
</div>

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
  - [run-pipeline](#run-pipeline)
  - [config](#config)
  - [inspect](#inspect)
  - [gather](#gather)
  - [webapp](#webapp)
  - [webui](#webui)
  - [dbschema](#dbschema)
  - [doctor](#doctor-check)
  - [check](#doctor-check)
  - [refactor](#refactor)
  - [inspect-code](#inspect-code)
  - [EDRR-cycle](#EDRR-cycle)
  - [align](#align)
  - [alignment-metrics](#alignment-metrics)
  - [inspect-config](#inspect-config)
  - [validate-manifest](#validate-manifest)
  - [validate-metadata](#validate-metadata)
  - [test-metrics](#test-metrics)
  - [generate-docs](#generate-docs)
  - [ingest](#ingest)
  - [apispec](#apispec)
  - [serve](#serve)
  - [completion](#completion)
  - [mvu](#mvu)
- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [Examples](#examples)


## Installation

The DevSynth CLI is installed automatically when you install the DevSynth package.
For most users installing from PyPI using Poetry is sufficient:

```bash
poetry add devsynth
```

You can also use `pipx` *(end-user install)* for an isolated environment:

```bash
pipx install devsynth
```

For development from source, use a Poetry-managed environment instead of pip.

After installation, the `devsynth` command should be available in your terminal.

## Global Options

These options can be used with any command:

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable verbose output | False |
| `--quiet`, `-q` | Suppress all output except errors | False |
| `--config-file` | Path to configuration file | ~/.devsynth/config.yaml |
| `--log-level` | Set logging level (debug, info, warning, error) | info |
| `--dashboard-hook` | Python path to function receiving dashboard metric events | - |
| `--help`, `-h` | Show help message and exit | - |

## Command Reference

The following commands are available via `devsynth`:

```text
init
spec
test
code
run-pipeline
config
inspect
gather
webapp
webui
dbschema
doctor (alias: check)
refactor
inspect-code
EDRR-cycle
align
alignment-metrics
inspect-config
validate-manifest
validate-metadata
test-metrics
generate-docs
ingest
apispec
serve
completion
mvu
```

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

## init

Initialize a new DevSynth project or onboard an existing one.

```bash
devsynth init [--path PATH] [--template TEMPLATE] [--project-root ROOT] [--language LANG]
             [--source-dirs DIRS] [--test-dirs DIRS] [--docs-dirs DIRS]
             [--extra-languages LANGS] [--goals TEXT] [--constraints FILE]
             [--wizard] [--metrics-dashboard]
```

**Options:**

- `--path`, `-p`: Path to initialize the project (default: current directory)
- `--template`, `-t`: Template to use for initialization (default: basic)
- `--project-root`: Root directory of an existing project to onboard
- `--language`: Primary language of the project (default: python). Supported
  values: `python`, `javascript`, `typescript`, `go`, `rust`, `haskell`, `julia`,
  or `polyglot` for multi-language projects.
- `--source-dirs`: Comma separated list of source directories (default: src)
- `--test-dirs`: Comma separated list of test directories (default: tests)
- `--docs-dirs`: Comma separated list of documentation directories (default: docs)
- `--extra-languages`: Additional languages used in the project (comma-separated)
  using the same language names as `--language`.
- `--goals`: High-level goals or constraints for the project
- `--constraints`: Path to a constraint configuration file
- `--wizard`: Launch the guided setup wizard even outside a detected project
- `--metrics-dashboard`: Print instructions for enabling the optional MVUU metrics dashboard


This command detects existing projects and launches an interactive wizard when run inside a directory containing `pyproject.toml` or `project.yaml`. Use the `--wizard` flag to start the wizard explicitly in any directory. The command uses provided options and `DEVSYNTH_INIT_*` environment variables directly, prompting only for missing values. Supplying `--defaults` or `--non-interactive` skips prompts entirely.
The wizard presents a streamlined, step-by-step flow with progress indicators and optional quick presets (`minimal`, `standard`, `advanced`).
Progress messages show when configuration is saved and when scaffolding files are generated.
The wizard reads configuration using the [Unified Config Loader](../implementation/config_loader_workflow.md),
which prefers the `[tool.devsynth]` table in `pyproject.toml` when both files are present.
During the wizard you will:

1. Select the memory backend (``memory``, ``file``, ``Kuzu`` or ``ChromaDB``).
2. Choose whether to enable optional features such as ``wsde_collaboration`` and ``dialectical_reasoning``.
3. Decide if DevSynth should operate in offline mode.

Developers writing custom commands can leverage the progress utilities to show
step-based status updates:

```python
from devsynth.interface.progress_utils import step_progress

with step_progress(bridge, ["Saving configuration", "Generating project files"]) as progress:
    progress.advance(status="writing config")
    # perform work
    progress.advance(status="scaffolding")
    # perform next step
```


The resulting `.devsynth/project.yaml` is validated against
`project_schema.json` using `jsonschema` to ensure a well-formed project
manifest.

When offline mode is enabled the CLI uses the settings under
`offline_provider`. Set `offline_provider.model_path` to a local HuggingFace
model so generation commands work without network access. Be aware that offline
mode disables remote LLM capabilities including streaming responses and
third-party integrations. The built-in provider focuses on deterministic output
for testing rather than high quality completions.

**Examples:**

```bash

# Initialize in current directory

devsynth init

# Initialize in a specific directory with a specific template

devsynth init --path ./my-project --template web-app

# Onboard an existing project using custom language

devsynth init --project-root ./existing --language typescript

# Provide directories and project goals via flags

devsynth init --project-root . --language python \
  --source-dirs src --test-dirs tests --docs-dirs docs \
  --extra-languages javascript,go --goals "demo"

# Start the guided wizard directly

devsynth init --wizard
```

## inspect

Generate specifications from requirements.

```bash
devsynth inspect [--requirements-file FILE] [--output-file FILE]
```

**Options:**

- `--requirements-file`, `-r`: Path to requirements file (default: requirements.md)
- `--output-file`, `-o`: Path to output specification file (default: specifications.md)


**Examples:**

```bash

# Generate specifications from default requirements file

devsynth inspect

# Generate specifications from a specific requirements file

devsynth inspect --requirements-file custom_requirements.md --output-file custom_specs.md
```

## run-pipeline

Generate tests from specifications.

```bash
devsynth run-pipeline [--spec-file FILE] [--output-dir DIR] [--test-type TYPE]
```

**Options:**

- `--spec-file`, `-s`: Path to specification file (default: specifications.md)
- `--output-dir`, `-o`: Directory to output test files (default: tests/)
- `--test-type`, `-t`: Type of tests to generate (unit, integration, behavior) (default: all)


**Examples:**

```bash

# Generate all test types from default specification file

devsynth run-pipeline

# Generate only unit tests from a specific specification file

devsynth run-pipeline --spec-file custom_specs.md --test-type unit
```

## refactor

Generate code from tests or specifications.

```bash
devsynth refactor [--test-dir DIR] [--spec-file FILE] [--output-dir DIR]
```

**Options:**

- `--test-dir`, `-t`: Directory containing test files (default: tests/)
- `--spec-file`, `-s`: Path to specification file (default: specifications.md)
- `--output-dir`, `-o`: Directory to output code files (default: src/)
- `--language`, `-l`: Target language for generated code. Supported values are
  `python`, `javascript`, `typescript`, `go`, `rust`, `haskell`, `julia`, or
  `polyglot`.


**Examples:**

```bash

# Generate code from tests

devsynth refactor

# Generate code from a specific specification file

devsynth refactor --spec-file custom_specs.md --output-dir custom_src/

# Generate TypeScript code

devsynth refactor --language typescript
```

## run-pipeline

Execute generated code or tests.

```bash
devsynth run-pipeline [--target TARGET]
```

**Options:**

- `--target`, `-t`: Target to run (unit-tests, integration-tests, behavior-tests, application) (default: application)


**Examples:**

```bash

# Run the application

devsynth run-pipeline

# Run unit tests

devsynth run-pipeline --target unit-tests
```

## config

Configure DevSynth settings.
Configuration values are loaded through a unified loader that reads YAML or TOML files.
The loader first checks `pyproject.toml` for a `[tool.devsynth]` table and falls back
to `.devsynth/project.yaml` if that section is missing. See the
[Unified Configuration Loader specification](../specifications/unified_configuration_loader.md)
for details.

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

## enable-feature

Toggle a feature flag in your project configuration.

```bash
devsynth config enable-feature <name>
```

### Feature Flags

The `config enable-feature` command toggles optional capabilities defined in
the configuration file. The default feature flags are:

| Flag | Default |
|------|---------|
| `wsde_collaboration` | `true` |
| `dialectical_reasoning` | `false` |
| `code_generation` | `false` |
| `test_generation` | `false` |
| `documentation_generation` | `false` |
| `prompt_auto_tuning` | `false` |
| `automatic_phase_transitions` | `true` |
| `collaboration_notifications` | `true` |

If every feature is disabled, the CLI emits a warning at startup. This behaviour
is implemented in
`src/devsynth/adapters/cli/typer_adapter.py` via the `_warn_if_features_disabled`
helper.

**Example:**

```bash
devsynth config enable-feature code_generation
```

### run-pipeline

Execute a predefined pipeline of DevSynth commands.

```bash
devsynth run-pipeline <pipeline-name>
```

**Examples:**

```bash
devsynth run-pipeline default
```

### refactor

Analyze the project and suggest an appropriate workflow.

```bash
devsynth refactor [--path PATH]
```

**Options:**

- `--path`, `-p`: Path to the project root (default: current directory)


**Examples:**

```bash
devsynth refactor
devsynth refactor --path ./my-project
```

### inspect

Analyze requirements from a file or interactively.

```bash
devsynth inspect [--input FILE] [--interactive]
```

**Options:**

- `--input`, `-i`: Input file containing requirements
- `--interactive`: Start an interactive session


**Examples:**

```bash
devsynth inspect --input requirements.md
devsynth inspect --interactive
```

### webapp

Generate a simple web application project.

```bash
devsynth webapp [--framework FRAMEWORK] [--name NAME] [--path PATH]
```

**Options:**

- `--framework`, `-f`: Web framework to use (flask, fastapi, django, express)
- `--name`, `-n`: Name of the project (default: webapp)
- `--path`, `-p`: Directory to create the project (default: .)


**Examples:**

```bash
devsynth webapp --framework flask --name demo --path ./apps
```

### webui

Launch the NiceGUI-based graphical interface.

```bash
devsynth webui
```

The WebUI mirrors CLI commands using the same `UXBridge` workflows.

| CLI Command | WebUI Page/Action |
|-------------|------------------|
| `init` | **Onboarding** page – Initialize Project |
| `spec` | **Requirements** page – Generate Specs |
| `inspect` | **Requirements** page – Inspect Requirements |
| `test` | **Synthesis** page – Generate Tests |
| `code` | **Synthesis** page – Generate Code |
| `run-pipeline` | **Synthesis** page – Run Pipeline |
| `config` | **Config** page – Update Settings |

```python

# Pseudocode: WebUI page invoking a CLI workflow

def trigger_action(command: str, **kwargs):
    cli_fn = getattr(cli_commands, f"{command}_cmd")
    cli_fn(**kwargs, bridge=self)  # 'self' implements UXBridge
```

## dbschema

Generate a database schema for a given database type.

```bash
devsynth dbschema [--db-type TYPE] [--name NAME] [--path PATH]
```

**Options:**

- `--db-type`, `-d`: Database type (sqlite, mysql, postgresql, mongodb)
- `--name`, `-n`: Schema name (default: database)
- `--path`, `-p`: Output directory (default: .)


**Examples:**

```bash
devsynth dbschema --db-type sqlite --name blog --path ./schema
```

### doctor / check {#doctor-check}

Validate environment configuration files for common issues. The command is also
available as `devsynth check`.

```bash
devsynth doctor [--config-dir DIR]
devsynth check [--config-dir DIR]
```

If the project configuration fails schema validation, the command raises
``Configuration issues detected. Run 'devsynth init' to generate defaults.``

**Options:**

- `--config-dir`, `-c`: Directory containing environment configs (default: ./config)


**Examples:**

```bash

# Validate default configuration files

devsynth doctor

# Validate a custom configuration directory

devsynth doctor --config-dir ./configs

# Using the alias

devsynth check
```

Typical successful output:

```text
All configuration files are valid.
```

If issues are detected you may see warnings like:

```text
Warning: Python 3.12 or higher is required. Current version: 3.10
Missing environment variables: OPENAI_API_KEY
ChromaDB support is enabled but the 'ChromaDB' package is missing.
Configuration issues detected. Run 'devsynth init' to generate defaults.
```

## Additional commands

The CLI also provides several specialized commands used for advanced workflows.
These commands mirror the names reported by `devsynth --help`:

```text
gather
inspect-code
EDRR-cycle
align
alignment-metrics
inspect-config
validate-manifest
validate-metadata
test-metrics
generate-docs
ingest
apispec
serve
completion
mvu
```

### generate-docs

Generate API reference documentation for the current project.

```bash
devsynth generate-docs [--path PATH] [--output-dir DIR]
```

**Options:**

- `--path PATH`: Project directory to analyze (defaults to the current directory).
- `--output-dir DIR`: Directory for generated documentation (defaults to `docs/api_reference`).

See the [API Reference Generation Guide](api_reference_generation.md) for usage and examples.

### ingest

Run the Expand, Differentiate, Refine, Retrospect pipeline for a project.

```bash
devsynth ingest [MANIFEST] [--non-interactive] [--yes] [--defaults] [--priority PRIORITY]
```

**Options:**

- `MANIFEST` (optional): Path to the project manifest. Defaults to `.devsynth/project.yaml` or `DEVSYNTH_MANIFEST_PATH`.
- `--non-interactive`: Run without prompts.
- `--yes`, `--auto-confirm`: Automatically approve confirmations.
- `--defaults`: Apply sensible defaults and skip prompts (implies `--non-interactive` and `--yes`).
- `--priority`: Set project priority.

**Examples:**

```bash
# Ingest using defaults and no prompts
devsynth ingest --defaults

# Non-interactive ingestion with explicit manifest and high priority
devsynth ingest manifest.yaml --non-interactive --yes --priority high
```

### completion

Generate or install shell completion scripts for the DevSynth CLI. Typer's
built-in completion support is also available via the global
`--install-completion` and `--show-completion` flags.

```bash
devsynth completion [--shell bash|zsh|fish] [--install] [--path PATH]
```

**Options:**

- `--shell`: Target shell. Defaults to the current shell.
- `--install`: Install the completion script into the user's shell configuration.
- `--path`: Write the generated script to a file instead of printing.

**Examples:**

```bash
# Show the completion script for your current shell
devsynth completion

# Install zsh completions
devsynth completion --shell zsh --install

# Write script to file
devsynth completion --shell bash --path ~/.devsynth-completion.bash
```

### mvu

Utilities for Minimal Viable Useful Unit configuration.

#### init

Scaffold `.devsynth/mvu.yml` with default schema path and storage settings.

```bash
devsynth mvu init
```

#### exec

Run a shell command within the MVU workflow and forward its output and exit code.

```bash
devsynth mvu exec echo hello
```

## Environment Variables

DevSynth uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVSYNTH_PROVIDER` | Default Provider | openai |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OPENAI_MODEL` | OpenAI model to use | gpt-4 |
| `LM_STUDIO_ENDPOINT` | LM Studio API endpoint | http://127.0.0.1:1234 |
| `SERPER_API_KEY` | Serper API key for web searches | None |
| `DEVSYNTH_CONFIG_PATH` | Path to configuration file | ~/.devsynth/config.yaml |
| `DEVSYNTH_MEMORY_PATH` | Path to memory storage | ~/.devsynth/memory |
| `DEVSYNTH_MANIFEST_PATH` | Default manifest path for `devsynth ingest` | None |
| `DEVSYNTH_INGEST_DRY_RUN` | Set to `1` to enable `--dry-run` by default | 0 |
| `DEVSYNTH_INGEST_VERBOSE` | Set to `1` to enable verbose ingestion output | 0 |
| `DEVSYNTH_INGEST_VALIDATE_ONLY` | Set to `1` to run only manifest validation | 0 |
| `DEVSYNTH_INGEST_PRIORITY` | Persist project priority without prompting | None |
| `DEVSYNTH_INGEST_AUTO_PHASE_TRANSITIONS` | Set to `0` to require manual EDRR phase transitions | 1 |
| `DEVSYNTH_INGEST_NONINTERACTIVE` | Set to `1` to disable prompts during ingestion | 0 |
| `DEVSYNTH_AUTO_CONFIRM` | Auto-approve prompts across commands | 0 |

## Configuration File

DevSynth uses a YAML configuration file located at `~/.devsynth/config.yaml` by default. You can specify a different location using the `--config-file` option or the `DEVSYNTH_CONFIG_PATH` environment variable.

Example configuration file:

```yaml

# Provider Configuration

provider:
  name: openai
  model: gpt-4
  temperature: 0.7

# Memory Configuration

memory:
  vector_store: ChromaDB
  document_store: TinyDB
  graph_store: RDFLib
  path: ~/.devsynth/memory

# `.devsynth/project.yaml`

project:
  default_path: ~/projects
  templates_path: ~/.devsynth/templates

# Logging Configuration

logging:
  level: info
  file: ~/.devsynth/logs/devsynth.log
```

## Examples

Additional walkthroughs for each command can be found in the `examples` directory:

- [Init](../../examples/init_example)
- [Spec](../../examples/spec_example)
- [Test](../../examples/test_example)
- [Code](../../examples/code_example)
- [EDRR](../../examples/edrr_cycle_example)


### Complete Workflow Example

```bash

# Initialize a new project

devsynth init --path ./my-project

# Generate specifications from requirements

devsynth inspect --requirements-file requirements.md

# Generate tests from specifications

devsynth run-pipeline --spec-file specifications.md

# Generate code from tests

devsynth refactor --test-dir tests/

# Run the tests to verify the implementation

devsynth run-pipeline --target unit-tests

# Run the application

devsynth run-pipeline
```

## Configuration Example

```bash

# Set the LLM model to use

devsynth config --key provider.model --value gpt-4

# Set the memory path

devsynth config --key memory.path --value ./custom_memory

# List all configuration settings

devsynth config --list
```

## Memory Management Example

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

For more information, see the [User Guide](user_guide.md), [Configuration Guide](../technical_reference/configuration_reference.md), and the [Architecture Overview](../architecture/overview.md).


## run-tests

Run DevSynth test suites with stability and reporting options.

```bash
devsynth run-tests [OPTIONS]
```

Options:

- `--target {all-tests|unit-tests|integration-tests|behavior-tests}`: Select test target.
- `--speed <fast|medium|slow>`: Speed category to run; may be repeated to include multiple.
- `--no-parallel`: Disable xdist parallelization.
- `--report`: Produce an HTML report under `test_reports/`.
- `--smoke`: Disable xdist and third-party plugins (sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`).
- `--segment`: Enable batched execution.
- `--segment-size N`: Batch size when segmenting.
- `--maxfail N`: Stop after N failures.
- `--feature name[=true|false]`: Set feature flags mapping to `DEVSYNTH_FEATURE_<NAME>`.

Examples:

```bash
# Fast smoke run, fail on first error, no parallel
poetry run devsynth run-tests --speed fast --smoke --maxfail=1 --no-parallel

# Medium + slow, segmenting into batches of 25
poetry run devsynth run-tests --speed medium --speed slow --segment --segment-size 25

# Generate HTML report and disable parallel
poetry run devsynth run-tests --report --no-parallel
```
