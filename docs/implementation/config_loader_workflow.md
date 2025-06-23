---
title: "Configuration Loader Workflow"
date: "2025-06-16"
version: "1.0.0"
tags:
  - "implementation"
  - "pseudocode"
  - "configuration"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# Configuration Loader Workflow

This pseudocode describes how DevSynth loads project settings from either `devsynth.yml` or `pyproject.toml` using a unified parser.

```pseudocode
class ConfigLoader:
    function load(path=".") -> DevSynthConfig:
        defaults = DevSynthConfig(project_root=path)
        if file_exists(path + "/.devsynth/devsynth.yml"):
            try:
                user = parse_yaml(path + "/.devsynth/devsynth.yml")
            except ParseError:
                raise ConfigError("Malformed YAML configuration")
        elif file_exists(path + "/pyproject.toml"):
            try:
                user = parse_toml(path + "/pyproject.toml").tool.devsynth
            except ParseError:
                raise ConfigError("Malformed TOML configuration")
        else:
            user = {}
        merged = merge(defaults, user)
        return DevSynthConfig(**merged)
```

The loader merges values from the chosen file into a common `DevSynthConfig` object so that both new and existing projects share the same configuration structure.

## Current Limitations

This workflow is a conceptual outline. The unified parser has not been fully
implemented, and integration tests for various project layouts are missing.
