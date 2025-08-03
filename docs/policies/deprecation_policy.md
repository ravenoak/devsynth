---
author: DevSynth Team
date: '2025-07-31'
last_reviewed: '2025-07-31'
status: draft
tags:
- policy
title: Deprecation Policy
version: 0.1.0---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Deprecation Policy
</div>

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
are deprecated and scheduled for removal in v1.0.

Developers should migrate to the recommended replacements before the removal
version.
