---
author: DevSynth Team
date: '2025-08-25'
last_reviewed: '2025-08-25'
status: stable
tags:
- api
- reference
title: Public API Surface
version: "0.1.0a1"
---

# Public API Surface

This document enumerates the stable, supported public API of the DevSynth Python package. Items listed here follow semantic versioning guarantees:
- Additive changes are allowed in minor versions.
- Backwards-incompatible removals/renames only occur in major versions and are preceded by a deprecation period.

See also: docs/policies/deprecation_policy.md for policy and timelines.

## Package Root: `devsynth`

Stable exports available from `import devsynth`:
- `__version__` (str): project version.
- Logging helpers (lazily exported):
  - `DevSynthLogger`
  - `set_request_context`
  - `clear_request_context`
  - `get_logger`
  - `setup_logging`
- Initialization:
  - `initialize_subpackages()` — optional helper to import subpackages eagerly when necessary.

Notes:
- These symbols are re-exported via lazy attribute access to keep import-time side effects minimal.
- Additional internal modules are not considered public unless explicitly documented here or referenced from the package root.

## CLI

The supported CLI entrypoint is `devsynth` with subcommands documented in:
- docs/user_guides/cli_command_reference.md

The legacy wrapper `scripts/run_all_tests.py` is deprecated in favor of `devsynth run-tests`. It currently issues a `DeprecationWarning` and will be removed per the deprecation schedule (v1.0).

## Compatibility Contract

- Import stability: The exports listed above are guaranteed to exist across patch and minor versions.
- Behavior: Function signatures and core behavior will remain backwards-compatible across minor versions. See CHANGELOG for notable changes.
- Deprecations: Items marked deprecated will emit warnings and are scheduled for removal as documented.

## Out of Scope (Internal)

Modules under `devsynth.*` not re-exported at the package root or listed here are considered internal and may change without notice.
