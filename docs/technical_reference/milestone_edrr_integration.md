---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
  - technical-reference
title: 'Milestone-EDRR Integration: Approval Gates'
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; 'Milestone-EDRR Integration: Approval Gates'
</div>

# Milestone-EDRR Integration: Approval Gates

## Overview

This guide explains how DevSynth's EDRR process can align with milestone-based
projects that require formal approvals between stages. The milestone adapter
provides simple hooks for tracking approvals and generating compliance reports.

**Implementation Status:** Basic milestone adapter implemented with configurable
approval gates and approver lists.

## Key Concepts

1. **Event-Driven Progression**: Phases advance when milestones are reached.
2. **Approval Gates**: Optional approvals can be required after each phase.
3. **Compliance Reporting**: Reports capture approvers and approval status.
4. **Regulated Environments**: Useful for teams operating under strict
   compliance requirements.

## Configuration Example

```yaml
methodologyConfiguration:
  type: "milestone"
  settings:
    approvalRequired:
      afterExpand: true
      afterDifferentiate: true
      afterRefine: true
      afterRetrospect: false
    approvers: ["tech-lead", "product-owner"]
```

## Adapter Behaviour

- `should_start_cycle` simply returns `True`, assuming milestone scheduling is
  handled externally.
- `should_progress_to_next_phase` checks the `approved` flag in results when a
  phase requires approval.
- `generate_reports` produces a short compliance summary.

## Usage Tips

- Capture the approving individual's identity in the phase results for audit
  purposes.
- Combine with the report generation API to archive milestone documentation.
