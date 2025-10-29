---
 title: "Rollback Procedures"
 author: "DevSynth Team"
 date: "2025-07-10"
 last_reviewed: "2025-07-10"
 status: "draft"
 version: "0.1.0a1"
 tags:
   - deployment
   - rollback
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Deployment</a> &gt; Rollback Procedures
</div>

# Rollback Procedures

This guide describes how to revert the DevSynth stack to a previous release.

## Quick Rollback

Use the helper script to stop the current stack, pull the specified image tag,
restart services, and verify their health:

```bash
scripts/deployment/rollback.sh <previous_tag> [environment]
```

If you prefer to perform the steps manually, follow the process below.

## Manual Steps

1. Stop the current stack:

   ```bash
   scripts/deployment/stop_stack.sh
   ```

2. Pull the previous image tag:

   ```bash
   docker pull ghcr.io/OWNER/REPO:previous-tag
   ```

3. Start the stack with the earlier image:

   ```bash
   scripts/deployment/start_stack.sh
   ```

4. Verify service health:

   ```bash
   scripts/deployment/health_check.sh
   ```

## Tests

After performing a rollback, validate the environment:

```bash
scripts/deployment/health_check.sh
poetry run pytest tests/unit/deployment/test_health_check_smoke.py
```

These smoke tests confirm that the core services and deployment scripts operate as expected.
