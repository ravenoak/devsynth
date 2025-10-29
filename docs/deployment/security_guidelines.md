---
title: "Deployment Security Guidelines"
date: "2025-07-10"
version: "0.1.0a1"
tags:
  - deployment
  - security
status: "active"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Deployment</a> &gt; Deployment Security Guidelines
</div>

# Deployment Security Guidelines

These guidelines describe the baseline safeguards enforced by the deployment
scripts. Following them helps reduce accidental exposure of credentials and
limits the blast radius of compromised containers.

## Preflight Checks

The helper scripts perform several checks before taking action:

- Refuse to run as the `root` user to encourage least-privilege operation.
- Verify required tooling is available (`docker`, `docker compose`, and
  `curl` for health checks).
- Abort if a local `.env` file is more permissive than `600`.
- Validate the requested environment against an allowlist and ensure its
  `.env.<environment>` file exists with strict `600` permissions.
- Reject image tags that contain characters outside of `[A-Za-z0-9._-]` to
  prevent command injection through tag names.
- Health checks only accept `http` or `https` URLs and refuse any other
  protocol schemes.

## Runtime Safeguards

- Images are pulled with `--pull=always` and production builds use
  `--no-cache` to ensure the latest patched layers are used.
- Containers start with Docker's `no-new-privileges` option and include
  health checks that timeout quickly.

## Additional Recommendations

- Store secrets outside of version control and rotate them regularly.
- Review container logs for unusual activity and keep Docker up to date.

These practices will evolve as DevSynth matures; contributors should keep this
document current when introducing new deployment mechanisms.
