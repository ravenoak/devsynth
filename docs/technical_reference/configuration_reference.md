---
title: "DevSynth Configuration Reference"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "configuration"
  - "reference"
  - "settings"
  - "technical"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# DevSynth Configuration Reference

This document provides a comprehensive reference for configuring DevSynth. It covers configuration file structure, environment variables, and programmatic configuration options.

## Table of Contents

- [Configuration File](#configuration-file)
- [Environment Variables](#environment-variables)
- [Configuration Categories](#configuration-categories)
  - [Provider Configuration](#provider-configuration)
  - [Memory Configuration](#memory-configuration)
  - [Project Configuration](#project-configuration)
  - [Logging Configuration](#logging-configuration)
  - [Agent Configuration](#agent-configuration)
  - [EDRR Configuration](#edrr-configuration)
- [Configuration API](#configuration-api)
- [Best Practices](#best-practices)

## Configuration File

DevSynth uses a YAML configuration file located at `~/.devsynth/config.yaml` by default. You can specify a different location using the `--config-file` CLI option or the `DEVSYNTH_CONFIG_PATH` environment variable.

For project configuration DevSynth relies on a *unified loader* that searches the
project root for either a `[tool.devsynth]` table in `pyproject.toml` or the file
`.devsynth/devsynth.yml`. When both are present the TOML entry takes precedence.
Saving a configuration writes back to whichever file was originally loaded. The
loader also checks the `version` field against the CLI's expected
`ConfigModel.version` and logs a warning if they differ, providing a simple form
of version locking.

### Example Configuration File

```yaml
# LLM Provider Configuration
provider:
  name: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 4000
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0
  timeout: 60

# Memory Configuration
memory:
  vector_store: chromadb
  document_store: tinydb
  graph_store: rdflib
  path: ~/.devsynth/memory
  persistence: true
  embedding_model: text-embedding-3-small

# Project Configuration
project:
  default_path: ~/projects
  templates_path: ~/.devsynth/templates
  default_template: basic

# Logging Configuration
logging:
  level: info
  file: ~/.devsynth/logs/devsynth.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_size: 10485760  # 10MB
  backup_count: 5

# Agent Configuration
agents:
  documentation:
    enabled: true
    model: gpt-4
  specification:
    enabled: true
    model: gpt-4
  test:
    enabled: true
    model: gpt-4
  code:
    enabled: true
    model: gpt-4
  review:
    enabled: true
    model: gpt-4

# EDRR Configuration
edrr:
  expand:
    depth: 3
    breadth: 5
  differentiate:
    criteria_weight:
      performance: 0.3
      maintainability: 0.3
      security: 0.2
      scalability: 0.2
  refine:
    iterations: 2
  retrospect:
    metrics:
      - code_quality
      - test_coverage
      - performance
```

## Environment Variables

DevSynth uses the following environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVSYNTH_ENV` | Deployment environment | development |
| `DEVSYNTH_PROVIDER` | Default LLM provider | openai |
| `DEVSYNTH_LLM_PROVIDER` | LLM provider override | openai |
| `DEVSYNTH_MEMORY_STORE` | Memory store to use | kuzu |
| `DEVSYNTH_OPENAI_API_KEY` | OpenAI API key (config override) | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `DEVSYNTH_OPENAI_MODEL` | OpenAI model to use | gpt-4 |
| `OPENAI_MODEL` | OpenAI model to use | gpt-4 |
| `LM_STUDIO_ENDPOINT` | LM Studio API endpoint | http://127.0.0.1:1234 |
| `SERPER_API_KEY` | Serper API key for web searches | None |
| `DEVSYNTH_CONFIG_PATH` | Path to configuration file | ~/.devsynth/config.yaml |
| `DEVSYNTH_MEMORY_PATH` | Path to memory storage | ~/.devsynth/memory |
| `DEVSYNTH_LOG_LEVEL` | Logging level | info |
| `DEVSYNTH_LOG_FILE` | Path to log file | ~/.devsynth/logs/devsynth.log |

Environment variables take precedence over configuration file settings.

## Configuration Categories

### Provider Configuration

The `provider` section configures the LLM provider used by DevSynth.

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `name` | Provider name | openai | openai, lm_studio, anthropic, abacus |
| `model` | Model to use | gpt-4 | Any model supported by the provider |
| `temperature` | Randomness of responses | 0.7 | 0.0-1.0 |
| `max_tokens` | Maximum tokens in response | 4000 | 1-32000 (provider-dependent) |
| `top_p` | Nucleus sampling parameter | 1.0 | 0.0-1.0 |
| `frequency_penalty` | Penalty for token frequency | 0.0 | 0.0-2.0 |
| `presence_penalty` | Penalty for token presence | 0.0 | 0.0-2.0 |
| `timeout` | Request timeout in seconds | 60 | Any positive integer |

### Memory Configuration

The `memory` section configures DevSynth's memory system.

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `vector_store` | Vector storage backend | chromadb | chromadb, faiss, in_memory |
| `document_store` | Document storage backend | tinydb | tinydb, json, in_memory |
| `graph_store` | Graph storage backend | rdflib | rdflib, in_memory |
| `path` | Path to memory storage | ~/.devsynth/memory | Any valid directory path |
| `persistence` | Enable memory persistence | true | true, false |
| `embedding_model` | Model for generating embeddings | text-embedding-3-small | Any embedding model name |

### Project Configuration

The `project` section configures project-related settings.

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `default_path` | Default project path | ~/projects | Any valid directory path |
| `templates_path` | Path to project templates | ~/.devsynth/templates | Any valid directory path |
| `default_template` | Default project template | basic | Any template name |

### Logging Configuration

The `logging` section configures DevSynth's logging behavior.

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `level` | Logging level | info | debug, info, warning, error, critical |
| `file` | Log file path | ~/.devsynth/logs/devsynth.log | Any valid file path |
| `format` | Log message format | %(asctime)s - %(name)s - %(levelname)s - %(message)s | Any valid log format string |
| `max_size` | Maximum log file size in bytes | 10485760 (10MB) | Any positive integer |
| `backup_count` | Number of backup logs to keep | 5 | Any non-negative integer |

### Agent Configuration

The `agents` section configures individual agents in DevSynth.

Each agent can have the following settings:

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `enabled` | Enable/disable the agent | true | true, false |
| `model` | LLM model for the agent | gpt-4 | Any model supported by the provider |
| `temperature` | Randomness for this agent | 0.7 | 0.0-1.0 |
| `max_tokens` | Maximum tokens for this agent | 4000 | 1-32000 (provider-dependent) |

### EDRR Configuration

The `edrr` section configures the EDRR (Expand, Differentiate, Refine, Retrospect) cycle.

| Key | Description | Default | Valid Values |
|-----|-------------|---------|--------------|
| `expand.depth` | Depth of expansion | 3 | Any positive integer |
| `expand.breadth` | Breadth of expansion | 5 | Any positive integer |
| `differentiate.criteria_weight` | Weights for evaluation criteria | See example | Any valid weight distribution |
| `refine.iterations` | Number of refinement iterations | 2 | Any positive integer |
| `retrospect.metrics` | Metrics to evaluate in retrospect | See example | Any valid metrics |

## Configuration API

DevSynth provides a programmatic API for configuration management:

```python
from devsynth.config import Config

# Load configuration
config = Config.load()

# Get configuration values
provider_name = config.get("provider.name")
memory_path = config.get("memory.path")

# Set configuration values
config.set("provider.model", "gpt-4")
config.set("logging.level", "debug")

# Save configuration
config.save()

# Reset to defaults
config.reset()
```

## Best Practices

### Security

- Store API keys in environment variables rather than in the configuration file
- Use environment-specific configuration files for different environments
- Restrict access to configuration files containing sensitive information

### Performance

- Configure memory persistence based on your needs (disable for ephemeral usage)
- Adjust model parameters (temperature, max_tokens) based on your use case
- Use local models via LM Studio for faster development iterations

### Organization

- Use project-specific configuration files for project-specific settings
- Document any custom configuration in your project's README
- Version control your configuration templates but not your actual configuration files with secrets

### Troubleshooting

- Increase logging level to debug for troubleshooting
- Check environment variables if configuration doesn't seem to be applied
- Use `devsynth config --list` to verify current configuration

---

For more information on using these configuration options, see the [CLI Reference](../user_guides/cli_reference.md) and [User Guide](../user_guides/user_guide.md).