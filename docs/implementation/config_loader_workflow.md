---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-07-10"
status: draft
tags:

- implementation
- pseudocode
- configuration

title: Configuration Loader Workflow
version: 0.1.0---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Configuration Loader Workflow
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Configuration Loader Workflow
</div>

# Configuration Loader Workflow

DevSynth uses the implemented `UnifiedConfigLoader` to read configuration from
either `project.yaml` or `pyproject.toml`.

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

This workflow is fully implemented. The unified parser handles both YAML and
TOML configurations, and integration tests cover multiple project layouts.
## Implementation Status

This feature is **implemented** and verified by automated tests.
