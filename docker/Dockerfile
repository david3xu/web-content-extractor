# Multi-stage build for smaller production image
FROM python:3.10-slim AS build

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1

# Set Poetry config
RUN poetry config virtualenvs.in-project true

# Copy pyproject.toml and poetry.lock
WORKDIR /app
COPY pyproject.toml ./
# Copy poetry.lock if it exists
COPY poetry.lock* ./

# Install dependencies (without development dependencies)
RUN poetry install --only main --no-interaction --no-ansi

# Second stage - runtime
FROM python:3.10-slim AS runtime

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Set working directory
WORKDIR /app

# Copy from build stage
COPY --from=build /app/.venv /app/.venv
COPY src /app/src
COPY README.md /app/

# Set PATH to include venv
ENV PATH="/app/.venv/bin:$PATH"

# Set Python path
ENV PYTHONPATH="/app:$PYTHONPATH"

# Set up logs and output directories
RUN mkdir -p /app/logs /app/output && \
    chown -R appuser:appuser /app/logs /app/output

# Set default config values
ENV WEB_EXTRACTOR_LOG_LEVEL="INFO" \
    WEB_EXTRACTOR_JSON_LOGS="true" \
    WEB_EXTRACTOR_HTTP_TIMEOUT="30.0" \
    WEB_EXTRACTOR_MAX_RETRIES="3" \
    WEB_EXTRACTOR_OUTPUT_DIRECTORY="/app/output"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/health'); response = conn.getresponse(); exit(0 if response.status == 200 else 1)"

# Expose port
EXPOSE 8000

# Set entrypoint to run API server
ENTRYPOINT ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0"]
