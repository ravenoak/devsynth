# Deployment Configurations

This directory contains Docker Compose files for running DevSynth and its dependencies.

- `docker-compose.yml` – core services (DevSynth API and ChromaDB)
- `docker-compose.monitoring.yml` – optional monitoring stack with Prometheus and Grafana

Use these files together to spin up a complete local environment:

```bash
# Start DevSynth with monitoring
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
```
