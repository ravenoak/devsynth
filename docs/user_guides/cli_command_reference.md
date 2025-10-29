---
title: "DevSynth CLI Command Reference"
author: "DevSynth Team"
date: "2025-07-07"
version: "0.1.0a1"
status: "published"
tags:
  - user-guide
  - cli
  - reference
last_reviewed: "2025-08-24"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth CLI Command Reference
</div>

# DevSynth CLI Command Reference

## Introduction

This document provides a comprehensive reference for all DevSynth CLI commands. Each command is explained in detail, including its purpose, options, and usage examples.

### See also
- [Improvement Plan](../plan.md)
- [Improvement Tasks Checklist](../tasks.md)
- [Test Framework README](../../tests/README.md)

## Global Options

### Exit Codes

DevSynth standardizes CLI exit codes so automation and CI can respond predictably:

- 0: Success
- 1: Runtime or unexpected error (e.g., internal failure during command execution)
- 2: Usage or argument error (e.g., invalid flags, bad parameters)

These codes apply to top-level CLI execution via the entry point and when invoking commands with `devsynth ...`.

Global flags are intentionally minimal:

| Option | Description |
|--------|-------------|
| `--help` | Show help information for the current command |
| `--version` | Show DevSynth version and exit |
| `--dashboard-hook module:function` | Register a Python hook function to receive dashboard metric events (top-level option) |
| `--debug` | Enable debug logging (equivalent to `--log-level DEBUG`) |
| `--log-level <LEVEL>` | Set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |

Notes:
- Logging can also be controlled via env: `DEVSYNTH_LOG_LEVEL` or `DEVSYNTH_DEBUG=1`.
- Verbosity and configuration flags remain command-specific and documented per command below.

## CLI Messaging Principles

DevSynth commands follow a few simple rules to ensure messages are clear, concise, and actionable:
- Lead with the problem, then the remedy. Example: "Unknown target 'foo'. Valid values: unit-tests, integration-tests, behavior-tests, all-tests."
- Use exit code 2 for usage errors; include a one-line hint to `--help` with the problematic flag.
- Prefer single-sentence error messages; follow-up with a short suggestion ("Try: devsynth run-tests --help").
- Avoid stack traces for expected user errors; reserve tracebacks for `--debug` or internal errors (exit 1).
- Keep warnings actionable and rate-limited; include the flag or env var to silence or resolve.
- In smoke/offline modes, explicitly confirm that network calls are disabled to set expectations.

These principles are enforced in tests for key commands (see unit tests under `tests/unit/application/cli/commands/`).

## Rich Output Formatting Guidelines

The CLI renders help, summaries, and structured feedback with [Rich](https://rich.readthedocs.io) components. Use the following conventions so layouts remain consistent and accessible across commands:

- Prefer helper utilities (`CommandOutput`, wizard summary builders, or `show_help` helpers) whenever possible; they automatically respect the active theme and sanitization policy.
- When constructing custom tables or panels:
  - Title sections in Title Case and keep borders minimal (`box=None` or `ROUNDED`) to improve screen-reader export text.
  - Use theme style keys such as `heading`, `section`, `command`, `info`, `success`, and `warning` rather than hard-coded colors so colorblind themes render correctly.
  - Sanitize all dynamic strings via `sanitize_output` (or `OutputFormatter`) before adding them to Rich `Text`, `Table`, or `Panel` instances.
- Group related information inside a single panel or layout. For example, summaries should combine configuration, feature toggles, and next steps so duplicate plain-text lines are avoided.
- Provide textual fallbacks: when a bridge lacks a Rich console, export renderables with `Console(record=True).export_text()` and emit the resulting string via the bridge.
- Keep column widths balanced for narrow terminals (aim for ≤ 100 characters) and prefer grid layouts for multi-section output.
- Validate rich output against both standard and colorblind themes before shipping and ensure status indications rely on both color and label text (e.g., "Enabled"/"Disabled").

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

## run-pipeline (alias: run)

Run the pipeline or a specific execution target.

**Usage:**

```bash
devsynth run-pipeline [OPTIONS]
# alias
devsynth run [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target TEXT` | Execution target (unit-tests, integration-tests, behavior-tests, all) |
| `--report TEXT` | JSON string with additional report data to persist |

**Examples:**

```bash
# Run the default pipeline
 devsynth run-pipeline

# Run unit tests target
 devsynth run-pipeline --target unit-tests

# Provide a report payload to persist alongside results
 devsynth run --target all --report '{"build_id": 123, "env": "ci"}'
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

Note: The WebUI is optional. If the `webui` extra (Streamlit) is not installed, the command remains visible but will error gracefully on invocation with guidance to install the extra, for example:

```bash
poetry install --with dev --extras "webui"
```

Imports are lazy/guarded, so `devsynth doctor` and other CLI commands work without Streamlit installed.

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

## run-tests

Run DevSynth test suites with stability and reporting options.

**Usage:**

```bash
poetry run devsynth run-tests [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--target {all-tests|unit-tests|integration-tests|behavior-tests}` | Test target to run (validated) |
| `--speed {fast|medium|slow}` | Speed category to run; repeatable |
| `--report` | Generate an HTML test report (stored under test_reports/) |
| `--verbose` | Show verbose output |
| `--no-parallel` | Disable parallel test execution (disables xdist) |
| `--smoke` | Disable third-party plugins and xdist for maximally stable runs (sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; defaults to `--speed fast` if no speed provided) |
| `--segment` | Run tests in batches |
| `--segment-size INTEGER` | Number of tests per batch when segmenting (default: 50) |
| `--maxfail INTEGER` | Exit after this many failures |
| `--dry-run` | Preview the pytest command without executing tests |
| `--feature TEXT` | Feature flags to set; repeatable; accept `name` or `name=false` (maps to `DEVSYNTH_FEATURE_<NAME>`) |
| `--inventory` | Produce a JSON inventory of collected tests (written to `test_reports/test_inventory.json`) |
| `-m`, `--marker TEXT` | Additional pytest marker expression to AND with speed filters (e.g., `requires_resource('lmstudio') and not slow`) |

Additional behavior:
- In smoke mode, the CLI enforces no parallel execution by default (equivalent to passing `--no-parallel`) and disables xdist and third-party pytest plugins. Passing `--no-parallel` is redundant in smoke mode.
- In smoke mode, a conservative per-test timeout is applied by default: `DEVSYNTH_TEST_TIMEOUT_SECONDS=30` (unless already set).
- For explicit fast-only runs (non-smoke), a slightly looser default timeout is applied: `DEVSYNTH_TEST_TIMEOUT_SECONDS=30` (unless already set).
- `--dry-run` performs test collection and prints the prepared pytest command, making it ideal for validating plugin wiring or marker filters without executing the suite.

**Examples:**
```bash
# Fast smoke run, fail on first error, no parallel
poetry run devsynth run-tests --target unit-tests --speed fast --smoke --maxfail 1 --no-parallel

# Smoke dry-run to verify plugin configuration
poetry run devsynth run-tests --target unit-tests --speed fast --smoke --no-parallel --maxfail 1 --dry-run

# Medium + slow, segmenting into batches of 25
poetry run devsynth run-tests --target all-tests --speed medium --speed slow --segment --segment-size 25

# Slow suite segmented into default-sized batches (50)
poetry run devsynth run-tests --target all-tests --speed slow --segment

# Generate HTML report and disable parallel
poetry run devsynth run-tests --report --no-parallel

# Generate an inventory of collected tests
poetry run devsynth run-tests --inventory

# Scoped inventory to avoid heavy collection:
poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
poetry run devsynth run-tests --inventory --target integration-tests --speed=medium

# Feature flags examples (maps to DEVSYNTH_FEATURE_<NAME>)
poetry run devsynth run-tests --feature EXPERIMENTAL_UI --speed fast
poetry run devsynth run-tests --feature SAFETY_CHECKS=false --speed fast --no-parallel
```

Note on inventory:
- The inventory is written to test_reports/test_inventory.json.
- Scoping by target and speed significantly reduces collection time and avoids timeouts in large repositories.
- If you experience timeouts, prefer running with --smoke and --no-parallel and consult docs/developer_guides/testing.md (Inventory collection constraints and timeouts) for mitigation tips.

Recommendation:
- For medium/slow suites, prefer segmentation with `--segment-size 50` as a starting point. Adjust to 25–100 depending on stability and runtime. Keep `--no-parallel` while triaging flakes.
- Coverage readiness: Always aggregate coverage across fast+medium (and slow when applicable) using the run-tests CLI or combine segmented runs before asserting readiness. Avoid relying on narrow subset runs due to the global fail-under threshold (see docs/plan.md §Coverage aggregation).

Coverage-only profile (documented command):
- To produce authoritative coverage artifacts locally with the global threshold enforced, use one of the following standardized commands:
  - Single-run aggregate (preferred):
    - poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report 2>&1 | tee test_reports/full_fast_medium.log
  - Segmented aggregate (memory-friendly):
    - poetry run devsynth run-tests --speed=fast --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_fast_1.log
    - poetry run devsynth run-tests --speed=medium --segment --segment-size 100 --no-parallel 2>&1 | tee test_reports/seg_medium_1.log
    - poetry run coverage combine && poetry run coverage html -d htmlcov && poetry run coverage json -o coverage.json
- Evidence locations: htmlcov/index.html, coverage.json, test_reports/
- The run-tests command now emits htmlcov/ and coverage.json even when no tests match the selection.

Note on segmentation and collection caching:
- When using --segment, the runner first collects matching tests. This collection is cached to speed up repeated runs.
- Default collection cache TTL is 3600 seconds (1 hour). You can override via env var:
  - DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS=<seconds>

Behavior when no tests match a requested speed:
- For behavior-tests and integration-tests, if a given --speed has no matching tests, the runner will gracefully broaden selection to the default marker filter (equivalent to -m "not memory_intensive") for collection purposes to avoid false negatives in CI. During execution, empty selections are skipped without failing the run.
- This supports stable pipelines where certain speeds may be temporarily absent for a target without causing "no tests ran" failures.

Default resource gating:
- The run-tests CLI applies offline-first defaults and disables optional remote resources unless explicitly enabled (e.g., DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false by default). Tests marked with @pytest.mark.requires_resource(...) will be skipped when their resource is unavailable.
- Provider defaults applied for tests: `DEVSYNTH_PROVIDER=stub`, `DEVSYNTH_OFFLINE=true` (unless already set).

Smoke mode guidance:
- Use `--smoke` to disable third-party plugins and xdist for maximally stable runs.
- Effectively sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and disables parallelism; combine with `--no-parallel` for clarity.
- Applies a conservative default timeout via `DEVSYNTH_TEST_TIMEOUT_SECONDS` unless already set.

### Troubleshooting run-tests

- Plugins hang or unexpected collection behavior:
  - Re-run in smoke mode to disable third-party plugins and xdist:
    - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  - Smoke sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and disables -p no:xdist -p no:cov.
- Excessive runtime or timeouts:
  - Use segmentation to reduce flakiness and memory pressure:
    - poetry run devsynth run-tests --segment --segment-size 50
  - In smoke mode, a tighter timeout is applied by default via DEVSYNTH_TEST_TIMEOUT_SECONDS.
- No tests collected for a given speed:
  - Behavior/integration targets will broaden selection to a safe default; verify your markers with:
    - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Ensure offline-first and deterministic runs:
  - Verify env defaults: DEVSYNTH_PROVIDER=stub, DEVSYNTH_OFFLINE=true.
  - Resource flags default to false; enable explicitly if needed, e.g. export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true.

For broader guidance, see project guidelines and docs/developer_guides/testing.md.

## completion

Show or install shell completion scripts.

**Usage:**

```bash
devsynth completion [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--shell TEXT` | Shell type (e.g., bash, zsh) |
| `--install` | Install completion script |
| `--path TEXT` | Installation path |

**Examples:**

```bash
# Show completion script for current shell
devsynth completion --shell bash

# Install completion to default path
devsynth completion --install

# Install completion to a custom path
devsynth completion --install --path ~/.local/share/bash-completion/completions
```

## ingest

Ingest a project manifest into DevSynth.

**Usage:**

```bash
devsynth ingest [OPTIONS] [MANIFEST_PATH]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--dry-run` | Perform a dry run without making changes |
| `--verbose` | Enable verbose output |
| `--validate-only` | Only validate the manifest, do not ingest |
| `--priority TEXT` | Persist project priority |
| `--auto-phase-transitions/--no-auto-phase-transitions` | Automatically advance EDRR phases (default: enabled) |
| `--defaults` | Use defaults and skip prompts (implies non-interactive) |
| `--non-interactive` | Run without interactive prompts |

**Examples:**

```bash
# Validate only
devsynth ingest ./project.yaml --validate-only

# Dry run with verbose output
devsynth ingest ./project.yaml --dry-run --verbose

# Non-interactive defaults
devsynth ingest ./project.yaml --defaults
```

## mvuu-dashboard

Launch the MVUU traceability dashboard.

Usage:

```bash
# Validate wiring only (no external processes)
devsynth mvuu-dashboard --no-run

# Generate traceability report and launch the dashboard
mvuu-dashboard
```

Notes:
- The command is safe to import and supports a --no-run flag for smoke testing.
- The full dashboard requires the web UI dependency (NiceGUI / Streamlit) and may be gated in tests.

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

## edrr-cycle

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

Inspect and analyze project configuration and manifest alignment.

**Usage:**

```bash
devsynth inspect-config [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `PATH` | Optional path to the project root (defaults to current directory) |
| `--update` | Update the manifest with discovered items |
| `--prune` | Remove entries from the manifest that no longer exist |

**Examples:**

```bash
# Inspect project configuration in the current directory
devsynth inspect-config

# Inspect a specific path
devsynth inspect-config ./examples/project

# Update the manifest with discovered items
devsynth inspect-config --update

# Prune stale entries from the manifest
devsynth inspect-config --prune
```

## validate-manifest

Validate `.devsynth/project.yaml`.

**Usage:**

```bash
devsynth validate-manifest [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--manifest-file TEXT` | Path to the manifest file (default: `.devsynth/project.yaml`) |
| `--fix` | Attempt to fix issues automatically (default: False) |

**Examples:**

```bash

# Validate `.devsynth/project.yaml`

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

## security-audit

Run dependency and static analysis security checks.

**Usage:**

```bash
devsynth security-audit [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--skip-static` | Skip running Bandit static analysis |

**Examples:**

```bash

# Run full security audit
devsynth security-audit

# Run audit without static analysis
devsynth security-audit --skip-static
```

## Environment Variables
DevSynth respects the following environment variables:

| Variable | Description |
|----------|-------------|
| `DEVSYNTH_CONFIG` | Path to the configuration file |
| `DEVSYNTH_PROVIDER` | Default Provider to use (tests default to `stub` unless overridden by the run-tests CLI) |
| `OPENAI_API_KEY` | API key for OpenAI (live tests are strictly opt-in and gated) |
| `OPENAI_MODEL` | OpenAI chat/completions model to use for live tests (e.g., `gpt-4o-mini`) |
| `OPENAI_EMBEDDINGS_MODEL` | OpenAI embeddings model to use for live tests (e.g., `text-embedding-3-small`) |
| `LM_STUDIO_ENDPOINT` | Base URL for LM Studio server (default `http://127.0.0.1:1234`) |
| `ANTHROPIC_API_KEY` | API key for Anthropic |
| `DEVSYNTH_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DEVSYNTH_DEBUG` | If set (e.g., 1/true), forces DEBUG logging unless overridden by `--log-level` |
| `DEVSYNTH_CACHE_DIR` | Directory for caching data |
| `DEVSYNTH_DISABLE_TELEMETRY` | Disable telemetry (set to any value) |
| `DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS` | TTL (in seconds) for cached pytest collection used by run-tests segmentation (default: 3600) |

Note on live provider tests:
- Tests that exercise real OpenAI or LM Studio endpoints are marked with `@pytest.mark.requires_resource("openai"|"lmstudio")` and are skipped by default in CI. To opt in locally, set the appropriate env vars above and export `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true`. These tests assert only on response shape and use short timeouts (<=5s). For flake mitigation, resource-marked tests may be retried up to `DEVSYNTH_ONLINE_TEST_RETRIES` times (default 2) when `pytest-rerunfailures` is available; set to 0 to disable. OpenAI live profile reference: `DEVSYNTH_OFFLINE=false`, `DEVSYNTH_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_HTTP_TIMEOUT=15`. LM Studio profile: `DEVSYNTH_OFFLINE=false`, `DEVSYNTH_PROVIDER=lmstudio`, `LM_STUDIO_ENDPOINT`, `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true`, `LM_STUDIO_HTTP_TIMEOUT=15`.

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

## Implementation Status

- The run-tests CLI options are validated by behavior tests under `tests/behavior/steps/test_run_tests_steps.py` and unit tests under `tests/unit/application/cli/commands/`.
- CI workflows exercise fast unit tests by default and archive HTML reports when `--report` is used; see `.github/workflows/unit_tests.yml`.
- For determinism and resource gating defaults applied by the CLI, see `project guidelines` and `docs/developer_guides/testing.md`.



## Appendix: run-tests inventory output

The --inventory flag writes a JSON file to test_reports/test_inventory.json that summarizes the collected tests for planning and coverage tracking. This file is safe to generate in CI and local runs (no execution occurs when only inventorying).

Contents overview (fields may evolve conservatively):
- collected_count: total number of collected test items
- by_target: mapping of target → count (unit-tests, integration-tests, behavior-tests)
- by_speed: mapping of speed → count (fast, medium, slow)
- items: optional list of objects with fields
  - nodeid: pytest node id (e.g., tests/unit/test_example.py::TestClass::test_foo)
  - target: inferred target bucket
  - speed: speed marker

Practical uses:
- Sanity-check target/speed coverage before modifying CI matrices.
- Identify modules that lack speed markers (when used alongside the marker verification report).
- Track growth/regression in suites between commits by comparing JSONs.

Example generation:
- poetry run devsynth run-tests --inventory
- open test_reports/test_inventory.json

See also:
- docs/developer_guides/testing.md (segmentation, smoke mode)
- project guidelines (marker discipline and offline-first defaults)



## vcs

Utilities for working with version control (git) from DevSynth.

### vcs chunk-commit

Analyze pending changes and commit them in logical chunks sequentially. Files are grouped by concern (docs, tests, src, config, scripts, CI, examples, templates, chore). Commit messages include a brief Socratic and dialectical rationale to make the intent explicit.

Usage:

```bash
poetry run devsynth vcs chunk-commit --dry-run     # default: show plan only
poetry run devsynth vcs chunk-commit --execute     # perform commits
poetry run devsynth vcs chunk-commit --execute --staged-only
poetry run devsynth vcs chunk-commit --execute --no-verify
poetry run devsynth vcs chunk-commit --execute --staged-only=false --include-untracked
```

Options:
- --dry-run/--execute: Preview plan versus execute (default: --dry-run)
- --staged-only: Only consider staged changes (default: true)
- --include-untracked: When not staged-only, include untracked files
- --no-verify: Pass --no-verify to git commit per chunk

Notes:
- The command operates conservatively: it commits only the files in each group via pathspecs, avoiding accidental inclusion of unrelated staged changes.
- If a single file appears to cross-cut concerns, prefer committing it separately; the tool will place it in the "chore" group if no category matches.
- Designed to be CI-safe; it shells out to git similarly to MVU storage helpers.
