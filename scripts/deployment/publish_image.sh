#!/usr/bin/env bash
set -euo pipefail

# Build and publish the DevSynth image to a registry.
# Usage: publish_image.sh [tag]
#   tag: image tag to publish (default: latest)

TAG=${1:-latest}
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

export DEVSYNTH_IMAGE_TAG="$TAG"

# Build the image with the specified tag

docker compose build devsynth

# Push the image to the configured registry

docker compose push devsynth
