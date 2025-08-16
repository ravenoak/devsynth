#!/usr/bin/env bash
set -euo pipefail

# Build and publish the DevSynth image to a registry.
# Usage: publish_image.sh [tag] [service]
#   tag: image tag to publish (default: latest)
#   service: compose service to publish (default: devsynth-api)

TAG=${1:-latest}
SERVICE=${2:-devsynth-api}
if [[ "$EUID" -eq 0 ]]; then
  echo "Please run this script as a non-root user." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but could not be found in PATH." >&2
  exit 1
fi

if [[ ! "$TAG" =~ ^[a-zA-Z0-9._-]+$ ]]; then
  echo "Invalid tag: $TAG" >&2
  exit 1
fi
if [[ ! "$SERVICE" =~ ^[a-zA-Z0-9._-]+$ ]]; then
  echo "Invalid service: $SERVICE" >&2
  exit 1
fi

export DEVSYNTH_IMAGE_TAG="$TAG"

# Ensure environment file permissions
ENV_FILE=".env.production"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing environment file: $ENV_FILE" >&2
  exit 1
fi
if [[ $(stat -c %a "$ENV_FILE") != "600" ]]; then
  echo "Environment file $ENV_FILE must have 600 permissions" >&2
  exit 1
fi
ENV_ARGS=(--env-file "$ENV_FILE")

# Build the image with the specified tag
docker compose "${ENV_ARGS[@]}" -f docker-compose.production.yml build "$SERVICE"

# Push the image to the configured registry
docker compose "${ENV_ARGS[@]}" -f docker-compose.production.yml push "$SERVICE"
