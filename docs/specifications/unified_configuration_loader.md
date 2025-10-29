---

title: "Unified Configuration Loader"
date: "2025-06-16"
last_reviewed: "2025-07-20"
version: "0.1.0a1"
tags:
  - "specification"
  - "configuration"

status: "draft"
author: "DevSynth Team"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Unified Configuration Loader
</div>

# Unified Configuration Loader

This specification describes the goals and design of the unified configuration loader. The loader reads project settings from either the YAML file `.devsynth/project.yaml` or the `[tool.devsynth]` table in `pyproject.toml`. Its main goals are:

1. Provide a single API to read and write configuration regardless of file format.
2. Support persistent CLI preferences so commands remember previously selected options.
3. Offer autocompletion of configuration keys to improve the command-line experience.


## Schema Outline

```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class DevSynthConfig(BaseModel):
    project_root: str = "."
    language: str = "python"
    structure: str = "single_package"
    directories: Dict[str, List[str]] = {"source": ["src"], "tests": ["tests"], "docs": ["docs"]}
    features: Dict[str, bool] = {"code_generation": False, "test_generation": False}
    preferences: Dict[str, str] = {}
    resources: Dict[str, str] = {}
```

## YAML and TOML Support

The loader checks for `.devsynth/project.yaml`. If not found, it falls back to the `pyproject.toml` section. Saving can be directed to either format based on user preference, allowing teams to keep configuration alongside existing project files.

## CLI Autocompletion

Commands can expose key completion by returning known configuration paths. Example Bash snippet:

```bash
_complete_devsynth_config_keys() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(devsynth config complete-keys "$cur") )
}
complete -F _complete_devsynth_config_keys devsynth
```

## Implementation Status

This feature is **implemented**. See `src/devsynth/config/loader.py` for the
reference implementation.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/unified_configuration_loader.feature`](../../tests/behavior/features/unified_configuration_loader.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
