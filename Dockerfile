# DevSynth Dockerfile
# Multi-stage build for development, testing, and production environments

FROM python:3.12-slim AS base

ARG USERNAME=dev
ARG USER_UID=1000

# Disallow building with root user
RUN if [ "$USERNAME" = "root" ]; then echo "USERNAME must be non-root" >&2; exit 1; fi

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        cargo \
        cmake \
        libssl-dev \
        libffi-dev \
        libopenblas-dev \
        liblmdb-dev \
        libomp-dev \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==1.8.2"

# Create non-root user
RUN useradd -m -u ${USER_UID} ${USERNAME}

WORKDIR /workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

# Copy dependency files first for caching
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock* ./

# Builder stage to install dependencies
FROM base AS builder
WORKDIR /workspace
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock* ./
USER ${USERNAME}
RUN poetry install --with dev,docs --all-extras --no-root

# Development stage with all dependencies and dev tools
FROM base AS development
COPY --from=builder --chown=${USERNAME}:${USERNAME} /workspace/.venv /workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

# Copy source and tests
COPY --chown=${USERNAME}:${USERNAME} src ./src
COPY --chown=${USERNAME}:${USERNAME} tests ./tests
COPY --chown=${USERNAME}:${USERNAME} docs ./docs
COPY --chown=${USERNAME}:${USERNAME} scripts ./scripts
COPY --chown=${USERNAME}:${USERNAME} templates ./templates

USER ${USERNAME}
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["poetry", "run", "pytest", "-q"]

# Testing stage with minimal dependencies needed for testing
FROM development AS testing

# Install additional packages required for running the test suite
RUN poetry install --with dev --no-root

CMD ["poetry", "run", "pytest", "-q"]

# Production stage with minimal dependencies
FROM base AS production
COPY --from=builder --chown=${USERNAME}:${USERNAME} /workspace/.venv /workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

# Copy only source code (no tests)
COPY --chown=${USERNAME}:${USERNAME} src ./src

USER ${USERNAME}

# Default to a safe, minimal command that verifies installation.
# Override with: docker run --rm devsynth:latest poetry run devsynth <command>
CMD ["poetry", "run", "devsynth", "--help"]
