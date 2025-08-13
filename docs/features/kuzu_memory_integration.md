---
title: "Kuzu Memory Integration"
date: "2025-08-13"
version: "0.1.0-alpha.1"
tags:
  - "documentation"
  - "feature"
status: "draft"
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
