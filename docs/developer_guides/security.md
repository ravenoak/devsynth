---

title: "Security Audit"
date: "2025-07-21"
version: "0.1.0a1"
tags:
  - "developer-guide"
  - "security"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-21"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Security Audit
</div>

# Security Audit

The `devsynth security-audit` command aggregates multiple scanners to help
protect the project. By default all checks run. The legacy wrapper script is
deprecated and will be removed in a future release.

## Checks

- **Safety** – Python dependency vulnerability scan.
- **Bandit** – static analysis for common security issues.
- **Secrets scan** – searches the repository for strings resembling API keys.
- **OWASP Dependency Check** – invokes the OWASP Dependency-Check tool for
  third-party library analysis.

## Usage

Run all checks:

```bash
devsynth security-audit
```

Skip specific scanners using flags:

```bash
devsynth security-audit --skip-bandit --skip-secrets --skip-owasp --skip-safety
```

`--skip-static` remains an alias for `--skip-bandit` for backward compatibility.
