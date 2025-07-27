# DevSynth Dockerfile
# Multi-stage build for development, testing, and production environments

FROM python:3.12-slim AS base

ARG USERNAME=dev
ARG USER_UID=1000

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

# Copy dependency files first for caching
COPY pyproject.toml poetry.lock* ./

# Builder stage to install dependencies
FROM base AS builder
WORKDIR /workspace
COPY pyproject.toml poetry.lock* ./
RUN poetry install --with dev,docs --all-extras --no-root

# Development stage with all dependencies and dev tools
FROM base AS development
COPY --from=builder /workspace/.venv /workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

# Copy source and tests
COPY src ./src
COPY tests ./tests
COPY docs ./docs
COPY scripts ./scripts
COPY templates ./templates

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

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
COPY --from=builder /workspace/.venv /workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"

EXPOSE 8000

# Copy only source code (no tests)
COPY src ./src

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["poetry", "run", "uvicorn", "devsynth.api:app", "--host", "0.0.0.0", "--port", "8000"]
