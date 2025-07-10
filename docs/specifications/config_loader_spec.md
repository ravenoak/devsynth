---
author: DevSynth Team
date: '2025-06-16'
status: draft
tags:

- specification
- configuration
- pseudocode

title: Configuration Loader Specification
version: 0.1.0
---

# Configuration Loader Specification

```pseudocode
class DevSynthConfig:
    project_root: str = "."
    language: str = "python"
    structure: str = "single_package"
    features: Dict[str, bool]
```

```pseudocode
function load_config(path):
    if exists(path/.devsynth/project.yaml):
        data = parse_yaml(path/.devsynth/project.yaml)
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
        write_yaml(".devsynth/project.yaml", config)
```

The CLI exposes autocompletion of configuration keys:

```pseudocode
function config_key_autocomplete(incomplete):
    config = load_config()
    return [k for k in config.keys() if k.starts_with(incomplete)]
```

## Prompt Auto Tuning

When the feature flag `prompt_auto_tuning` is enabled in the loaded
configuration, the :class:`UnifiedAgent` will adjust LLM generation
parameters such as `temperature` using the `BasicPromptTuner`. Feedback
recorded through the agent's `record_prompt_feedback` method gradually
raises or lowers the sampling temperature to refine future prompts.