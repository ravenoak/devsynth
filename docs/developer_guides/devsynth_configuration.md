# DevSynth Configuration and Storage System

This document provides a comprehensive overview of the DevSynth configuration and storage systems, including where resources are stored and how they're configured.

## Configuration System

DevSynth uses a hierarchical configuration system with both global and project-level settings:

1. **Global Configuration**: Stored in `~/.devsynth/config/global_config.yaml`
2. **Project Configuration**: Stored in `manifest.yaml` at the project root

The configuration system follows a precedence order:
1. Environment variables (highest precedence)
2. Project-level configuration in `manifest.yaml`
3. Global configuration in `~/.devsynth/config/global_config.yaml`
4. Default values (lowest precedence)

### Manifest File

The `manifest.yaml` file is the primary configuration file for a DevSynth project. It defines the project structure, key artifacts, and resource locations. This file is created automatically when you run `devsynth init` in a directory.

The manifest file follows a schema defined in `docs/manifest_schema.json` and can be validated using the `devsynth validate-manifest` command.

Example manifest.yaml:
```yaml
projectName: my-project
version: 0.1.0
lastUpdated: 2025-05-25T12:00:00
structure:
  type: single_package
  primaryLanguage: python
  directories:
    source: [src]
    tests: [tests]
    docs: [docs]
  entryPoints: [src/main.py]
  ignore:
    - "**/__pycache__/**"
    - "**/.git/**"
    - "**/venv/**"
    - "**/.env"
keyArtifacts:
  docs:
    - path: README.md
      purpose: Project overview and getting started guide
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

- `devsynth init`: Creates a new project with a default `manifest.yaml` file
- `devsynth analyze-manifest`: Analyzes and updates the `manifest.yaml` file based on the actual project structure
- `devsynth validate-manifest`: Validates the `manifest.yaml` file against its schema

## Best Practices

1. **Version Control**: Include the `manifest.yaml` file in version control to ensure consistent configuration across all developers.
2. **Gitignore**: Add `.devsynth/` to your `.gitignore` file to exclude project-level resources from version control.
3. **Environment Variables**: Use environment variables for sensitive information like API keys instead of storing them in configuration files.
4. **Regular Updates**: Periodically run `devsynth analyze-manifest` to keep your manifest file in sync with the actual project structure.