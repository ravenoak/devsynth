FROM python:3.12-slim

ARG USERNAME=dev
ARG USER_UID=1000

# Disallow building with root user
RUN if [ "$USERNAME" = "root" ]; then echo "USERNAME must be non-root" >&2; exit 1; fi

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
ENV POETRY_VERSION=2.1.3 \
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
RUN useradd -m -u ${USER_UID} ${USERNAME}

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock* ./
USER ${USERNAME}
RUN poetry install --all-groups --extras "dev chromadb retrieval dsp memory llm docs minimal" --no-root

# Ensure the virtual environment binaries are on PATH
ENV PATH="/workspace/.venv/bin:$PATH"

# Default command
#CMD ["poetry", "run", "pytest", "-q"]
