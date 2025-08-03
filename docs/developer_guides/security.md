---
title: "Security Audit"
date: "2025-07-21"
version: "0.1.0"
tags:
  - "developer-guide"
  - "security"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-21"---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Security Audit
</div>

# Security Audit

The `security_audit.py` script aggregates multiple scanners to help protect the
project. By default all checks run.

## Checks

- **Safety** – Python dependency vulnerability scan.
- **Bandit** – static analysis for common security issues.
- **Secrets scan** – searches the repository for strings resembling API keys.
- **OWASP Dependency Check** – invokes the OWASP Dependency-Check tool for
  third-party library analysis.

## Usage

Run all checks:

```bash
python scripts/security_audit.py
```

Skip specific scanners using flags:

```bash
python scripts/security_audit.py --skip-bandit --skip-secrets --skip-owasp --skip-safety
```

`--skip-static` is retained as an alias for `--skip-bandit` for backward
compatibility.
