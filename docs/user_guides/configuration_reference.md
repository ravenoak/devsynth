---

author: DevSynth Team
date: '2025-07-17'
last_reviewed: "2025-07-10"
status: published
tags:

- configuration
- reference
- settings
- options

title: DevSynth Configuration Reference
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth Configuration Reference
</div>

# DevSynth Configuration Reference

This document provides a comprehensive reference for all configuration options available in DevSynth. It explains how to set these options, their purpose, possible values, and provides examples of common configurations.

## Table of Contents

- [LLM Configuration](#llm-configuration)
- [Environment Variables](#environment-variables)
- [.devsynth/project.yaml](#project-configuration)
- [Development Configuration](#development-configuration)
- [Memory Configuration](#memory-configuration)
- [UXBridge Configuration](#uxbridge-configuration)
- [Feature Flags](#feature-flags)
- [Configuration File Structure](#configuration-file-structure)
- [Command-Line Configuration](#command-line-configuration)


## LLM Configuration

DevSynth uses Large Language Models (LLMs) for various tasks. The following options control how these models are used.

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `llm.provider` | The Provider to use | `openai` | `openai`, `lmstudio`, `anthropic`, `abacus`, `offline` |
| `llm.model` | The LLM model to use | `gpt-3.5-turbo` | Any model supported by the selected provider |
| `llm.temperature` | Creativity level (higher = more creative) | `0.7` | 0.0 - 1.0 |
| `llm.max_tokens` | Maximum tokens for responses | `2000` | Any positive integer |
| `llm.endpoint` | API endpoint for the Provider | Provider-specific | Any valid URL |
| `llm.timeout` | Timeout for LLM requests in seconds | `60` | Any positive integer |
| `llm.retry_attempts` | Number of retry attempts for failed requests | `3` | Any non-negative integer |
| `llm.retry_delay` | Delay between retry attempts in seconds | `2` | Any positive integer |
| `llm.auto_select_model` | Automatically select the best model for the task | `false` | `true`, `false` |

### Example LLM Configuration

```yaml
llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  timeout: 120
  retry_attempts: 5
  retry_delay: 3
  auto_select_model: false
```

## Environment Variables

DevSynth supports loading configuration from environment variables. This is especially useful for sensitive information like API keys.

| Environment Variable | Configuration Key | Description |
|----------------------|------------------|-------------|
| `DEVSYNTH_LLM_PROVIDER` | `llm.provider` | The Provider to use |
| `DEVSYNTH_LLM_MODEL` | `llm.model` | The LLM model to use |
| `DEVSYNTH_LLM_TEMPERATURE` | `llm.temperature` | Creativity level |
| `DEVSYNTH_LLM_MAX_TOKENS` | `llm.max_tokens` | Maximum tokens for responses |
| `DEVSYNTH_LLM_ENDPOINT` | `llm.endpoint` | API endpoint for the Provider |
| `DEVSYNTH_LLM_TIMEOUT` | `llm.timeout` | Timeout for LLM requests in seconds |
| `DEVSYNTH_LLM_RETRY_ATTEMPTS` | `llm.retry_attempts` | Number of retry attempts |
| `DEVSYNTH_LLM_RETRY_DELAY` | `llm.retry_delay` | Delay between retry attempts |
| `DEVSYNTH_LLM_AUTO_SELECT_MODEL` | `llm.auto_select_model` | Auto-select the best model |
| `OPENAI_API_KEY` | `api_keys.openai` | OpenAI API key |
| `ANTHROPIC_API_KEY` | `api_keys.anthropic` | Anthropic API key |
| `SERPER_API_KEY` | `api_keys.serper` | Serper API key for web search |
| `DEVSYNTH_MEMORY_STORE` | `memory.store_type` | Memory store type |
| `DEVSYNTH_MEMORY_PATH` | `memory.file_path` | Path for file-based memory store |
| `DEVSYNTH_S3_BUCKET` | `memory.s3_bucket_name` | S3 bucket for S3 store |
| `DEVSYNTH_KUZU_DB_PATH` | `memory.kuzu_db_path` | Path for Kuzu |
| `DEVSYNTH_MAX_CONTEXT_SIZE` | `memory.max_context_size` | Maximum context size |
| `DEVSYNTH_LOG_LEVEL` | `logging.level` | Log level |
| `DEVSYNTH_CONFIG` | N/A | Path to the configuration file |
| `DEVSYNTH_DISABLE_TELEMETRY` | `telemetry.disabled` | Disable telemetry |

### Example Environment Variables

```env

# LLM Configuration

DEVSYNTH_LLM_PROVIDER=openai
DEVSYNTH_LLM_MODEL=gpt-4
DEVSYNTH_LLM_TEMPERATURE=0.7
DEVSYNTH_LLM_MAX_TOKENS=2000

# API Keys

OPENAI_API_KEY=sk-your-openai-api-key
SERPER_API_KEY=your-serper-api-key

# Memory Configuration

DEVSYNTH_MEMORY_STORE=s3
DEVSYNTH_S3_BUCKET=my-bucket

# Logging

DEVSYNTH_LOG_LEVEL=INFO
```

## `.devsynth/project.yaml`

These options control project-specific settings.

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `project.name` | Name of the project | Based on directory name | Any string |
| `project.description` | Description of the project | Empty string | Any string |
| `project.author` | Author of the project | System username | Any string |
| `project.license` | License for the project | `MIT` | Any valid license identifier |
| `project.version` | Version of the project | `0.1.0` | Any valid semantic version |
| `project.language` | Primary programming language | `python` | `python`, `javascript`, `typescript`, `java`, `go`, etc. |
| `project.layout` | Project layout style | `single_package` | `single_package`, `monorepo` |
| `project.requirements_file` | Path to requirements file | `requirements.md` | Any valid file path |
| `project.specs_file` | Path to specifications file | `specs.md` | Any valid file path |
| `project.tests_dir` | Directory for tests | `tests` | Any valid directory path |
| `project.src_dir` | Directory for source code | `src` | Any valid directory path |
| `project.docs_dir` | Directory for documentation | `docs` | Any valid directory path |

### Example `.devsynth/project.yaml`

```yaml
project:
  name: my-awesome-project
  description: A tool for automating development workflows
  author: Jane Doe
  license: MIT
  version: 0.1.0
  language: python
  layout: single_package
  requirements_file: docs/requirements.md
  specs_file: docs/specs.md
  tests_dir: tests
  src_dir: src
  docs_dir: docs
```

## Development Configuration

These options control development-specific settings.

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `development.test_framework` | Testing framework to use | `pytest` | `pytest`, `unittest` |
| `development.code_style` | Code style to follow | `pep8` | `pep8`, `google`, `numpy` |
| `development.documentation_style` | Documentation style | `google` | `google`, `numpy`, `sphinx` |
| `development.linter` | Linter to use | `flake8` | `flake8`, `pylint`, `ruff` |
| `development.formatter` | Code formatter to use | `black` | `black`, `yapf`, `autopep8` |
| `development.type_checker` | Type checker to use | `mypy` | `mypy`, `pyright`, `none` |
| `development.ci_provider` | CI provider to use | `github` | `github`, `gitlab`, `jenkins`, `none` |
| `development.package_manager` | Package manager to use | `poetry` | `poetry`, `pip`, `pipenv` |

### Example Development Configuration

```yaml
development:
  test_framework: pytest
  code_style: google
  documentation_style: google
  linter: ruff
  formatter: black
  type_checker: mypy
  ci_provider: github
  package_manager: poetry
```

## Memory Configuration

DevSynth uses a memory system to store and retrieve information. These options control how the memory system works.

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `memory.store_type` | Type of memory store to use | `memory` | `memory`, `file`, `Kuzu`, `ChromaDB` |
| `memory.file_path` | Path for file-based memory store | `~/.devsynth/memory` | Any valid directory path |
| `memory.kuzu_db_path` | Path for Kuzu | `~/.devsynth/memory/Kuzu.db` | Any valid file path |
| `memory.kuzu_embedded` | Use embedded Kuzu | `true` | `true`, `false` |
| `memory.max_context_size` | Maximum context size | `4096` | Any positive integer |
| `memory.context_expiration_days` | Days until context expires | `30` | Any positive integer |
| `memory.enable_vector_search` | Enable vector-based search | `true` | `true`, `false` |
| `memory.vector_dimensions` | Dimensions for vector embeddings | `1536` | Any positive integer |
| `memory.similarity_threshold` | Threshold for similarity search | `0.7` | 0.0 - 1.0 |

### Example Memory Configuration

```yaml
memory:
  store_type: Kuzu
  file_path: ~/.devsynth/memory
  kuzu_db_path: ~/.devsynth/memory/Kuzu.db
  kuzu_embedded: true
  max_context_size: 8192
  context_expiration_days: 60
  enable_vector_search: true
  vector_dimensions: 1536
  similarity_threshold: 0.75
```

## UXBridge Configuration

DevSynth uses the UXBridge abstraction to provide a consistent interface across different user interfaces (CLI, WebUI, Agent API).

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `uxbridge.default_interface` | Default interface to use | `cli` | `cli`, `webui`, `api` |
| `uxbridge.webui_port` | Port for WebUI | `8501` | Any valid port number |
| `uxbridge.api_port` | Port for Agent API | `8000` | Any valid port number |
| `uxbridge.api_host` | Host for Agent API | `127.0.0.1` | Any valid hostname or IP |
| `uxbridge.enable_auth` | Enable authentication | `false` | `true`, `false` |
| `uxbridge.auth_provider` | Authentication provider | `basic` | `basic`, `oauth`, `jwt` |
| `uxbridge.session_timeout` | Session timeout in minutes | `60` | Any positive integer |
| `uxbridge.enable_metrics` | Enable metrics collection | `false` | `true`, `false` |
| `uxbridge.metrics_port` | Port for metrics | `9090` | Any valid port number |

### Example UXBridge Configuration

```yaml
uxbridge:
  default_interface: webui
  webui_port: 8501
  api_port: 8000
  api_host: 0.0.0.0
  enable_auth: true
  auth_provider: jwt
  session_timeout: 120
  enable_metrics: true
  metrics_port: 9090
```

## Feature Flags

DevSynth uses feature flags to enable or disable specific features.

| Option | Description | Default Value | Possible Values |
|--------|-------------|---------------|----------------|
| `features.experimental` | Enable experimental features | `false` | `true`, `false` |
| `features.edrr_framework` | Enable the EDRR framework | `true` | `true`, `false` |
| `features.wsde_collaboration` | Enable WSDE collaboration | `false` | `true`, `false` |
| `features.dialectical_reasoning` | Enable dialectical reasoning | `false` | `true`, `false` |
| `features.uxbridge_webui` | Enable the WebUI interface | `true` | `true`, `false` |
| `features.uxbridge_agent_api` | Enable the Agent API interface | `false` | `true`, `false` |
| `features.memory_vector_search` | Enable vector-based memory search | `true` | `true`, `false` |
| `features.web_search` | Enable web search capabilities | `false` | `true`, `false` |
| `features.code_analysis` | Enable code analysis features | `true` | `true`, `false` |
| `features.auto_documentation` | Enable automatic documentation generation | `true` | `true`, `false` |

### Example Feature Flags Configuration

```yaml
features:
  experimental: false
  edrr_framework: true
  wsde_collaboration: true
  dialectical_reasoning: true
  uxbridge_webui: true
  uxbridge_agent_api: true
  memory_vector_search: true
  web_search: true
  code_analysis: true
  auto_documentation: true
```

## Configuration File Structure

DevSynth uses a YAML configuration file located at `.devsynth/config.yaml` by default. The configuration file can be modified using the `config` command or by editing it directly.

### Example Configuration File

```yaml

# DevSynth Configuration

project:
  name: my-project
  description: A tool for automating development workflows
  author: Jane Doe
  license: MIT
  version: 0.1.0
  language: python
  layout: single_package
  requirements_file: requirements.md
  specs_file: specs.md
  tests_dir: tests
  src_dir: src
  docs_dir: docs

llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  timeout: 120
  retry_attempts: 5
  retry_delay: 3
  auto_select_model: false

memory:
  store_type: Kuzu
  file_path: ~/.devsynth/memory
  kuzu_db_path: ~/.devsynth/memory/Kuzu.db
  kuzu_embedded: true
  max_context_size: 8192
  context_expiration_days: 60
  enable_vector_search: true
  vector_dimensions: 1536
  similarity_threshold: 0.75

development:
  test_framework: pytest
  code_style: google
  documentation_style: google
  linter: ruff
  formatter: black
  type_checker: mypy
  ci_provider: github
  package_manager: poetry

uxbridge:
  default_interface: webui
  webui_port: 8501
  api_port: 8000
  api_host: 0.0.0.0
  enable_auth: true
  auth_provider: jwt
  session_timeout: 120
  enable_metrics: true
  metrics_port: 9090

features:
  experimental: false
  edrr_framework: true
  wsde_collaboration: true
  dialectical_reasoning: true
  uxbridge_webui: true
  uxbridge_agent_api: true
  memory_vector_search: true
  web_search: true
  code_analysis: true
  auto_documentation: true

logging:
  level: INFO
  file: ~/.devsynth/logs/devsynth.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_size: 10485760  # 10 MB
  backup_count: 5

telemetry:
  disabled: false
  anonymize: true
```

## Command-Line Configuration

You can view and modify configuration settings using the `config` command:

```bash

# View all configuration settings

devsynth config --list

# Set a configuration value

devsynth config llm.model gpt-4

# Reset configuration to default values

devsynth config --reset
```

You can also enable or disable feature flags using the `enable-feature` and `disable-feature` commands:

```bash

# Enable a feature

devsynth enable-feature edrr_framework

# Disable a feature

devsynth disable-feature experimental
```

## Configuration Precedence

DevSynth uses the following precedence order for configuration (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Project-specific configuration file (`.devsynth/config.yaml`)
4. User-specific configuration file (`~/.devsynth/config.yaml`)
5. Default values


This means that command-line arguments override environment variables, which override the project-specific configuration file, and so on.

## Conclusion

This reference covers all the configuration options available in DevSynth. For more detailed information about specific features or workflows, refer to the DevSynth documentation or use the `--help` option with any command.
## Implementation Status

This feature is **implemented** and reflects the options available in the
current release.
