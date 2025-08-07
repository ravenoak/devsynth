# Deployment Configurations

This directory contains Docker Compose files and helper scripts for running DevSynth and its dependencies.

- `docker-compose.yml` – core services (DevSynth API and ChromaDB)
- `docker-compose.monitoring.yml` – optional monitoring stack with Prometheus and Grafana
- `bootstrap_env.sh` – build and start DevSynth with monitoring
- `health_check.sh` – verify running services

Use these files together to spin up a complete local environment:

```bash
# Start DevSynth with monitoring
./deployment/bootstrap_env.sh
```

Check service status:

```bash
./deployment/health_check.sh
```
