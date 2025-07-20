---
author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-07-10"
status: active
tags:

- deployment
- docker
- configuration
- foundation-stabilization

title: DevSynth Deployment Guide
version: 0.1.0
---

# DevSynth Deployment Guide

This guide provides comprehensive instructions for deploying DevSynth in various environments using Docker and the configuration system.

## Prerequisites

- Docker Engine 24.0.0 or higher
- Docker Compose 2.20.0 or higher
- Git
- Access to required environment variables (API keys, etc.)


## Quick Start

For a quick local development setup:

```bash

# Clone the repository

git clone https://github.com/ravenoak/devsynth.git
cd devsynth

# Set up environment variables (optional for development)

cp .env.example .env

# Edit .env with your settings

# Start the development environment

docker compose up -d

# Check the status

docker compose ps
```

Logs are written to the `./logs` directory by default when running via
Docker Compose. Ensure this directory exists so containers can write log files.

### Using Go-Task

The `Taskfile.yml` provides shortcuts for common container commands. After
installing [`go-task`](https://taskfile.dev), you can build and start the
environment with:

```bash
task docker:build
task docker:up
```

Stop the stack with `task docker:down` and view logs using `task docker:logs`.

## Deployment Environments

DevSynth supports multiple deployment environments, each with its own configuration:

- **Development**: For local development with debugging enabled
- **Testing**: For running tests with mock services
- **Staging**: For pre-production testing with production-like settings
- **Production**: For production deployment with security hardening


## Environment-Specific Deployment

### Development Environment

```bash

# Start the development environment

docker compose up -d

# View logs

docker compose logs -f

# Run development tools

docker compose --profile tools up -d dev-tools
docker compose exec dev-tools bash
```

## Testing Environment

```bash

# Run tests

docker compose --profile test up test-runner

# Run specific tests

docker compose --profile test run test-runner pytest tests/unit/
```

## Staging Environment

```bash

# Set required environment variables

export DEVSYNTH_ENV=staging
export DEVSYNTH_LLM_PROVIDER=openai
export DEVSYNTH_OPENAI_API_KEY=your-api-key

# Build and start staging environment

docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

## Production Environment

Use the production compose file which includes Prometheus and Grafana for monitoring.

```bash

# Set required environment variables

export DEVSYNTH_ENV=production
export DEVSYNTH_LLM_PROVIDER=openai
export DEVSYNTH_OPENAI_API_KEY=your-api-key
export DEVSYNTH_OPENAI_MODEL=gpt-4

# Build and start production environment

docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

## Configuration

DevSynth uses a hierarchical configuration system with environment-specific overrides:

1. **Default Configuration**: Base settings in `config/default.yml`
2. **Environment Configuration**: Environment-specific settings in `config/{environment}.yml`
3. **Environment Variables**: Override configuration with environment variables
4. **Runtime Configuration**: Dynamic configuration at runtime


### Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVSYNTH_ENV` | Deployment environment | `development` |
| `DEVSYNTH_LOG_LEVEL` | Logging level | Depends on environment |
| `DEVSYNTH_MEMORY_STORE` | Memory store to use | `ChromaDB` |
| `DEVSYNTH_LLM_PROVIDER` | Provider to use | `openai` |
| `DEVSYNTH_OPENAI_API_KEY` | OpenAI API key | None |
| `DEVSYNTH_OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `DEVSYNTH_MAX_WORKERS` | Maximum worker threads | Depends on environment |

### Validating Configuration

Use the validation script to check your configuration:

```bash

# Validate all environments

./scripts/validate_config.py

# Validate specific environments

./scripts/validate_config.py --environments development production
```

## Health Checks and Monitoring

DevSynth includes built-in health checks for all services:

- **DevSynth API**: `http://localhost:8000/health`
- **ChromaDB**: `http://localhost:8001/api/v1/heartbeat`


Monitor container health with:

```bash
docker compose ps
docker compose top
```

Prometheus scrapes metrics from `http://localhost:8000/metrics` and Grafana is
available at `http://localhost:3000` (default credentials admin/admin).

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Errors**
   - Check that ChromaDB is running: `docker compose ps ChromaDB`
   - Verify network connectivity: `docker compose exec devsynth ping ChromaDB`
   - Check ChromaDB logs: `docker compose logs ChromaDB`

2. **API Key Issues**
   - Ensure environment variables are set correctly
   - Check for API key expiration or rate limiting
   - Verify provider status

3. **Container Startup Failures**
   - Check container logs: `docker compose logs devsynth`
   - Verify environment variables are set
   - Check disk space and permissions


### Logs

Access logs for troubleshooting:

```bash

# View all logs

docker compose logs

# View specific service logs

docker compose logs devsynth

# Follow logs in real-time

docker compose logs -f
```

## Performance Tuning

### Resource Allocation

Adjust container resources in `docker-compose.yml`:

```yaml
services:
  devsynth:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Configuration Optimization

Optimize performance through configuration:

1. Adjust `max_workers` based on available CPU cores
2. Configure cache TTL based on data volatility
3. Enable memory-efficient mode for resource-constrained environments
4. Tune LLM parameters for speed vs. quality tradeoffs


## Security Considerations

### Production Hardening

For production deployments:

1. Use non-root users (already configured in Dockerfile)
2. Enable encryption at rest and in transit
3. Implement API key rotation
4. Configure rate limiting
5. Use secrets management for sensitive values
6. Enable audit logging


### Secrets Management

For sensitive information:

```bash

# Using Docker secrets (swarm mode)

docker secret create devsynth_openai_key /path/to/key_file
docker stack deploy -c docker-compose.yml -c docker-compose.production.yml devsynth

# Using environment files with restricted permissions

chmod 600 .env.production
```

## Backup and Recovery

### Data Backup

Back up persistent data:

```bash

# Backup ChromaDB data

docker compose stop ChromaDB
tar -czf ChromaDB-backup.tar.gz -C /data/devsynth/ChromaDB .
docker compose start ChromaDB
```

## Disaster Recovery

1. Restore from backup:

   ```bash
   mkdir -p /data/devsynth/ChromaDB
   tar -xzf ChromaDB-backup.tar.gz -C /data/devsynth/ChromaDB
   ```

2. Rebuild and restart:

   ```bash
   docker compose down
   docker compose up -d
   ```

## Upgrading

### Version Upgrades

To upgrade DevSynth:

```bash

# Pull latest changes

git pull

# Rebuild containers

docker compose build

# Apply migrations (if any)

docker compose run --rm devsynth python -m devsynth.migrations

# Restart services

docker compose down
docker compose up -d
```

## Conclusion

This deployment guide covers the basics of deploying DevSynth in various environments. For advanced deployment scenarios, including Kubernetes deployment, high availability configurations, and enterprise integrations, refer to the Advanced Deployment Guide.
## Implementation Status

This feature is **planned** and not yet implemented.
