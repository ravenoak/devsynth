---

author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-09-21"
status: review
tags:

- implementation
- pseudocode
- configuration

title: Configuration Loader Workflow
version: "0.1.0a1"
---
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

## Evidence

- **Behavior:** [`tests/behavior/features/configuration_loader.feature`](../../tests/behavior/features/configuration_loader.feature) exercises the YAML fallback path and surfaces configuration errors for malformed `pyproject.toml` inputs.
- **Unit:** [`tests/unit/core/test_unified_config_loader.py`](../../tests/unit/core/test_unified_config_loader.py) verifies fallback selection along with malformed YAML and TOML failure modes in `UnifiedConfigLoader`.

## Current Limitations

This workflow is fully implemented. The unified parser handles both YAML and
TOML configurations, and the tests above cover fallback selection plus
configuration error handling for malformed files.
## Implementation Status

This feature is **implemented** and verified by automated tests.
