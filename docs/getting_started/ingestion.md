# Ingestion Pipeline

The `devsynth ingest` command runs the Expand, Differentiate, Refine, and Retrospect pipeline for a project.

## Non-interactive usage

Use `--non-interactive` to bypass prompts. Combine it with `--yes` or the
`DEVSYNTH_AUTO_CONFIRM=1` environment variable to auto-approve confirmations.
For a one-flag solution, `--defaults` implies both options. You can also set
defaults such as project priority with `--priority` or by using
`DEVSYNTH_INGEST_PRIORITY`.

```bash
devsynth ingest manifest.yaml --non-interactive --yes --priority high

# Equivalent shorthand
devsynth ingest --defaults --priority high
```

Setting `DEVSYNTH_INGEST_NONINTERACTIVE=1` enables non-interactive mode by
default. These options are useful in scripts or CI environments where no user
interaction is available.
