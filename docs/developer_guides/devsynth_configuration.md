---

title: "DevSynth Configuration and Storage System"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "developer-guide"
  - "configuration"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Configuration and Storage System
</div>

# DevSynth Configuration and Storage System

This document provides a comprehensive overview of the DevSynth configuration and storage systems, including where resources are stored and how they're configured.

## Configuration System

DevSynth uses a hierarchical configuration system with both global and project-level settings:

1. **Global Configuration**: Stored in `~/.devsynth/config/global_config.yaml`
2. **`.devsynth/project.yaml`**: Configuration file for projects managed by DevSynth


The configuration system follows a precedence order:

1. Environment variables (highest precedence)
2. Project-level configuration in `.devsynth/project.yaml` (for projects managed by DevSynth)
3. Global configuration in `~/.devsynth/config/global_config.yaml`
4. Default values (lowest precedence)


Note: The presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth. If a project is not managed by DevSynth, it will not have a `.devsynth/` directory or a project configuration file.

### `.devsynth/project.yaml` File

The `.devsynth/project.yaml` file is the configuration file for projects managed by DevSynth. It describes the shape and attributes of the project in a minimal but functional, featureful, and human-friendly way. This file is created automatically when you run `devsynth init` in a directory, which also creates the `.devsynth/` directory.

The project configuration file follows a schema defined in `src/devsynth/schemas/project_schema.json` and can be validated using the `devsynth validate-manifest` command (formerly `validate-manifest`).

Example project.yaml:

```yaml
metadata:
  name: my-project
  version: 0.1.0
  description: A sample project managed by DevSynth
  lastUpdated: 2025-05-25T12:00:00
structure:
  type: single_package
  languages:
    primary: python
    additional: [javascript]
  directories:
    source: [src]
    tests: [tests]
    docs: [docs]
goals: Build a demo application
  entryPoints: [src/main.py]
  ignore:
    - "**/__pycache__/**"
    - "**/.git/**"
    - "**/venv/**"
    - "**/.env"

```

## Storage System

DevSynth uses a hybrid storage system with both global and project-level resources:

### Global Resources

Global resources are shared across all DevSynth projects on the system:

1. **Configuration Directory**: `~/.devsynth/config/`
   - Contains global configuration files like `global_config.yaml`
   - Stores global settings that apply to all projects

2. **Cache Directory**: `~/.devsynth/cache/`
   - Stores cached data that can be reused across projects
   - Includes cached LLM responses, downloaded documentation, etc.

3. **Logs Directory**: `~/.devsynth/logs/`
   - Stores global logs for DevSynth operations
   - Useful for troubleshooting issues that span multiple projects

4. **Memory Directory**: `~/.devsynth/memory/`
   - Stores global memory files for DevSynth
   - Includes vector databases, context history, etc. that can be shared across projects


### Project-Level Resources

Project-level resources are specific to each DevSynth project:

1. **Configuration Directory**: `.devsynth/`
   - Contains project-specific configuration files
   - Created automatically when you run `devsynth init`

2. **Cache Directory**: `.devsynth/cache/`
   - Stores project-specific cached data
   - Includes cached analysis results, temporary files, etc.

3. **Logs Directory**: `.devsynth/logs/`
   - Stores project-specific logs
   - Useful for troubleshooting issues within a specific project

4. **Memory Directory**: `.devsynth/memory/`
   - Stores project-specific memory files
   - Includes vector databases, context history, etc. that are specific to the project


## Managing Configuration

DevSynth provides several commands for managing configuration:

- `devsynth init`: Creates a new project with a default `.devsynth/project.yaml` file and establishes the project as managed by DevSynth
- `devsynth inspect-config` (formerly `analyze-manifest`): Analyzes and updates the `.devsynth/project.yaml` file based on the actual project structure
- `devsynth validate-manifest` (formerly `validate-manifest`): Validates the `.devsynth/project.yaml` file against its schema


### Configuration Schema and Loader

The unified configuration loader searches for `.devsynth/project.yaml` or a `[tool.devsynth]` section in `pyproject.toml`. Both formats share common fields:

```text
project_root: str
structure: str
language: str
goals: str (optional)
constraints: str (optional)
directories: {source: ["src"], tests: ["tests"], docs: ["docs"]}
features: {code_generation: bool, test_generation: bool, ...}
resources: {project: {memoryDir: str, logsDir: str}}
```

`load_config()` returns a `DevSynthConfig` dataclass with defaults when no configuration file exists. `save_config()` writes the dataclass back to YAML or TOML and is used by the CLI to persist preferences during initialization and later configuration updates.

### Core configuration loader

`src/devsynth/core/config_loader.py` provides a lightweight loader used by
internal tools. It merges environment variables with project-level files and the
global configuration stored in `~/.devsynth/config/`. Environment variables with
the `DEVSYNTH_` prefix always take precedence. The module also exposes
`config_key_autocomplete()` so Typer commands can offer CLI autocompletion for
configuration keys and `save_global_config()` to persist user preferences.

```python
from devsynth.core.config_loader import load_config, save_global_config

cfg = load_config()
save_global_config(cfg)
```

## Best Practices

1. **Version Control**: Include the `.devsynth/project.yaml` file in version control to ensure consistent configuration across all developers.
2. **Gitignore**: Add `.devsynth/cache/`, `.devsynth/logs/`, and `.devsynth/memory/` to your `.gitignore` file to exclude volatile project-level resources from version control, but keep `.devsynth/project.yaml`.
3. **Environment Variables**: Use environment variables for sensitive information like API keys instead of storing them in configuration files.
4. **Regular Updates**: Periodically run `devsynth inspect-config` to keep your project configuration file in sync with the actual project structure.
5. **Project Marker**: Remember that the presence of a `.devsynth/` directory is the marker that a project is managed by DevSynth. Do not create this directory manually; use `devsynth init` to establish a project as managed by DevSynth.
## Implementation Status

This feature is **implemented** and documented with examples.
