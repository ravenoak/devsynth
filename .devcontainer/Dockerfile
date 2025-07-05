FROM python:3.12-slim

# Install required build tools and headers for compiled dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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

# Environment configuration
ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/poetry/bin:$PATH"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Create non-root user
RUN useradd -m -u 1000 dev

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --with dev --all-extras --no-root

# Copy source and tests
COPY src ./src
COPY tests ./tests

# Use non-root user for subsequent commands
USER dev

# Ensure the virtual environment binaries are on PATH
ENV PATH="/workspace/.venv/bin:$PATH"

# Default command
CMD ["pytest", "-q"]
