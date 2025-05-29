# DevSynth Dockerfile
# Multi-stage build for development, testing, and production environments

###################
# BASE STAGE
###################
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy project files
COPY pyproject.toml poetry.lock* ./

###################
# DEVELOPMENT STAGE
###################
FROM base AS development

# Install development dependencies
RUN poetry install --no-root --with dev

# Copy the rest of the application
COPY . .

# Install the application
RUN poetry install --with dev

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Command to run the application
CMD ["poetry", "run", "devsynth", "serve", "--debug"]

###################
# TESTING STAGE
###################
FROM base AS testing

# Install test dependencies
RUN poetry install --no-root --with test

# Copy the rest of the application
COPY . .

# Install the application
RUN poetry install --with test

# Run tests
CMD ["poetry", "run", "pytest"]

###################
# PRODUCTION STAGE
###################
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN groupadd -g 1000 devsynth && \
    useradd -u 1000 -g devsynth -s /bin/bash -m devsynth

# Set working directory
WORKDIR /app

# Copy virtual environment from base stage
COPY --from=base --chown=devsynth:devsynth $VENV_PATH /app/.venv

# Copy application code
COPY --chown=devsynth:devsynth ./src /app/src
COPY --chown=devsynth:devsynth ./pyproject.toml /app/

# Switch to non-root user
USER devsynth

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Command to run the application
CMD ["devsynth", "serve"]