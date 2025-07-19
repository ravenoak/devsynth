---
author: DevSynth Team
date: '2025-07-15'
last_reviewed: '2025-07-15'
status: active
tags:
  - deployment
  - monitoring
---

# Monitoring and Logging

DevSynth exposes Prometheus metrics on `/metrics` and structured logs via the standard logging configuration. When using Docker Compose the `prometheus` service collects metrics from the `devsynth` container.

## Enabling Prometheus

1. Start the stack:
   ```bash
   docker compose up -d devsynth prometheus
   ```
2. Open `http://localhost:9090` to query metrics.

## Logs

Container logs are written to the `./logs` directory mounted by `docker-compose.yml`. Review these files or use `docker compose logs` to stream logs.
