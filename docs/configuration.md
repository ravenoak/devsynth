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

