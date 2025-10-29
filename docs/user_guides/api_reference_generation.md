---
title: "API Reference Generation"
date: "2025-08-08"
version: "0.1.0a1"
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

DevSynth can generate API reference pages using the `devsynth generate-docs` command or the underlying `scripts/gen_ref_pages.py` script. Both approaches scan project source directories, create a navigation tree, and write Markdown files under `docs/api_reference/` for inclusion in the documentation site.

## CLI Command

Run the CLI to generate documentation from the current project:

```bash
poetry run devsynth generate-docs [--path PATH] [--output-dir DIR]
```

- `--path PATH`: Project directory to analyze (defaults to the current directory).
- `--output-dir DIR`: Output directory for the generated documentation (defaults to `docs/api_reference`).

See the [CLI Reference](cli_reference.md#generate-docs) for additional options.

## Script Usage

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
