# DevSynth Dockerfile
# Multi-stage build for development, testing, and production environments

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

# Development stage with all dependencies and dev tools
FROM base AS development

# Install all dependencies including development dependencies
RUN poetry install --with dev --all-extras --no-root

# Copy source and tests
COPY src ./src
COPY tests ./tests
COPY docs ./docs
COPY scripts ./scripts
COPY templates ./templates

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}

ENV PATH="/workspace/.venv/bin:$PATH"

CMD ["poetry", "run", "pytest", "-q"]

# Testing stage with minimal dependencies needed for testing
FROM base AS testing

# Install dependencies needed for testing
RUN poetry install --with dev --extras "minimal memory retrieval" --no-root

# Copy source and tests
COPY src ./src
COPY tests ./tests

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}

ENV PATH="/workspace/.venv/bin:$PATH"

CMD ["poetry", "run", "pytest", "-q"]

# Production stage with minimal dependencies
FROM base AS production

# Install only production dependencies
#RUN poetry install --without dev --extras "minimal memory" --no-root
RUN poetry install --all-groups --extras "dev chromadb retrieval dsp memory llm docs minimal" --no-root

# Copy only source code (no tests)
COPY src ./src

# Ensure user owns workspace
RUN chown -R ${USERNAME}:${USERNAME} /workspace

USER ${USERNAME}

ENV PATH="/workspace/.venv/bin:$PATH"

CMD ["poetry", "run", "uvicorn", "devsynth.api:app", "--host", "0.0.0.0", "--port", "8000"]
