---
author: DevSynth Team
date: '2025-08-17'
last_reviewed: '2025-08-17'
status: active
tags:
  - deployment
  - automation
title: Deployment Automation
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Deployment</a> &gt; Deployment Automation
</div>

## Prerequisites

- Run the environment provisioning script.
- Install Docker and Docker Compose.
- Create an environment file such as `.env.development` and set its permissions to `600`.
- Execute deployment commands as a non-root user.

## Automated Deployment

1. Bootstrap the environment:

   ```bash
   scripts/deployment/bootstrap_env.sh <environment>
   ```

2. Start the stack:

   ```bash
   scripts/deployment/start_stack.sh <environment>
   ```

3. Verify services:

   ```bash
   scripts/deployment/check_health.sh <environment>
   ```

4. Stop the stack when finished:

   ```bash
   scripts/deployment/stop_stack.sh <environment>
   ```

All deployment scripts validate environment file permissions and refuse to run as root.
