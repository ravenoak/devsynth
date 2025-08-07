# Rollback Procedure

If a deployment needs to be rolled back, use the following steps:

1. Stop the current stack:
   ```bash
   scripts/deployment/stop_stack.sh
   ```
2. Redeploy the previous image tag:
   ```bash
   docker compose pull devsynth:<previous_tag>
   docker compose up -d
   ```
3. Verify services are healthy:
   ```bash
   scripts/deployment/health_check.sh
   ```
