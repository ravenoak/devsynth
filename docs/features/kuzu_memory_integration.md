---
title: "Kuzu Memory Integration"
date: "2025-08-13"
version: "0.1.0a1"
tags:
  - "documentation"
  - "feature"
status: "draft"
implementation_status: "partial"
author: "DevSynth Team"
last_reviewed: "2025-08-13"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Feature Documentation</a> &gt; Kuzu Memory Integration
</div>

# Kuzu Memory Integration

Feature: Kuzu memory integration

Integrates the Kuzu graph database as a memory store, providing persistent graph storage with automatic fallback to an in-memory implementation when the embedded engine is unavailable. The `DEVSYNTH_KUZU_EMBEDDED` environment variable controls use of the embedded engine.

## Related Documentation

- [Kuzu Memory Integration specification](../specifications/kuzu_memory_integration.md)
- [Memory Integration Guide](../developer_guides/memory_integration_guide.md)

!!! warning "Implementation status: Partial"
    - The current adapter emulates Kùzu behaviour with a JSON-backed in-memory store and NumPy-based similarity search, so it does not yet talk to a live Kùzu database.【F:src/devsynth/adapters/memory/kuzu_adapter.py†L1-L160】
    - Full cross-store synchronization and transactional durability remain open in the "Complete memory system integration" remediation issue.【F:issues/Complete-memory-system-integration.md†L1-L37】
    - The v0.1.0a1 execution plan schedules optional-backend guardrails (PR-3) to stabilize adapters like the Kùzu fallback alongside ChromaDB fixes.【F:docs/release/v0.1.0a1_execution_plan.md†L40-L72】
