# Stage 1: Builder
FROM nvcr.io/nvidia/pytorch:24.01-py3 AS builder

ENV PYTHON_VERSION=3.10
ENV POETRY_VENV=/app/.venv

# Install dependencies and Poetry, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION}-venv \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install --upgrade pip setuptools poetry==1.7.1 \
    && poetry config virtualenvs.in-project true

ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Copy only the dependency files first for better caching
COPY poetry.lock pyproject.toml ./

# Install dependencies without installing the package itself
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the application code
COPY . .

# Install the package and additional dependencies, then clean up caches
RUN poetry install --no-interaction --no-ansi \
    && pip install --upgrade wheel \
    && pip install ninja packaging \
    && pip install flash-attn --no-build-isolation \
    && rm -rf ~/.cache/pip

# Stage 2: Final Image
FROM nvcr.io/nvidia/pytorch:24.01-py3

ENV POETRY_VENV=/app/.venv
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Copy the virtual environment and application code from the builder
COPY --from=builder /app /app

EXPOSE 9000

CMD gunicorn --bind 0.0.0.0:9000 --workers 1 --timeout 0 app.app:app -k uvicorn.workers.UvicornWorker
