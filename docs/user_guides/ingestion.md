---
title: Ingestion
date: "2025-07-12"
version: "0.1.0-alpha.1"
tags:
  - user-guide
  - ingestion
status: draft
author: "DevSynth Team"
last_reviewed: "2025-07-12"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Ingestion
</div>

# Ingestion

Use the `devsynth ingest` command to run the Expand, Differentiate, Refine, Retrospect pipeline for a project.

## Non-interactive mode

Disable prompts when automating workflows by running:

```bash
devsynth ingest --non-interactive --yes
```

The `--defaults` flag combines both options:

```bash
devsynth ingest --defaults
```

Setting `DEVSYNTH_INGEST_NONINTERACTIVE=1` enables non-interactive mode by default. Pair with `DEVSYNTH_AUTO_CONFIRM=1` or `--yes` to auto-approve prompts.

## Implementation Status

.
