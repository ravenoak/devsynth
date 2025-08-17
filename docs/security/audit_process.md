# Security Audit Process

DevSynth uses automated static analysis to detect security issues before deployment.

## Automated Checks

The `policy:gate` task runs the full audit:

```bash
poetry run task policy:gate
```

This invokes the following tools:

- **Bandit** – scans source code for common security flaws.
- **Safety** – checks project dependencies for known vulnerabilities.

The task fails if either tool reports a problem, preventing insecure builds from progressing in CI.

## Manual Execution

Developers can run the checks locally:

```bash
poetry run task security:bandit
poetry run task security:safety
```

Approve pre-deployment checks as needed and re-run `policy:gate` to verify compliance.
