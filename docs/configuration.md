---

title: "Configuration Overview"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "configuration"
  - "feature-flags"

status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Configuration Overview
</div>

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
| `mvuu_dashboard` | Enables the MVUU traceability dashboard. |
| `gui` | Enables the Dear PyGui desktop client. |

For the UX design rationale behind gradually exposing these capabilities, see the [Progressive Complexity UX Design section](analysis/dialectical_evaluation.md#synthesis-progressive-complexity-ux-design).

## GUI Configuration

DevSynth includes an optional Dear PyGUI interface. To prevent unintended GUI launches in headless environments this interface is disabled by default. Set `gui.enabled` to `true` to enable the `dpg` CLI command and activate related feature flags:

```yaml
gui:
  enabled: true
features:
  gui: true
  mvuu_dashboard: true
```

This example enables both the desktop client and the MVUU traceability dashboard.

## Enabling Flags

1. **CLI**: use the `config` command to set a flag:

   ```bash
   devsynth config features.code_generation true
   ```

2. **Setup Wizard**: running `devsynth init` will prompt you to enable optional features interactively.


Changes are written to the appropriate configuration file so subsequent runs use the selected features.

## Unified Configuration Loader

DevSynth provides a single loader that reads project configuration from either
`.devsynth/project.yaml` or the `[tool.devsynth]` section of `pyproject.toml`.
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

## Language Selection

The `language` key in your project configuration determines which primary
programming language DevSynth uses when creating files. The
`MultiLanguageCodeAgent` also reads this value when generating templates.
Supported values currently include `python` and `javascript`.

Example:

```yaml
language: javascript
features:
  code_generation: true
```

Setting `language: javascript` instructs the agent to produce JavaScript code by
default. When `language` is omitted, Python is used.

## Migrating from YAML to pyproject.toml

Existing projects that store settings in `.devsynth/project.yaml` can move
those values into the `[tool.devsynth]` table of `pyproject.toml`. When both
files are present the loader now prefers the TOML table, so you may delete the
YAML file once migrated. All configuration keys remain the same.

## Offline Mode and Offline Provider

When `offline_mode` is set to `true` in project configuration DevSynth avoids remote LLM calls and uses the built-in offline provider. This provider generates deterministic text and embeddings so automated workflows remain repeatable. The following keys control this behaviour:

| Key | Description |
| --- | ----------- |
| `offline_mode` | Enable offline operation and select the offline provider. |
| `offline_provider.model_path` | Path to a local HF model used by the offline provider. |
| `resources.local.model_path` | Optional path to a local HF model if you wish to run a real model while offline. |
| `resources.local.context_length` | Maximum tokens kept when pruning conversation history when using a local model. |

Example configuration:

```yaml
offline_mode: true
offline_provider:
  model_path: /models/tiny-gpt2
resources:
  local:
    model_path: /models/mistral
    context_length: 4096
```

## Implementation Status

This feature is **implemented** and validated by unit tests.
