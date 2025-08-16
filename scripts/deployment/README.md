# Deployment Utilities

This directory contains helper scripts for managing DevSynth deployments.

## Rollback Procedure

1. Identify the previous image tag to restore.
2. Ensure the corresponding environment file (e.g. `.env.production`) exists with `600` permissions.
3. Run `scripts/deployment/rollback.sh <previous_tag> [environment]` as a non-root user.
4. The script stops the stack, pulls the specified tag, and verifies service health before completing.

All scripts in this directory refuse to run as the root user and validate environment file permissions to promote least privilege and prevent misconfiguration.
