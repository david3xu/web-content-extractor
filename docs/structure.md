# Web Content Extractor - Professional Python Project Structure

## Project Structure

```
web-content-extractor/
├── src/
│   ├── __init__.py
│   ├── main.py                     # Entry point
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── web_content_extractor.py    # Main orchestrator
│   │   ├── content_scraper.py          # Web scraping service
│   │   ├── link_classifier.py          # Link categorization
│   │   └── output_formatter.py         # Result formatting
│   ├── models/
│   │   ├── __init__.py
│   │   ├── extraction_models.py        # Data classes
│   │   └── exceptions.py               # Custom exceptions
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── http_client.py              # HTTP utilities
│   │   ├── validators.py               # Validation helpers
│   │   └── logger.py                   # Logging configuration
│   └── config/
│       ├── __init__.py
│       ├── settings.py                 # Configuration management
│       └── config.yaml                 # Application settings
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_content_scraper.py
│   │   ├── test_link_classifier.py
│   │   └── test_output_formatter.py
│   ├── integration/
│   │   └── test_web_extractor.py
│   └── fixtures/
│       └── sample_data.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── azure/
│   ├── function_app.py                 # Azure Functions entry
│   ├── requirements.txt                # Azure-specific deps
│   └── host.json                       # Function configuration
├── scripts/
│   ├── setup.sh                        # Environment setup
│   └── deploy.sh                       # Deployment script
├── output/                             # Default output directory
├── .env.example                        # Environment template
├── .gitignore
├── README.md
├── pyproject.toml                      # Modern Python packaging
└── requirements.txt                    # Dependencies
```

## Deployment Architecture

### **Shared Core + Dual Entry Points**

```
Shared Business Logic (src/extractors/, src/models/, src/utils/)
    ↓
Local CLI Entry Point (src/main.py) ←→ Azure Functions Entry Point (azure/function_app.py)
```

### **Local Development → Azure Production Pipeline**

1. **Develop Locally**: CLI interface for rapid development and testing
2. **Share Core Logic**: Same extraction services for both environments
3. **Deploy to Azure**: Functions wrapper around existing business logic
4. **Unified Testing**: Test core logic once, works in both environments

## Core Implementation

### 1. Data Models (src/models/extraction_models.py)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class LinkType(Enum):
    PDF = "pdf"
    YOUTUBE = "youtube"
    OTHER = "other"


@dataclass
class ExtractedLink:
    url: str
    link_text: str
    link_type: LinkType
    is_valid: bool = True
    context: Optional[str] = None


@dataclass
class ExtractionMetadata:
    total_links_found: int
    pdf_count: int
    youtube_count: int
    processing_time_seconds: float
    page_title: Optional[str] = None
    extraction_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LinkCategorizationResult:
    source_url: str
    pdf_links: List[ExtractedLink] = field(default_factory=list)
    youtube_links: List[ExtractedLink] = field(default_factory=list)
    other_links: List[ExtractedLink] = field(default_factory=list)
    metadata: Optional[ExtractionMetadata] = None

    def get_all_links(self) -> List[ExtractedLink]:
        return self.pdf_links + self.youtube_links + self.other_links
```

### 2. Custom Exceptions (src/models/exceptions.py)

```python
class WebExtractionError(Exception):
    """Base exception for web extraction operations"""
    pass


class ContentScrapingError(WebExtractionError):
    """Exception raised during web content scraping"""
    pass


class LinkClassificationError(WebExtractionError):
    """Exception raised during link classification"""
    pass


class OutputFormattingError(WebExtractionError):
    """Exception raised during output formatting"""
    pass


class ConfigurationError(WebExtractionError):
    """Exception raised for configuration issues"""
    pass
```

### 3. Configuration Management (src/config/settings.py)

```python
from pathlib import Path
import yaml
from typing import Dict, Any


class Settings:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    @property
    def extraction_settings(self) -> Dict[str, Any]:
        return self.config.get('extraction', {})

    @property
    def output_settings(self) -> Dict[str, Any]:
        return self.config.get('output', {})

    @property
    def request_timeout(self) -> int:
        return self.extraction_settings.get('request_timeout', 30)

    @property
    def max_retry_attempts(self) -> int:
        return self.extraction_settings.get('max_retry_attempts', 3)

    @property
    def user_agent(self) -> str:
        return self.extraction_settings.get('user_agent', 'WebContentExtractor/1.0')

    @property
    def output_format(self) -> str:
        return self.output_settings.get('default_format', 'json')

    @property
    def output_directory(self) -> str:
        return self.output_settings.get('output_directory', './output')
```

### 4. HTTP Client Utility (src/utils/http_client.py)

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from ..models.exceptions import ContentScrapingError


class HttpClient:
    def __init__(self, timeout: int = 30, max_retries: int = 3, user_agent: str = None):
        self.session = requests.Session()
        self.timeout = timeout

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})

    def get_content(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise ContentScrapingError(f"Failed to fetch content from {url}: {str(e)}")

    def close(self):
        self.session.close()
```

### 5. Content Scraper (src/extractors/content_scraper.py)

```python
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from ..utils.http_client import HttpClient
from ..models.exceptions import ContentScrapingError


class ContentScrapingService:
    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def extract_web_content(self, url: str) -> Tuple[BeautifulSoup, str]:
        """Extract and parse web content"""
        try:
            content = self.http_client.get_content(url)
            soup = BeautifulSoup(content, 'html.parser')
            return soup, content
        except Exception as e:
            raise ContentScrapingError(f"Failed to extract content: {str(e)}")

    def extract_all_links(self, soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
        """Extract all links with their text content"""
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            if self._is_valid_url(absolute_url):
                links.append((absolute_url, text))

        return links

    def get_page_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else None

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
```

### 6. Link Classifier (src/extractors/link_classifier.py)

```python
import re
from typing import List, Tuple
from ..models.extraction_models import ExtractedLink, LinkType
from ..models.exceptions import LinkClassificationError


class LinkClassifierService:
    def __init__(self):
        self.pdf_pattern = re.compile(r'\.pdf$', re.IGNORECASE)
        self.youtube_patterns = [
            re.compile(r'youtube\.com/watch\?v=', re.IGNORECASE),
            re.compile(r'youtu\.be/', re.IGNORECASE),
            re.compile(r'youtube\.com/embed/', re.IGNORECASE)
        ]

    def classify_links(self, links: List[Tuple[str, str]]) -> List[ExtractedLink]:
        """Classify links into categories"""
        try:
            classified_links = []

            for url, text in links:
                link_type = self._determine_link_type(url)
                extracted_link = ExtractedLink(
                    url=url,
                    link_text=text,
                    link_type=link_type,
                    is_valid=True  # Could add validation here
                )
                classified_links.append(extracted_link)

            return classified_links
        except Exception as e:
            raise LinkClassificationError(f"Failed to classify links: {str(e)}")

    def _determine_link_type(self, url: str) -> LinkType:
        """Determine the type of link"""
        if self.pdf_pattern.search(url):
            return LinkType.PDF

        for pattern in self.youtube_patterns:
            if pattern.search(url):
                return LinkType.YOUTUBE

        return LinkType.OTHER

    def categorize_by_type(self, links: List[ExtractedLink]) -> Tuple[List[ExtractedLink], List[ExtractedLink], List[ExtractedLink]]:
        """Separate links by type"""
        pdf_links = [link for link in links if link.link_type == LinkType.PDF]
        youtube_links = [link for link in links if link.link_type == LinkType.YOUTUBE]
        other_links = [link for link in links if link.link_type == LinkType.OTHER]

        return pdf_links, youtube_links, other_links
```

### 7. Output Formatter (src/extractors/output_formatter.py)

```python
import json
from pathlib import Path
from typing import Dict, Any
from ..models.extraction_models import LinkCategorizationResult, ExtractedLink
from ..models.exceptions import OutputFormattingError


class OutputFormatterService:
    def __init__(self, output_directory: str = "./output"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)

    def generate_json_report(self, result: LinkCategorizationResult) -> str:
        """Generate JSON formatted report"""
        try:
            report_data = {
                "source_url": result.source_url,
                "extraction_timestamp": result.metadata.extraction_timestamp.isoformat() if result.metadata else None,
                "summary": {
                    "total_links": len(result.get_all_links()),
                    "pdf_count": len(result.pdf_links),
                    "youtube_count": len(result.youtube_links),
                    "other_count": len(result.other_links)
                },
                "pdf_links": [self._link_to_dict(link) for link in result.pdf_links],
                "youtube_links": [self._link_to_dict(link) for link in result.youtube_links],
                "other_links": [self._link_to_dict(link) for link in result.other_links],
                "metadata": self._metadata_to_dict(result.metadata) if result.metadata else None
            }

            return json.dumps(report_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OutputFormattingError(f"Failed to generate JSON report: {str(e)}")

    def generate_console_output(self, result: LinkCategorizationResult) -> str:
        """Generate human-readable console output"""
        output_lines = [
            f"Web Content Extraction Results",
            f"Source URL: {result.source_url}",
            f"",
            f"Summary:",
            f"  Total Links Found: {len(result.get_all_links())}",
            f"  PDF Links: {len(result.pdf_links)}",
            f"  YouTube Links: {len(result.youtube_links)}",
            f"  Other Links: {len(result.other_links)}",
            f""
        ]

        if result.pdf_links:
            output_lines.extend([
                "PDF Links:",
                *[f"  • {link.link_text}: {link.url}" for link in result.pdf_links],
                ""
            ])

        if result.youtube_links:
            output_lines.extend([
                "YouTube Links:",
                *[f"  • {link.link_text}: {link.url}" for link in result.youtube_links],
                ""
            ])

        return "\n".join(output_lines)

    def export_to_file(self, content: str, filename: str, format_type: str = "json"):
        """Export content to file"""
        try:
            file_path = self.output_directory / f"{filename}.{format_type}"
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return str(file_path)
        except Exception as e:
            raise OutputFormattingError(f"Failed to export to file: {str(e)}")

    def _link_to_dict(self, link: ExtractedLink) -> Dict[str, Any]:
        return {
            "url": link.url,
            "text": link.link_text,
            "type": link.link_type.value,
            "is_valid": link.is_valid
        }

    def _metadata_to_dict(self, metadata) -> Dict[str, Any]:
        return {
            "total_links_found": metadata.total_links_found,
            "pdf_count": metadata.pdf_count,
            "youtube_count": metadata.youtube_count,
            "processing_time_seconds": metadata.processing_time_seconds,
            "page_title": metadata.page_title,
            "extraction_timestamp": metadata.extraction_timestamp.isoformat()
        }
```

### 8. Main Orchestrator (src/extractors/web_content_extractor.py)

```python
import time
from typing import Optional
from ..utils.http_client import HttpClient
from ..models.extraction_models import LinkCategorizationResult, ExtractionMetadata
from .content_scraper import ContentScrapingService
from .link_classifier import LinkClassifierService
from .output_formatter import OutputFormatterService


class WebContentExtractor:
    def __init__(self,
                 timeout: int = 30,
                 max_retries: int = 3,
                 user_agent: str = None,
                 output_directory: str = "./output"):

        self.http_client = HttpClient(timeout, max_retries, user_agent)
        self.content_scraper = ContentScrapingService(self.http_client)
        self.link_classifier = LinkClassifierService()
        self.output_formatter = OutputFormatterService(output_directory)

    def extract_and_categorize(self, url: str) -> LinkCategorizationResult:
        """Main extraction and categorization workflow"""
        start_time = time.time()

        # Extract web content
        soup, raw_content = self.content_scraper.extract_web_content(url)
        page_title = self.content_scraper.get_page_title(soup)

        # Extract all links
        raw_links = self.content_scraper.extract_all_links(soup, url)

        # Classify links
        classified_links = self.link_classifier.classify_links(raw_links)
        pdf_links, youtube_links, other_links = self.link_classifier.categorize_by_type(classified_links)

        # Create metadata
        processing_time = time.time() - start_time
        metadata = ExtractionMetadata(
            total_links_found=len(classified_links),
            pdf_count=len(pdf_links),
            youtube_count=len(youtube_links),
            processing_time_seconds=processing_time,
            page_title=page_title
        )

        # Create result
        result = LinkCategorizationResult(
            source_url=url,
            pdf_links=pdf_links,
            youtube_links=youtube_links,
            other_links=other_links,
            metadata=metadata
        )

        return result

    def extract_and_export(self, url: str, output_format: str = "json",
                          export_to_file: bool = True) -> str:
        """Extract, categorize, and export results"""
        result = self.extract_and_categorize(url)

        if output_format.lower() == "json":
            formatted_output = self.output_formatter.generate_json_report(result)
        else:
            formatted_output = self.output_formatter.generate_console_output(result)

        if export_to_file:
            timestamp = int(time.time())
            filename = f"extraction_results_{timestamp}"
            file_path = self.output_formatter.export_to_file(
                formatted_output, filename, output_format
            )
            return file_path

        return formatted_output

    def close(self):
        """Clean up resources"""
        self.http_client.close()
```

### 9. Entry Point (src/main.py)

```python
#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from .config.settings import Settings
from .extractors.web_content_extractor import WebContentExtractor
from .models.exceptions import WebExtractionError


def main():
    parser = argparse.ArgumentParser(description='Extract and categorize web content links')
    parser.add_argument('url', help='URL to extract content from')
    parser.add_argument('--format', choices=['json', 'console'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--output-file', action='store_true',
                       help='Save output to file')
    parser.add_argument('--config', help='Configuration file path')

    args = parser.parse_args()

    try:
        # Load configuration
        settings = Settings(args.config) if args.config else Settings()

        # Initialize extractor
        extractor = WebContentExtractor(
            timeout=settings.request_timeout,
            max_retries=settings.max_retry_attempts,
            user_agent=settings.user_agent,
            output_directory=settings.output_directory
        )

        # Extract and process
        if args.output_file:
            file_path = extractor.extract_and_export(
                args.url,
                output_format=args.format,
                export_to_file=True
            )
            print(f"Results exported to: {file_path}")
        else:
            output = extractor.extract_and_export(
                args.url,
                output_format=args.format,
                export_to_file=False
            )
            print(output)

        extractor.close()

    except WebExtractionError as e:
        print(f"Extraction error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Configuration Files

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "web-content-extractor"
version = "1.0.0"
description = "Professional web content extraction and link categorization"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
dependencies = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "pyyaml>=6.0",
    "urllib3>=2.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0"
]
azure = [
    "azure-functions>=1.18.0",
    "azure-storage-blob>=12.19.0"
]

[project.scripts]
web-extractor = "src.main:main"
```

### config.yaml

```yaml
extraction:
  request_timeout: 30
  max_retry_attempts: 3
  user_agent: "WebContentExtractor/1.0"
  enable_link_validation: true

output:
  default_format: "json"
  output_directory: "./output"
  include_metadata: true
  timestamp_files: true
```

## Development Workflow

### 1. Quick Start

```bash
# Clone and setup
git clone <repository>
cd web-content-extractor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Run extraction
python -m src.main https://tutorial.nlp-tlp.org/ai-engineer-bootcamp --format json --output-file
```

### 2. Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Testing
pytest tests/ --cov=src
```

### 3. Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test
pytest tests/unit/test_link_classifier.py -v
```

### 10. Azure Functions Entry Point (azure/function_app.py)

```python
import json
import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from typing import Optional
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.extractors.web_content_extractor import WebContentExtractor
from src.models.exceptions import WebExtractionError
from src.config.settings import Settings


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="extract", methods=["POST"])
def extract_web_content(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function endpoint for web content extraction"""
    logging.info('Web content extraction function triggered')

    try:
        # Parse request
        req_body = req.get_json()
        if not req_body or 'url' not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'url' in request body"}),
                status_code=400,
                mimetype="application/json"
            )

        url = req_body['url']
        output_format = req_body.get('format', 'json')
        save_to_blob = req_body.get('save_to_blob', False)

        # Load settings
        settings = Settings()

        # Initialize extractor
        extractor = WebContentExtractor(
            timeout=settings.request_timeout,
            max_retries=settings.max_retry_attempts,
            user_agent=settings.user_agent
        )

        # Perform extraction
        result = extractor.extract_and_categorize(url)

        # Format output
        if output_format.lower() == 'json':
            formatted_output = extractor.output_formatter.generate_json_report(result)
        else:
            formatted_output = extractor.output_formatter.generate_console_output(result)

        # Optionally save to Azure Blob Storage
        blob_url = None
        if save_to_blob:
            blob_url = _save_to_blob_storage(formatted_output, result.source_url, output_format)

        # Clean up
        extractor.close()

        # Response
        response_data = {
            "status": "success",
            "result": json.loads(formatted_output) if output_format == 'json' else formatted_output,
            "blob_url": blob_url
        }

        return func.HttpResponse(
            json.dumps(response_data, ensure_ascii=False),
            status_code=200,
            mimetype="application/json"
        )

    except WebExtractionError as e:
        logging.error(f"Extraction error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Extraction failed: {str(e)}"}),
            status_code=422,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "web-content-extractor"}),
        status_code=200,
        mimetype="application/json"
    )


def _save_to_blob_storage(content: str, source_url: str, format_type: str) -> Optional[str]:
    """Save extraction results to Azure Blob Storage"""
    try:
        # Get connection string from environment
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logging.warning("No Azure Storage connection string found")
            return None

        # Initialize blob service
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = "extraction-results"

        # Generate blob name
        from urllib.parse import urlparse
        import time
        domain = urlparse(source_url).netloc.replace('.', '-')
        timestamp = int(time.time())
        blob_name = f"{domain}/extraction_{timestamp}.{format_type}"

        # Upload to blob
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        blob_client.upload_blob(content, overwrite=True)

        # Return blob URL
        return blob_client.url

    except Exception as e:
        logging.error(f"Failed to save to blob storage: {str(e)}")
        return None
```

### 11. Azure Functions Configuration (azure/host.json)

```json
{
  "version": "2.0",
  "functionTimeout": "00:05:00",
  "extensions": {
    "http": {
      "routePrefix": "api"
    }
  },
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true
      }
    }
  }
}
```

### 12. Azure Requirements (azure/requirements.txt)

```txt
azure-functions>=1.18.0
azure-storage-blob>=12.19.0
azure-identity>=1.15.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pyyaml>=6.0
urllib3>=2.0.0
```

### 13. Docker Configuration (docker/Dockerfile)

```dockerfile
# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create output directory
RUN mkdir -p output

# Set Python path
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "src.main", "--help"]
```

### 14. Docker Compose (docker/docker-compose.yml)

```yaml
version: "3.8"

services:
  web-extractor:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - OUTPUT_DIRECTORY=/app/output
    volumes:
      - ../output:/app/output
      - ../config:/app/config
    command: python -m src.main https://example.com --format json --output-file

  # Optional: Add Azure Storage Emulator for local testing
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    ports:
      - "10000:10000"
      - "10001:10001"
      - "10002:10002"
    environment:
      - AZURITE_ACCOUNTS=devstoreaccount1
```

### 15. Deployment Scripts (scripts/deploy.sh)

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Web Content Extractor..."

# Configuration
RESOURCE_GROUP="rg-web-extractor"
FUNCTION_APP_NAME="func-web-extractor-$(date +%s)"
STORAGE_ACCOUNT="stwextractor$(date +%s | tail -c 6)"
LOCATION="eastus"

# Create Resource Group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Storage Account
echo "💾 Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# Create Function App
echo "⚡ Creating function app..."
az functionapp create \
    --resource-group $RESOURCE_GROUP \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name $FUNCTION_APP_NAME \
    --storage-account $STORAGE_ACCOUNT

# Configure App Settings
echo "⚙️ Configuring app settings..."
CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString --output tsv)

az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings "AZURE_STORAGE_CONNECTION_STRING=$CONNECTION_STRING"

# Deploy Function Code
echo "📤 Deploying function code..."
cd azure
func azure functionapp publish $FUNCTION_APP_NAME --python

echo "✅ Deployment complete!"
echo "Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo "Test endpoint: https://$FUNCTION_APP_NAME.azurewebsites.net/api/extract"
```

## Dual Deployment Usage

### **Local Development**

```bash
# Quick extraction
python -m src.main https://tutorial.nlp-tlp.org/ai-engineer-bootcamp --format json

# Development with file output
python -m src.main https://example.com --format console --output-file

# Docker local testing
docker-compose -f docker/docker-compose.yml up
```

### **Azure Functions Production**

```bash
# Deploy to Azure
./scripts/deploy.sh

# Test via HTTP POST
curl -X POST https://your-function-app.azurewebsites.net/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tutorial.nlp-tlp.org/ai-engineer-bootcamp",
    "format": "json",
    "save_to_blob": true
  }'

# Health check
curl https://your-function-app.azurewebsites.net/api/health
```

### **Request/Response Examples**

#### Azure Function Request:

```json
{
  "url": "https://tutorial.nlp-tlp.org/ai-engineer-bootcamp",
  "format": "json",
  "save_to_blob": true
}
```

#### Azure Function Response:

```json
{
  "status": "success",
  "result": {
    "source_url": "https://tutorial.nlp-tlp.org/ai-engineer-bootcamp",
    "summary": {
      "total_links": 15,
      "pdf_count": 0,
      "youtube_count": 2,
      "other_count": 13
    },
    "youtube_links": [
      {
        "url": "https://youtube.com/watch?v=abc123",
        "text": "Tutorial Video",
        "type": "youtube"
      }
    ],
    "pdf_links": [],
    "other_links": [...]
  },
  "blob_url": "https://storage.blob.core.windows.net/extraction-results/..."
}
```

## Development Lifecycle

### **Phase 1: Local Development**

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Develop & Test
python -m src.main https://tutorial.nlp-tlp.org/ai-engineer-bootcamp
pytest tests/unit/ -v

# Code Quality
black src/ && flake8 src/ && mypy src/
```

### **Phase 2: Docker Testing**

```bash
# Build and test locally
docker-compose -f docker/docker-compose.yml up
docker exec -it container_name python -m src.main https://example.com
```

### **Phase 3: Azure Deployment**

```bash
# Deploy to Azure
./scripts/deploy.sh

# Monitor
az functionapp logs tail --name func-web-extractor --resource-group rg-web-extractor
```

This professional structure provides:

- **Single Codebase**: Shared business logic between local CLI and Azure Functions
- **Clean Architecture**: Separated concerns with clear service boundaries
- **Type Safety**: Full type hints and mypy compatibility
- **Error Handling**: Comprehensive exception hierarchy
- **Testing Ready**: Structured test organization for both deployment targets
- **CI/CD Ready**: Docker and Azure deployment automation
- **Production Ready**: Blob storage integration, health checks, monitoring
- **Scalable**: Easy to add new features that work in both environments
