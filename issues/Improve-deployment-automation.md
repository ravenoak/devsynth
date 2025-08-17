# Improve deployment automation
Milestone: 0.2.0
Status: open

Priority: medium
Dependencies: None


Current Docker Compose workflows require manual steps.

- Add scripts for environment bootstrapping and health checks
- Integrate Docker image publishing into CI pipeline
- Provide rollback instructions and test coverage
- Enforce non-root execution and strict `.env` permissions in deployment scripts with smoke tests

## Progress
- 2025-02-19: no automation scripts added yet.

- No progress yet

## References

- [docker-compose.yml](../docker-compose.yml)
- [scripts/deployment](../scripts/deployment)
