# Web Content Extractor - Execution Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Setup: Poetry vs Conda](#environment-setup-poetry-vs-conda)
3. [Installation & Setup](#installation--setup)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [API Usage](#api-usage)
7. [Docker Deployment](#docker-deployment)
8. [Azure Functions Deployment](#azure-functions-deployment)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Development Workflow](#development-workflow)

## Quick Start

Choose **one** of the following workflows:

### Poetry-Only Workflow (Recommended)

```bash
# 1. Install Poetry if not installed
pip install poetry

# 2. Install dependencies (including dev dependencies)
poetry install --with dev

# 3. Activate Poetry environment (choose one method)
# Method A: Use poetry run for each command
poetry run python --version  # Verify you're in the right environment

# Method B: Activate the Poetry environment directly
poetry env info --path  # Get the path to the Poetry environment
source $(poetry env info --path)/bin/activate  # Activate it
python --version  # Now you're in the Poetry environment

# 4. (Optional) Install pre-commit hooks
poetry run make install-hooks  # If using Method A
# OR
make install-hooks  # If using Method B (environment activated)

# 5. Verify installation
poetry run make verify  # If using Method A
# OR
make verify  # If using Method B (environment activated)

# 6. Run a quick test
poetry run make run  # If using Method A
# OR
make run  # If using Method B (environment activated)
```

### Conda + Poetry Workflow (If you must use Conda)

```bash
# 1. Create and activate Conda environment
conda create -n mining_analytics python=3.10
conda activate mining_analytics

# 2. Tell Poetry to use the current environment
poetry config virtualenvs.create false

# 3. Install dependencies (including dev dependencies)
poetry install --with dev

# 4. (Optional) Install pre-commit hooks
make install-hooks

# 5. Verify installation
make verify

# 6. Run a quick test
make run
```

> **Important Notes:**
>
> - **Do NOT mix environments**: Don't activate Conda and use Poetry's own venv at the same time. Pick one workflow.
> - **If you use Conda**: Always run `poetry config virtualenvs.create false` **before** `poetry install`.
> - **Poetry-only workflow**: Choose either Method A (`poetry run`) or Method B (activate Poetry env directly), not both.
> - **Environment duplication**: Poetry creates its own virtual environment by default. Don't create additional conda environments unless you specifically need them.

---

## Environment Setup: Poetry vs Conda

### Poetry-Only (Recommended)

- Poetry manages its own virtual environment.
- No need to use Conda for Python version management.
- All dependencies are isolated in `.cache/pypoetry/virtualenvs/...`.
- **Method A**: Use `poetry run <command>` to run commands in the Poetry environment.
- **Method B**: Activate the Poetry environment directly with `source $(poetry env info --path)/bin/activate`.
- Use `poetry env info` to see environment information.

### Conda + Poetry

- Use Conda to manage Python version and system-level dependencies.
- Tell Poetry to use the active Conda environment with `poetry config virtualenvs.create false`.
- All dependencies are installed into the Conda environment.
- No separate Poetry venv is created.

---

## Installation & Setup

Follow the steps in your chosen workflow above. For reference, here are the details:

### Step 1: Clone the Project

```bash
git clone <repository-url>
cd web-content-extractor
```

### Step 2: Install Poetry (if not already installed)

```bash
pip install poetry
```

### Step 3: Install Dependencies

- **Poetry-only:**
  ```bash
  poetry install --with dev
  ```
- **Conda+Poetry:**
  ```bash
  poetry config virtualenvs.create false
  poetry install --with dev
  ```

### Step 4: Verify Environment

- **Poetry-only (Method A):**
  ```bash
  poetry run python --version
  ```
- **Poetry-only (Method B):**
  ```bash
  poetry env info --path
  source $(poetry env info --path)/bin/activate
  python --version
  ```
- **Conda+Poetry:**
  ```bash
  python --version
  ```

### Step 5: Install Pre-commit Hooks (Optional)

- **Poetry-only:**
  ```bash
  poetry run make install-hooks
  ```
- **Conda+Poetry:**
  ```bash
  make install-hooks
  ```

### Step 6: Verify Installation

- **Poetry-only:**
  ```bash
  poetry run make verify
  ```
- **Conda+Poetry:**
  ```bash
  make verify
  ```

### Step 7: Run a Quick Test

- **Poetry-only:**
  ```bash
  poetry run make run
  ```
- **Conda+Poetry:**
  ```bash
  make run
  ```

---

## Prerequisites

- **Python 3.10+**
- **Poetry** (dependency management)
- **Git** (version control)
- **Conda** (optional, for environment management)
- **Docker** (optional, for containerized deployment)
- **Azure CLI** (optional, for Azure Functions deployment)
- **Azure Functions Core Tools** (optional, for local Azure Functions development)

---

## Basic Usage

### Command Line Interface

#### Single URL Extraction

```bash
# Basic extraction
web-extractor extract https://example.com

# Save results to file
web-extractor extract https://example.com --output results.json --save

# Use different output format
web-extractor extract https://example.com --format markdown --output results.md

# Verbose output for debugging
web-extractor extract https://example.com --verbose
```

#### Batch Processing

```bash
# Process multiple URLs
web-extractor batch https://example1.com https://example2.com https://example3.com

# Save batch results to directory
web-extractor batch https://example1.com https://example2.com \
    --output-dir ./batch_results \
    --format json
```

#### Available Output Formats

- **JSON** (`--format json`): Structured data format
- **Text** (`--format text`): Human-readable text
- **Markdown** (`--format markdown`): Markdown format
- **CSV** (`--format csv`): Comma-separated values

### Example Output

#### JSON Format

```json
{
  "source_url": "https://example.com",
  "total_links": 15,
  "pdf_links": [
    {
      "url": "https://example.com/document.pdf",
      "text": "Download PDF",
      "link_type": "PDF"
    }
  ],
  "youtube_links": [
    {
      "url": "https://www.youtube.com/watch?v=abc123",
      "text": "Watch Video",
      "link_type": "YOUTUBE"
    }
  ],
  "other_links": [...],
  "metadata": {
    "processing_time_seconds": 2.34,
    "correlation_id": "ext_123456789"
  }
}
```

#### Text Format

```
Web Content Extraction Results
==============================

Source URL: https://example.com
Total Links Found: 15
Processing Time: 2.34 seconds

PDF Links (2):
- https://example.com/document.pdf (Download PDF)
- https://example.com/report.pdf (Annual Report)

YouTube Links (1):
- https://www.youtube.com/watch?v=abc123 (Watch Video)

Other Links (12):
- https://example.com/about (About Us)
- https://example.com/contact (Contact)
...
```

## Advanced Usage

### Custom Configuration

Create a `.env` file in the project root:

```bash
# HTTP Settings
WEB_EXTRACTOR_HTTP_TIMEOUT=60.0
WEB_EXTRACTOR_MAX_RETRIES=5
WEB_EXTRACTOR_USER_AGENT="MyBot/1.0"

# Logging
WEB_EXTRACTOR_LOG_LEVEL=DEBUG
WEB_EXTRACTOR_JSON_LOGS=true

# Storage
WEB_EXTRACTOR_OUTPUT_DIRECTORY=./my_output

# Azure Storage (optional)
WEB_EXTRACTOR_AZURE_STORAGE_CONNECTION_STRING=your_connection_string
WEB_EXTRACTOR_AZURE_STORAGE_CONTAINER=extraction-results
```

### Error Handling

The application provides detailed error information:

```bash
# Verbose error output
web-extractor extract https://invalid-url.com --verbose

# Error output includes:
# - Correlation ID for tracking
# - Elapsed processing time
# - Detailed error context
```

### Logging

```bash
# Enable JSON logging
export WEB_EXTRACTOR_JSON_LOGS=true

# Set log level
export WEB_EXTRACTOR_LOG_LEVEL=DEBUG

# Run with logging
web-extractor extract https://example.com
```

## API Usage

### Start API Server

```bash
# Start development server
web-extractor serve

# Start with custom host/port
web-extractor serve --host 0.0.0.0 --port 8080

# Start with auto-reload (development)
web-extractor serve --reload
```

### API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 123.45
}
```

#### Extract Content

```bash
curl -X POST "http://localhost:8000/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com",
       "save_result": true
     }'
```

Response:

```json
{
  "source_url": "https://example.com",
  "total_links": 15,
  "pdf_count": 2,
  "youtube_count": 1,
  "other_count": 12,
  "processing_time_seconds": 2.34,
  "links": {
    "pdf": [...],
    "youtube": [...],
    "other": [...]
  }
}
```

### API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Docker Deployment

### Local Development with Docker

```bash
# Start with Docker Compose (includes Azurite for local Azure Storage)
cd docker
docker-compose up --build

# Access the API
curl http://localhost:8000/health

# Stop the services
docker-compose down
```

### Production Docker Build

```bash
# Build the image
docker build -f docker/Dockerfile -t web-extractor .

# Run the container
docker run -p 8000:8000 web-extractor

# Run with custom configuration
docker run -p 8000:8000 \
  -e WEB_EXTRACTOR_LOG_LEVEL=INFO \
  -e WEB_EXTRACTOR_OUTPUT_DIRECTORY=/app/output \
  -v $(pwd)/output:/app/output \
  web-extractor
```

### Docker Compose Configuration

The `docker/docker-compose.yml` includes:

- Web Content Extractor API
- Azurite (local Azure Storage emulator)
- Volume mounts for persistent storage

## Azure Functions Deployment

### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Login to Azure
az login
```

### Deploy to Azure Functions

```bash
# Install Azure dependencies
poetry install --with azure

# Create Azure Function App (if not exists)
az functionapp create \
  --name your-function-app-name \
  --storage-account your-storage-account \
  --consumption-plan-location eastus \
  --resource-group your-resource-group \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4

# Deploy to Azure Functions
cd azure-functions
func azure functionapp publish your-function-app-name
```

### Function Triggers

#### HTTP Trigger

```bash
# Trigger via HTTP POST
curl -X POST "https://your-function-app.azurewebsites.net/api/extract" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

#### Blob Trigger

```bash
# Upload JSON file to trigger blob processing
az storage blob upload \
  --account-name your-storage-account \
  --container-name input \
  --name urls.json \
  --file urls.json \
  --auth-mode login
```

## Configuration

### Environment Variables

| Variable                                        | Default              | Description                                 |
| ----------------------------------------------- | -------------------- | ------------------------------------------- |
| `WEB_EXTRACTOR_HTTP_TIMEOUT`                    | `30.0`               | HTTP request timeout in seconds             |
| `WEB_EXTRACTOR_MAX_RETRIES`                     | `3`                  | Maximum HTTP retry attempts                 |
| `WEB_EXTRACTOR_USER_AGENT`                      | `WebExtractor/1.0`   | User agent string                           |
| `WEB_EXTRACTOR_LOG_LEVEL`                       | `INFO`               | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `WEB_EXTRACTOR_JSON_LOGS`                       | `false`              | Enable JSON structured logging              |
| `WEB_EXTRACTOR_OUTPUT_DIRECTORY`                | `./output`           | Local output directory                      |
| `WEB_EXTRACTOR_AZURE_STORAGE_CONNECTION_STRING` | -                    | Azure Storage connection string             |
| `WEB_EXTRACTOR_AZURE_STORAGE_CONTAINER`         | `extraction-results` | Azure Storage container name                |

### Configuration File

Create `config.yaml` in the project root:

```yaml
http:
  timeout: 30.0
  max_retries: 3
  user_agent: "WebExtractor/1.0"

logging:
  level: INFO
  json_logs: false

storage:
  output_directory: ./output
  azure:
    connection_string: ${WEB_EXTRACTOR_AZURE_STORAGE_CONNECTION_STRING}
    container: extraction-results
```

## Troubleshooting

### Common Issues

#### 1. Poetry Installation Issues

```bash
# Clear Poetry cache
poetry cache clear --all pypi

# Reinstall dependencies
poetry install --no-cache

# If virtual environment is broken, recreate it
poetry env remove python
poetry install --with dev
```

#### 2. Pre-commit Installation Issues

```bash
# If pre-commit command not found after setup
make install-hooks

# Or manually install pre-commit
poetry install --with dev
poetry run pre-commit install

# If virtual environment was recreated
poetry run pip install pre-commit
poetry run pre-commit install
```

#### 2. HTTP Connection Errors

```bash
# Check network connectivity
curl -I https://example.com

# Increase timeout
export WEB_EXTRACTOR_HTTP_TIMEOUT=60.0

# Check user agent
export WEB_EXTRACTOR_USER_AGENT="Mozilla/5.0 (compatible; WebExtractor/1.0)"
```

#### 3. Permission Errors

```bash
# Fix output directory permissions
mkdir -p output
chmod 755 output

# For Docker, ensure volume permissions
docker run -v $(pwd)/output:/app/output:rw web-extractor
```

#### 4. Azure Functions Issues

```bash
# Check Azure Functions logs
func azure functionapp logstream your-function-app-name

# Verify function configuration
func azure functionapp list-functions your-function-app-name
```

### Debug Mode

```bash
# Enable debug logging
export WEB_EXTRACTOR_LOG_LEVEL=DEBUG

# Run with verbose output
web-extractor extract https://example.com --verbose

# Check logs
tail -f logs/app.log
```

### Performance Optimization

```bash
# Increase HTTP timeout for slow sites
export WEB_EXTRACTOR_HTTP_TIMEOUT=60.0

# Reduce retries for faster failure
export WEB_EXTRACTOR_MAX_RETRIES=1

# Use JSON logging for better performance
export WEB_EXTRACTOR_JSON_LOGS=true
```

## Development Workflow

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Run tests
make test

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# Check coverage
pytest --cov=src --cov-report=html
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files

# Or use the make command
poetry run make install-hooks
```

### Development Server

```bash
# Start development server with auto-reload
make dev

# Or manually
web-extractor serve --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test markers
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "slow"           # Slow tests only

# Run tests in parallel
pytest -n auto
```

### Continuous Integration

The project includes GitHub Actions workflows for:

- Code quality checks (formatting, linting)
- Unit and integration tests
- Docker image building
- Azure Functions deployment

## Support

### Getting Help

1. **Run the fix script**: Use `make fix` or `python scripts/fix_setup.py` to resolve common setup issues
2. **Check the logs**: Look for error messages in the application logs
3. **Review documentation**: Check the `docs/` directory for detailed guides
4. **Run tests**: Ensure all tests pass with `make test`
5. **Check configuration**: Verify environment variables and settings
6. **Create an issue**: Report bugs or request features on GitHub

### Useful Commands Reference

```bash
# Project management
make setup          # Install dependencies
make verify         # Verify setup
make fix            # Fix common setup issues
make install-hooks  # Install pre-commit hooks
make test           # Run tests
make format         # Format code
make lint           # Lint code
make clean          # Clean generated files

# CLI usage
web-extractor extract <url>           # Extract from URL
web-extractor batch <urls>            # Batch processing
web-extractor serve                   # Start API server
web-extractor --help                  # Show help

# Docker
docker-compose up --build             # Start with Docker
docker build -f docker/Dockerfile .   # Build image

# Azure Functions
func azure functionapp publish <name> # Deploy to Azure
func start                           # Start locally
```

---

**Note**: This execution guide covers the most common use cases. For advanced scenarios or specific requirements, refer to the individual component documentation in the `docs/` directory.
