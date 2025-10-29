---
author: DevSynth Team
date: '2025-08-29'
last_reviewed: '2025-08-29'
status: published
tags:
- developer-guide
- security

title: Security Audit Guide
version: '0.1.0a1'
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Security Audit Guide
</div>

# Security Audit Guide

Use the security audit command to validate required security settings and run
static analysis and dependency checks.

## Running the Audit

```bash
DEVSYNTH_PRE_DEPLOY_APPROVED=true poetry run python scripts/security_audit.py --report audit.json
```

The command performs the following routines:

- verifies mandatory security flags
- runs Bandit static analysis
- runs Safety dependency scanning
- writes a JSON summary to the path provided by `--report`

The JSON file contains `bandit` and `safety` fields with values `passed`,
`failed`, or `skipped`.

## Troubleshooting

- Ensure all required environment variables are set before running the audit.
- A non-zero exit code indicates a failed check; inspect the report for details.
