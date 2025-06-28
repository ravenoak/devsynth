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

DevSynth uses the implemented `UnifiedConfigLoader` to read configuration from
either `devsynth.yml` or `pyproject.toml`.

```python
from devsynth.config.unified_loader import UnifiedConfigLoader


def load_config(path: str = "."):
    unified = UnifiedConfigLoader.load(path)
    return unified.config
```

## Examples

Loading prefers the `[tool.devsynth]` table when both files are present:

```python
cfg = UnifiedConfigLoader.load(".")
assert cfg.use_pyproject
print(cfg.config.language)
```

Saving with `use_pyproject=True` writes back to the same table:

```python
cfg = UnifiedConfigLoader.load(".")
cfg.set_language("python")
cfg.save()
```

The loader merges values from the chosen file into a common configuration object so both new and existing projects share the same structure.

## Current Limitations

This workflow is a conceptual outline. The unified parser has not been fully
implemented, and integration tests for various project layouts are missing.
