# DevSynth Dockerfile
# Development and testing environment

FROM python:3.12-slim AS base

ARG USERNAME=dev
ARG USER_UID=1000

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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

# Install Python dependencies
RUN poetry install --with dev --all-extras --no-root

# Copy source and tests
COPY src ./src
COPY tests ./tests

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}

ENV PATH="/workspace/.venv/bin:$PATH"

CMD ["poetry", "run", "pytest", "-q"]
