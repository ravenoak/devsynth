---
title: "Configuration Loader Specification"
date: "2025-06-16"
version: "0.1.0"
tags:
  - "specification"
  - "configuration"
  - "pseudocode"
status: "draft"
author: "DevSynth Team"
---

# Unified Configuration Loader

```pseudocode
class DevSynthConfig:
    project_root: str = "."
    language: str = "python"
    structure: str = "single_package"
    features: Dict[str, bool]
```

```pseudocode
function load_config(path):
    if exists(path/.devsynth/devsynth.yml):
        data = parse_yaml(path/.devsynth/devsynth.yml)
    else if exists(path/pyproject.toml):
        data = parse_toml(path/pyproject.toml).tool.devsynth
    else:
        data = {}
    return DevSynthConfig(**data)
```

```pseudocode
function save_config(config, use_pyproject):
    if use_pyproject:
        update_toml("pyproject.toml", {tool.devsynth: config})
    else:
        write_yaml(".devsynth/devsynth.yml", config)
```

The CLI exposes autocompletion of configuration keys:

```pseudocode
function config_key_autocomplete(incomplete):
    config = load_config()
    return [k for k in config.keys() if k.starts_with(incomplete)]
```
