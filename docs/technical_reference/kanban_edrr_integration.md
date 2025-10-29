---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
  - technical-reference
title: 'Kanban-EDRR Integration: Continuous Flow'
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; 'Kanban-EDRR Integration: Continuous Flow'
</div>

# Kanban-EDRR Integration: Continuous Flow

## Overview

This document describes how DevSynth's EDRR methodology can operate within a
Kanban workflow. Unlike time-boxed sprints, Kanban focuses on continuous delivery
and limits the amount of work in progress (WIP) at each stage.

**Implementation Status:** Initial Kanban adapter is available with basic WIP
limit handling and simple phase progression rules.

## Key Concepts

1. **Continuous Progression**: Items advance through EDRR phases individually.
2. **WIP Limits**: Each phase can define a maximum number of active items.
3. **Pull-Based Advancement**: Work only moves forward when capacity exists.
4. **Board Integration**: The adapter can be extended to integrate with common
   Kanban boards for visualization.

## Configuration Example

```yaml
methodologyConfiguration:
  type: "kanban"
  settings:
    wipLimits:
      expand: 3
      differentiate: 2
      refine: 2
      retrospect: 1
```

## Adapter Behaviour

- `should_start_cycle` always returns `True`, allowing new items to enter the
  pipeline at any time.
- `should_progress_to_next_phase` checks the WIP limit of the next phase before
  allowing advancement.
- Reports include a summary of WIP counts for each phase.

## Usage Tips

- Adjust `wipLimits` to match your team's capacity.
- Combine with the bulkhead and circuit breaker utilities when calling external
  services for increased resilience.
