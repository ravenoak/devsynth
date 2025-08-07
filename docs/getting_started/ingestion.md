# Ingestion Pipeline

The `devsynth ingest` command runs the Expand, Differentiate, Refine, and Retrospect pipeline for a project.

## Non-interactive usage

Use the `--yes` flag to auto-confirm prompts and `--priority` to set a project priority without manual input:

```bash
devsynth ingest manifest.yaml --yes --priority high
```

These options are useful in scripts or CI environments where no user interaction is available.
