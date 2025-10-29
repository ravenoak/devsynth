---
title: "WSDE-EDRR Workflow"
date: "2025-08-01"
version: "0.1.0a1"
tags:
  - implementation
  - wsde
  - edrr
  - workflow
status: active
author: "DevSynth Team"
last_reviewed: "2025-08-01"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; WSDE-EDRR Workflow
</div>

# WSDE-EDRR Workflow

The finalized WSDE-EDRR workflow links the Worker Self-Directed Enterprise team model with the Expand–Differentiate–Refine–Retrospect methodology.

## Phase Progression

Each transition invokes `progress_roles`, reassigning roles for the new phase and flushing queued memory updates through the provided memory manager. The coordinator retains the mapping so external consumers can inspect current responsibilities.

## Memory Synchronization

Queued updates collected during a phase are flushed on boundary crossing. This prevents collaboration utilities from stalling and keeps cross-store data in sync.

## Role Accessibility

Role assignments for the active phase are accessible via `get_role_assignments`, enabling downstream processes to understand which agent holds a given responsibility.
