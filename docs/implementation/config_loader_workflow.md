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
        if file_exists(path + "/.devsynth/devsynth.yml"):
            data = parse_yaml(path + "/.devsynth/devsynth.yml")
        elif file_exists(path + "/pyproject.toml"):
            data = parse_toml(path + "/pyproject.toml").tool.devsynth
        else:
            data = {}
        return DevSynthConfig(**data)
```

The loader merges values from the chosen file into a common `DevSynthConfig` object so that both new and existing projects share the same configuration structure.

## Current Limitations

This workflow is a conceptual outline. The unified parser has not been fully
implemented, and integration tests for various project layouts are missing.
