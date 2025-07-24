---
author: DevSynth Team
date: '2025-07-20'
last_reviewed: '2025-07-20'
status: active
tags:
  - operations
  - incident
---

# Incident Response Procedures

This document describes how to respond to production incidents affecting DevSynth.

## 1. Detection

Alerts from Prometheus Alertmanager or failed health checks trigger an incident.

## 2. Initial Triage

1. Confirm the alert by checking logs and metrics.
2. Identify which services are impacted.
3. Escalate to the DevOps on-call engineer if needed.

## 3. Mitigation Steps

- Restart affected deployments:
  ```bash
  kubectl rollout restart deployment/devsynth-api -n devsynth
  ```
- If the database is affected, verify the `chromadb` pod status and PVC health.
- Consult recent changes and roll back if necessary using `kubectl rollout undo`.

## 4. Post-Incident

1. Create an incident report documenting timeline and resolution.
2. Update runbooks and monitoring rules if gaps were discovered.
3. Conduct a blameless postmortem to improve processes.
