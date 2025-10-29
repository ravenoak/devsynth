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

## Overview

This document provides a comprehensive explanation of the DevSynth configuration and storage system, including where individual resources live on a user's computer and how they are accessed by the application.

## Configuration System

DevSynth uses a hierarchical configuration system with multiple levels of precedence:

1. **Command-line arguments**: Highest precedence, overrides all other settings
2. **Environment variables**: Prefixed with `DEVSYNTH_`
3. **Project-level configuration**: Stored in `.devsynth/project.yaml`
4. **Global configuration**: Stored in `~/.devsynth/config/global_config.yaml`
5. **Default values**: Hardcoded in the application


### Configuration Files

#### Project-Level Configuration: `.devsynth/project.yaml`

The `.devsynth/project.yaml` file is the primary configuration file for a project. It is created by the `devsynth init` command and contains:

- Project metadata (name, version, last updated)
- Project structure information (type, primary language, directories)
- Entry points
- Ignore patterns
- Key artifacts
- Methodology settings
- Resource locations (both global and project-level)


Example:

```yaml
projectName: example-project
version: "0.1.0a1"
lastUpdated: 2025-05-25T12:00:00
structure:
  type: single_package
  primaryLanguage: python
  directories:
    source: ["src"]
    tests: ["tests"]
    docs: ["docs"]
  entryPoints: ["src/main.py"]
  ignore: ["**/__pycache__/**", "**/.git/**", "**/venv/**", "**/.env"]
keyArtifacts:
  docs:
    - path: README.md

      purpose: Project overview and getting started guide
methodology:
  type: sprint
  settings:
    sprintDuration: 14
    reviewFrequency: 7
resources:
  global:
    configDir: ~/.devsynth/config
    cacheDir: ~/.devsynth/cache
    logsDir: ~/.devsynth/logs
    memoryDir: ~/.devsynth/memory
  project:
    configDir: .devsynth
    cacheDir: .devsynth/cache
    logsDir: .devsynth/logs
    memoryDir: .devsynth/memory
```

#### Global Configuration: `~/.devsynth/config/global_config.yaml`

The global configuration file contains settings that apply to all projects. It is created automatically when DevSynth is first used and can be modified by the user.

Example:

```yaml
resources:
  global:
    configDir: ~/.devsynth/config
    cacheDir: ~/.devsynth/cache
    logsDir: ~/.devsynth/logs
    memoryDir: ~/.devsynth/memory
```

### Environment Variables

DevSynth supports configuration through environment variables, which take precedence over configuration files. All environment variables are prefixed with `DEVSYNTH_`.

Common environment variables:

- `DEVSYNTH_MEMORY_STORE`: Type of memory store to use (default: "memory")
- `DEVSYNTH_MEMORY_PATH`: Path to the memory file
- `DEVSYNTH_MAX_CONTEXT_SIZE`: Maximum context size (default: 1000)
- `DEVSYNTH_CONTEXT_EXPIRATION_DAYS`: Number of days before context expires (default: 7)
- `DEVSYNTH_LOG_DIR`: Directory for logs
- `DEVSYNTH_PROJECT_DIR`: Project directory
- `DEVSYNTH_PROVIDER_TYPE`: Provider type (default: "openai")


## Storage System

DevSynth uses a hybrid storage system with both global and project-level storage locations.

### Global Storage Locations

Global storage locations are shared across all projects and are stored in the user's home directory:

- **Configuration**: `~/.devsynth/config/`
  - Contains global configuration files like `global_config.yaml`
  - Stores Provider settings, default templates, and other global settings

- **Cache**: `~/.devsynth/cache/`
  - Stores cached data like LLM responses, external documentation, and other reusable resources
  - Helps reduce API calls and improve performance

- **Logs**: `~/.devsynth/logs/`
  - Contains log files for DevSynth operations
  - Useful for debugging and auditing

- **Memory**: `~/.devsynth/memory/`
  - Stores persistent memory for DevSynth
  - Includes conversation history, project context, and other long-term memory


### Project-Level Storage Locations

Project-level storage locations are specific to each project and are stored in the project directory:

- **Configuration**: `.devsynth/`
  - Contains project-specific configuration files
  - Includes the `.devsynth/project.yaml` file

- **Cache**: `.devsynth/cache/`
  - Stores project-specific cached data
  - Includes generated code, test results, and other project-specific resources

- **Logs**: `.devsynth/logs/`
  - Contains project-specific log files
  - Useful for debugging and auditing project-specific operations

- **Memory**: `.devsynth/memory/`
  - Stores project-specific memory
  - Includes project-specific conversation history and context


## Access Patterns

DevSynth uses a consistent pattern for accessing configuration and storage:

1. Check for explicit values provided via command-line arguments or function parameters
2. Check for environment variables
3. Check for project-level configuration in `.devsynth/project.yaml`
4. Check for global configuration in `~/.devsynth/config/global_config.yaml`
5. Fall back to default values


This pattern is implemented in the `settings.py` file, which provides validators for paths like `memory_file_path`, `log_dir`, and `project_dir` that follow this hierarchy.

## Best Practices

### For DevSynth Users

- Use the `devsynth init` command to create the initial `.devsynth/project.yaml` file
- Use the `devsynth inspect-config` command (formerly `analyze-manifest`) to keep the configuration up to date
 - Use the `devsynth validate-manifest` command to validate the configuration against its schema
- Avoid modifying global configuration files directly unless necessary
- Use environment variables for temporary configuration changes


### For DevSynth Developers

- Always use the `get_settings()` function to access configuration values
- Defer path creation until explicitly needed to maintain testability
- Use the `ensure_path_exists()` function to create directories when needed
- Follow the established pattern for accessing configuration and storage
- Add validators for new settings that need to check multiple sources


## Conclusion

The DevSynth configuration and storage system provides a flexible and robust way to manage settings and data across multiple projects. By understanding where resources live and how they are accessed, users and developers can effectively work with DevSynth in various contexts.
## Implementation Status

This feature is **implemented** and used by the CLI and WebUI.
