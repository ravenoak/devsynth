# Rollback Procedure

If a deployment needs to be rolled back, use the dedicated rollback script.

1. Revert the stack to a previous image tag:
   ```bash
   scripts/deployment/rollback.sh <previous_tag> [environment]
   ```
   This stops the stack, pulls the specified tag, and redeploys the service.
2. Verify services are healthy:
   ```bash
   scripts/deployment/health_check.sh
   ```
3. (Optional) Republish the previous image tag as `latest` if the rollback is permanent:
   ```bash
   scripts/deployment/publish_image.sh <previous_tag>
   ```
