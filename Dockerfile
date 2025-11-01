FROM python:3.12-slim AS base

# Core environment vars and set a Poetry home outside /root so non-root user can access it
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	POETRY_VERSION=1.8.3 \
	POETRY_HOME=/opt/poetry \
	PORT=8501

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Poetry into POETRY_HOME (instead of /root) and expose via symlink
RUN curl -sSL https://install.python-poetry.org | python - && \
	ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Create in-project virtualenv so it lives under /app/.venv (will be chowned later)
RUN poetry config virtualenvs.in-project true

# Copy only dependency descriptors first for layer caching
COPY pyproject.toml poetry.lock* /app/

# Install production dependencies (retry without group filter if lock missing)
RUN poetry install --no-interaction --no-ansi --without dev || \
	poetry install --no-interaction --no-ansi

# Copy project source
COPY cooking_assistant /app/cooking_assistant
COPY app /app/app
COPY scripts /app/scripts
COPY data /app/data

# Create a non-root user for security and ensure ownership of app + in-project venv + poetry home
RUN useradd -m streamer && chown -R streamer:streamer /app /opt/poetry
USER streamer

EXPOSE 8501

# Default environment file can be mounted; fallback STRICT_REAL_DATA=0
ENV STRICT_REAL_DATA=0

ENTRYPOINT ["poetry", "run", "streamlit", "run", "app/streamlit/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
