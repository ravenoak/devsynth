---
title: "Configuration Overview"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "configuration"
  - "feature-flags"
status: "draft"
author: "DevSynth Team"
---

# Configuration Overview

This guide explains the feature flags available in `config/*.yml` files and how you can enable them. These flags toggle optional capabilities of DevSynth. By default, most environments keep them disabled to minimize resource usage and limit surprises in production.

## Feature Flags

| Flag | Description |
| ---- | ----------- |
| `wsde_collaboration` | Enables multi-agent collaboration via the WSDE framework. |
| `dialectical_reasoning` | Activates dialectical reasoning for idea refinement. |
| `code_generation` | Allows automated code generation tasks. |
| `test_generation` | Enables automatic test creation features. |
| `documentation_generation` | Provides automated documentation generation. |
| `experimental_features` | Gates bleeding edge functionality; off in most configs. |

For the UX design rationale behind gradually exposing these capabilities, see the [Progressive Complexity UX Design section](analysis/dialectical_evaluation.md#synthesis-progressive-complexity-ux-design).

## Enabling Flags

1. **CLI**: use the `config` command to set a flag:
   ```bash
   devsynth config features.code_generation true
   ```
2. **Setup Wizard**: running `devsynth init` will prompt you to enable optional features interactively.

Changes are written to the appropriate configuration file so subsequent runs use the selected features.

## Unified Configuration Loader

DevSynth provides a single loader that reads project configuration from either
`.devsynth/devsynth.yml` or the `[tool.devsynth]` section of `pyproject.toml`.
The loader returns a `ConfigModel` dataclass with these fields:

```yaml
project_root: str
structure: str
language: str
goals: str | null
constraints: str | null
directories:
  source: ["src"]
  tests: ["tests"]
  docs: ["docs"]
features: {code_generation: bool, test_generation: bool}
resources: dict
```

Use `from devsynth.config import get_project_config` in your code to access the
parsed configuration. CLI commands also expose autocompletion of configuration
keys via `config_key_autocomplete`. For additional implementation details see
the [Unified Configuration Loader specification](specifications/unified_configuration_loader.md).

## Migrating from YAML to pyproject.toml

Existing projects that store settings in `.devsynth/devsynth.yml` can move
those values into the `[tool.devsynth]` table of `pyproject.toml`. When both
files are present the loader now prefers the TOML table, so you may delete the
YAML file once migrated. All configuration keys remain the same.

## Offline Mode and Local Provider

When `offline_mode` is set to `true` in project configuration DevSynth avoids remote LLM calls and relies on a local model. The following keys control this behaviour:

| Key | Description |
| --- | ----------- |
| `offline_mode` | Enable offline operation and select the local provider. |
| `resources.local.model_path` | Filesystem path to a local HF model directory. |
| `resources.local.context_length` | Maximum tokens kept when pruning conversation history. |

Example configuration:

```yaml
offline_mode: true
resources:
  local:
    model_path: /models/mistral
    context_length: 4096
```

