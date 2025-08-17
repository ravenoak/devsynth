---
title: "API Reference Generation"
date: "2025-08-08"
version: "0.1.0-alpha.1"
tags:
  - "user-guide"
  - "documentation"
  - "api"
  - "reference"

status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-08"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; API Reference Generation
</div>

# API Reference Generation

This guide explains how to generate API reference pages for DevSynth using the `scripts/gen_ref_pages.py` command. The script scans project source directories, creates a navigation tree, and writes Markdown files under `api_reference/` for inclusion in the documentation site.

## Usage

1. Ensure the environment provisioning script has been run and dependencies are installed.
2. From the repository root, generate API reference pages:

   ```bash
   poetry run python scripts/gen_ref_pages.py
   ```
3. The script reads project structure from `manifest.yaml` if available. Generated pages appear under `docs/api_reference/` and are included in the MkDocs build.

## Implementation Status

.
