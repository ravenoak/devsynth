---
title: "Configuration Reference"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
  - "reference"
  - "configuration"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Configuration Reference

## Feature Flags

DevSynth exposes several optional capabilities through feature flags. Flags are
stored in `.devsynth/project.yaml` (or the `devsynth` section of
`pyproject.toml`) under the `features` key.

### `experimental_features`

Enables opt‑in, unstable functionality. When disabled the application skips
code paths guarded by this flag, such as experimental DuckDB persistence
settings.

Use the CLI to toggle flags:

```bash
$ devsynth config enable-feature experimental_features
```

Programmatic checks are available via :mod:`devsynth.core.feature_flags`:

```python
from devsynth.core import feature_flags

if feature_flags.experimental_enabled():
    # execute experimental logic
    ...
```

After changing flag values, call :func:`feature_flags.refresh` to reload the
cached configuration.
