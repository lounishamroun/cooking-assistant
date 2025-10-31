FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	POETRY_VERSION=1.8.3 \
	PORT=8501

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python - && \
	ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy only dependency descriptors first for layer caching
COPY pyproject.toml poetry.lock* /app/

# Install production dependencies (no dev extras to keep image small)
RUN poetry install --no-interaction --no-ansi --without dev || \
	poetry install --no-interaction --no-ansi

# Copy project source
COPY cooking_assistant /app/cooking_assistant
COPY app /app/app
COPY scripts /app/scripts
COPY data /app/data

# Create a non-root user for security
RUN useradd -m streamer && chown -R streamer:streamer /app
USER streamer

EXPOSE 8501

# Default environment file can be mounted; fallback STRICT_REAL_DATA=0
ENV STRICT_REAL_DATA=0

ENTRYPOINT ["/root/.local/bin/poetry", "run", "streamlit", "run", "app/streamlit/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
