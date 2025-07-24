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

DevSynth exposes Prometheus metrics on `/metrics` and structured logs via the standard logging configuration. When using Docker Compose or Kubernetes the `prometheus` service collects metrics from the `devsynth` container. Alertmanager can be enabled to receive alerts on failed health checks or high latency.

## Enabling Prometheus

1. Start the stack:
   ```bash
   docker compose up -d devsynth prometheus
   ```
2. Open `http://localhost:9090` to query metrics.

### Alerting

The provided Kubernetes manifests deploy Prometheus with Alertmanager. Customize alert rules in `prometheus-configmap.yaml` and configure Alertmanager receivers for email or chat notifications.

## Logs

Container logs are written to the `./logs` directory mounted by `docker-compose.yml` or retrieved with `kubectl logs` when running in Kubernetes.
## Implementation Status

Monitoring and alerting are **active** and continuously monitored.
