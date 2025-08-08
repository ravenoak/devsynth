#!/usr/bin/env bash
set -euo pipefail

# Build and publish the DevSynth image to a registry.
# Usage: publish_image.sh [tag]
#   tag: image tag to publish (default: latest)

TAG=${1:-latest}
export DEVSYNTH_IMAGE_TAG="$TAG"

# Build the image with the specified tag

docker compose build devsynth

# Push the image to the configured registry

docker compose push devsynth
