---
author: DevSynth Team
date: '2025-07-20'
last_reviewed: '2025-07-20'
status: active
tags:
  - operations
  - runbook
---

# Operations Runbook

This runbook outlines routine operational tasks for DevSynth when deployed on Kubernetes.

## Scaling the API

Use the HorizontalPodAutoscaler to automatically scale based on CPU usage:

```bash
kubectl get hpa -n devsynth
```

Manual scaling can be performed with:

```bash
kubectl scale deployment devsynth-api --replicas=3 -n devsynth
```

## Restarting Services

```bash
kubectl rollout restart deployment/devsynth-api -n devsynth
```

## Checking Logs

```bash
kubectl logs deployment/devsynth-api -n devsynth
```

## Monitoring

Prometheus is available at `http://prometheus.dev.svc:9090` and Grafana at `http://grafana.dev.svc:3000` within the cluster. Use these dashboards to monitor request rates and latency metrics.
