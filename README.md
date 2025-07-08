# Web Content Extractor

A professional Python tool for extracting, categorizing, and analyzing links from web pages.

## Features

- **Content Extraction**: Fetches content from any web page with proper error handling
- **Link Classification**: Automatically identifies and categorizes PDF documents, YouTube videos, and other links
- **Multiple Output Formats**: Generate JSON or console-friendly reports
- **Extensible Architecture**: Easily add new link types or output formats
- **Production Ready**: Complete with logging, robust error handling, and resource management
- **Cloud Ready**: Includes Azure Functions integration for serverless deployment

## Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/web-content-extractor.git
cd web-content-extractor

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate the virtual environment
source venv/bin/activate
```

### Docker

```bash
# Build and run using Docker Compose
cd web-content-extractor
docker-compose -f docker/docker-compose.yml up --build
```

## Usage

### Command Line

```bash
# Basic usage
web-extractor https://example.com

# Specify output format
web-extractor https://example.com --format json

# Save output to file
web-extractor https://example.com --output-file

# Using custom configuration
web-extractor https://example.com --config path/to/config.yaml
```

### Python API

```python
from src.extractors.web_content_extractor import WebContentExtractor

# Initialize extractor
extractor = WebContentExtractor()

# Extract and process
result = extractor.extract_and_categorize("https://example.com")

# Print results
print(f"Found {len(result.pdf_links)} PDF links")
print(f"Found {len(result.youtube_links)} YouTube links")

# Clean up
extractor.close()
```

### Azure Function

Once deployed, you can use the HTTP trigger:

```
GET https://your-function-app.azurewebsites.net/api/extract?url=https://example.com
```

Or using POST:

```json
{
  "url": "https://example.com",
  "format": "json"
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src tests/

# Run specific test files
pytest tests/unit/test_link_classifier.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Deployment

### Azure Functions

```bash
# Deploy to Azure Functions
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
