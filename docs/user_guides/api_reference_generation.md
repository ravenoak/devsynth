---
title: "API Reference Generation"
date: "2025-08-08"
version: "0.1.0-alpha.1"
tags:
  - "user-guide"
  - "documentation"
  - "api"
  - "reference"
author: "DevSynth Team"
last_reviewed: "2025-08-08"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; API Reference Generation
</div>

# API Reference Generation

This guide explains how to generate API reference pages for DevSynth using the `scripts/gen_ref_pages.py` command. The script scans project source directories, creates a navigation tree, and writes Markdown files under `docs/api_reference/` for inclusion in the documentation site.

## Usage

1. Ensure the environment provisioning script has been run and dependencies are installed.
2. From the repository root, generate API reference pages:

   ```bash
   poetry run python scripts/gen_ref_pages.py
   ```
3. Validate by building the documentation site, which reruns the generator via the MkDocs build pipeline:

   ```bash
   poetry run mkdocs build --strict
   ```

## End-to-End Example

```bash
$ poetry run python scripts/gen_ref_pages.py
Generating API reference for src/devsynth
$ poetry run mkdocs build --strict
INFO     -  Building documentation...
INFO     -  Documentation built in "site"
```

Open `site/index.html` in a browser to browse the full reference. Example generated pages are provided under `docs/api_reference/`. The script reads project structure from `manifest.yaml` if available and defaults to `src/` otherwise.

## Implementation Status

The generation script is integrated with MkDocs through the `gen-files` plugin and invoked automatically during documentation builds, ensuring API pages regenerate during each build and are validated with the `--strict` flag.
