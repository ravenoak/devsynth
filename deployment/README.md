# Deployment Configurations

This directory contains Docker Compose files and helper scripts for running DevSynth and its dependencies.

- `docker-compose.yml` – core services (DevSynth API and ChromaDB)
- `docker-compose.monitoring.yml` – optional monitoring stack with Prometheus and Grafana
- `bootstrap_env.sh` – build and start DevSynth with monitoring
- `health_check.sh` – verify running services
- `bootstrap_with_health_check.sh` – start the stack and run health checks

All scripts perform basic security checks, refusing to run as root,
verifying required tooling, and warning if `.env` files are world-readable.

Use these files together to spin up a complete local environment:

```bash
# Start DevSynth with monitoring
./deployment/bootstrap_env.sh

# Or start and verify in one step
./deployment/bootstrap_with_health_check.sh
```

Check service status:

```bash
./deployment/health_check.sh
```
