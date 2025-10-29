---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: '2025-07-31'
status: draft
tags:
- policy
title: Deprecation Policy
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Deprecation Policy
</div>

# Deprecation Policy

DevSynth deprecates scripts and features prior to their removal. Deprecated
components remain available for the current minor release series and are
removed in the next major release.

## Schedule
- Announce deprecations with alternatives.
- Maintain deprecated items for the remainder of the current minor release
  series.
- Remove deprecated items in the next major release (v1.0).

For example, `scripts/alignment_check.py` and `scripts/validate_manifest.py`
are deprecated in favor of `devsynth align` and `devsynth validate-manifest`
and are scheduled for removal in v1.0.

Developers should migrate to the recommended replacements before the removal
version.

## Deprecation Notice

The following legacy scripts are deprecated and will be removed in v1.0
(scheduled for July 2026):

| Deprecated Script | Replacement Command | Removal Version |
|-------------------|---------------------|-----------------|
| `scripts/alignment_check.py` | `devsynth align` | v1.0 |
| `scripts/validate_manifest.py` | `devsynth validate-manifest` | v1.0 |
| `scripts/run_all_tests.py` | `devsynth run-tests` | v1.0 |
| `scripts/run_tests.sh` | `devsynth run-pipeline` | v1.0 |
| `scripts/validate_config.py` | `devsynth inspect-config` | v1.0 |
| `scripts/test_metrics.py` | `devsynth test-metrics` | v1.0 |
| `scripts/security_audit.py` | `devsynth security-audit` | v1.0 |

All deprecated scripts remain available throughout the current minor release
series but will be removed once v1.0 is released.
