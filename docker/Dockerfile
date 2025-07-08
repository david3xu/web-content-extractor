# Multi-stage build for optimal image size
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy the project files
COPY . .

# Create output directory
RUN mkdir -p ./output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; response = requests.get('http://localhost:8000/health'); exit(0) if response.status_code == 200 else exit(1)" || exit 1

# Run the application
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--help"]
