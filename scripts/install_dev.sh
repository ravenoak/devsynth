#!/usr/bin/env bash
set -euo pipefail

# Install DevSynth with development dependencies and required extras
poetry install --with dev --extras tests retrieval chromadb api
