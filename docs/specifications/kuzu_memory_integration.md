---
title: Kuzu Memory Integration
author: DevSynth Team
date: 2025-01-01
status: draft
---

# Summary

See [Kuzu Memory Integration feature](../features/kuzu_memory_integration.md) for usage overview.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

The Kuzu-backed memory store previously raised an `AttributeError` when
configuration attempted to access `kuzu_embedded`. This obscured the
intended fallback to an in-memory store when the embedded engine is
disabled or unavailable.

## Specification

- The `DEVSYNTH_KUZU_EMBEDDED` environment variable governs whether the
  embedded Kuzu engine should be used. Absent or invalid values fall back
  to the default.
- `src/devsynth/config/settings.py` exposes `kuzu_embedded` at the module
  level and keeps it synchronised when `get_settings` reloads. Callers
  may import `kuzu_embedded` directly or access it via the settings
  object.
- `KuzuMemoryStore.create_ephemeral()` starts an ephemeral store using
  the embedded engine when available. If `kuzu_embedded` is `False` or
  the engine cannot load, the store transparently falls back to the
  in-memory implementation.

## Acceptance Criteria

- Environment variables override defaults, and the module-level
  `kuzu_embedded` value mirrors `get_settings()`.
- Initialising an ephemeral Kuzu store succeeds regardless of the
  embedded engine's availability, using a fallback when necessary.
