# Deployment Policy

This policy defines best practices for deployment, CI/CD, and operational safety in DevSynth.

## Key Practices
- Use infrastructure-as-code for all deployment scripts and configs (e.g., Docker, Compose, Terraform).
- Store deployment docs and scripts in `deployment/` and document the process in `deployment/README.md`.
- Automate deployment via CI/CD; require all tests to pass and review/approval before production deploys.
- Use environment variables or secrets management for credentials; never hardcode secrets.
- Document rollback and incident response procedures in deployment docs.
- Require post-deployment verification (smoke tests, monitoring checks).
- Limit production deployment permissions to authorized roles/agents.
- Maintain observability: log standards, monitoring, and alerting must be documented and followed.
- Provide Docker Compose files for local and production deployments in the
  `deployment/` directory. The monitoring compose file enables Prometheus metrics
  scraping and Grafana dashboards.

## Artifacts
- Deployment Scripts: `deployment/`
- Deployment Docs: `deployment/README.md`
- CI/CD Config: `.github/workflows/` or `ci/`
- Monitoring/Logging: `deployment/monitoring.md` (if present)

## Compose Usage

Example command to start the core services with monitoring:

```bash
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
```


## References
- See [Testing Policy](testing.md) for release testing.
- See [Maintenance Policy](maintenance.md) for post-release support.

