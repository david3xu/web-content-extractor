# Web Content Extractor: Professional Improvement Guide

## **Overview: Simple Start, Professional Quality**

This guide transforms the existing web content extractor into a production-ready application while maintaining simplicity. We focus on **code-first improvements** that provide immediate professional benefits with minimal complexity.

### **Core Philosophy**
- **Simple Enough**: New developers can understand the codebase in 30 minutes
- **Professional Enough**: Ready for production deployment and team collaboration
- **Code Priority**: Architecture emerges from clean, well-structured code

---

## **Phase 1: Quick Start Foundation (1 Hour)**

### **Problem: Complex Setup Process**

**Current State:**
```bash
# Multiple manual steps, easy to get wrong
git clone repository
python -m venv venv
source venv/bin/activate  # Different on Windows
pip install -r requirements.txt
mkdir output
python -m src.main https://example.com --format json
```

**Issues:**
- Platform-specific virtual environment commands
- Manual directory creation
- No development workflow automation
- No dependency version management

### **Solution: Modern Python Tooling**

**1. Poetry for Dependency Management**

```toml
# pyproject.toml - Single source of truth
[tool.poetry]
name = "web-content-extractor"
version = "0.1.0"
description = "Professional web content extraction and link categorization"
authors = ["Your Team <team@company.com>"]
readme = "README.md"
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.10"
httpx = "^0.25.0"           # Modern async HTTP client
beautifulsoup4 = "^4.12.0"  # HTML parsing
pydantic = "^2.4.0"         # Settings and validation
structlog = "^23.1.0"       # Structured logging
typer = {extras = ["all"], version = "^0.9.0"}  # Modern CLI framework

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.9.0"
ruff = "^0.0.290"
mypy = "^1.5.0"
pre-commit = "^3.4.0"

[tool.poetry.scripts]
web-extractor = "src.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Why Poetry?**
- **Deterministic builds**: `poetry.lock` ensures identical dependencies across environments
- **Virtual environment automation**: No manual venv management
- **Script integration**: Direct command execution
- **Professional standard**: Used by most modern Python projects

**2. Makefile for Development Workflow**

```makefile
# Makefile - Cross-platform development commands
.DEFAULT_GOAL := help
.PHONY: help setup test run docker clean lint format

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and setup development environment
	@echo "🚀 Setting up development environment..."
	poetry install
	poetry run pre-commit install
	mkdir -p output logs
	@echo "✅ Setup complete! Run 'make run' to test extraction"

test: ## Run test suite with coverage
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

run: ## Run extraction example
	@echo "🔍 Running extraction example..."
	poetry run python -c "import asyncio; from src.cli import demo; asyncio.run(demo())"

lint: ## Check code quality
	@echo "🔍 Checking code quality..."
	poetry run ruff check src/ tests/
	poetry run mypy src/

format: ## Format code
	@echo "✨ Formatting code..."
	poetry run black src/ tests/
	poetry run ruff --fix src/ tests/

docker: ## Build and run with Docker
	@echo "🐳 Building Docker container..."
	docker-compose up --build

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf output/* logs/* .coverage htmlcov/ .mypy_cache/ .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev: ## Start development server
	@echo "🚀 Starting development server..."
	poetry run python -m src.cli serve --reload
```

**Why Makefile?**
- **Cross-platform**: Works on Windows, macOS, Linux
- **Self-documenting**: `make help` shows available commands
- **Team consistency**: Everyone uses the same commands
- **CI/CD integration**: Same commands work in automation

**3. Simple Setup Experience**

```bash
# New developer experience - 3 commands total
git clone https://github.com/company/web-content-extractor.git
cd web-content-extractor
make setup
make run
```

**Result**: 5-minute setup instead of 20+ minutes with troubleshooting.

---

## **Phase 2: Professional Architecture (2 Hours)**

### **Problem: Monolithic Service Class**

**Current Issues:**
```python
# src/extractors/web_content_extractor.py - Doing too much
class WebContentExtractor:
    def __init__(self, timeout, max_retries, user_agent, output_directory):
        # Hard-coded dependencies - can't test or swap implementations
        self.http_client = HttpClient(timeout, max_retries, user_agent)
        self.content_scraper = ContentScrapingService(self.http_client)
        self.link_classifier = LinkClassifierService()
        self.output_formatter = OutputFormatterService(output_directory)

    def extract_and_categorize(self, url: str):
        # Orchestrates everything - violates Single Responsibility Principle
        # Synchronous - blocks on network calls
        # Hard to test individual components
```

**Problems:**
- **Tight coupling**: Can't test components in isolation
- **Hard to extend**: Adding new link types requires changing core class
- **Synchronous**: Blocks on every HTTP request
- **No dependency injection**: Can't swap implementations for testing

### **Solution: Clean Architecture with Protocols**

**1. Define Clear Interfaces**

```python
# src/core/interfaces.py - Contract definitions
from abc import ABC, abstractmethod
from typing import Protocol, List
from .models import ExtractionResult, ExtractedLink

class ContentExtractor(Protocol):
    """Protocol for extracting content from URLs"""
    async def extract_content(self, url: str) -> str:
        """Extract raw HTML content from URL"""
        ...

class LinkParser(Protocol):
    """Protocol for parsing links from content"""
    def parse_links(self, content: str, base_url: str) -> List[tuple[str, str]]:
        """Parse links from HTML content, return (url, text) tuples"""
        ...

class LinkClassifier(Protocol):
    """Protocol for classifying link types"""
    def classify_links(self, links: List[tuple[str, str]]) -> List[ExtractedLink]:
        """Classify links into categories (PDF, YouTube, other)"""
        ...

class ResultStorage(Protocol):
    """Protocol for storing extraction results"""
    async def save_result(self, result: ExtractionResult) -> str:
        """Save extraction result, return storage location"""
        ...
```

**Why Protocols?**
- **Duck typing**: Python's natural way to define interfaces
- **Testability**: Easy to create mock implementations
- **Flexibility**: Multiple implementations without inheritance
- **Type safety**: MyPy can check interface compliance

**2. Clean Domain Models**

```python
# src/core/models.py - Business objects with validation
from pydantic import BaseModel, HttpUrl, Field, validator
from enum import Enum
from typing import List, Optional
from datetime import datetime

class LinkType(str, Enum):
    """Enumeration of supported link types"""
    PDF = "pdf"
    YOUTUBE = "youtube"
    OTHER = "other"

class ExtractedLink(BaseModel):
    """A single extracted and classified link"""
    url: HttpUrl
    text: str = Field(..., min_length=1, description="Link text content")
    link_type: LinkType
    is_valid: bool = Field(default=True, description="Whether link is accessible")

    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Link text cannot be empty')
        return v.strip()

class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    page_title: Optional[str] = None
    total_links_found: int = Field(..., ge=0)
    processing_time_seconds: float = Field(..., gt=0)
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    user_agent: str = Field(default="WebExtractor/1.0")

class ExtractionResult(BaseModel):
    """Complete result of link extraction and classification"""
    source_url: HttpUrl
    pdf_links: List[ExtractedLink] = Field(default_factory=list)
    youtube_links: List[ExtractedLink] = Field(default_factory=list)
    other_links: List[ExtractedLink] = Field(default_factory=list)
    metadata: Optional[ExtractionMetadata] = None

    @property
    def total_links(self) -> int:
        """Total number of links across all categories"""
        return len(self.pdf_links) + len(self.youtube_links) + len(self.other_links)

    @property
    def summary(self) -> dict:
        """Summary statistics for quick overview"""
        return {
            "total_links": self.total_links,
            "pdf_count": len(self.pdf_links),
            "youtube_count": len(self.youtube_links),
            "other_count": len(self.other_links)
        }
```

**Why Pydantic?**
- **Automatic validation**: Catches errors early with clear messages
- **Type conversion**: Automatically converts strings to URLs, numbers, etc.
- **JSON serialization**: Built-in conversion to/from JSON
- **Documentation**: Models serve as API documentation

**3. Clean Service Layer**

```python
# src/core/service.py - Business logic orchestration
import time
import structlog
from typing import Optional

from .interfaces import ContentExtractor, LinkParser, LinkClassifier, ResultStorage
from .models import ExtractionResult, ExtractionMetadata

logger = structlog.get_logger()

class ExtractionService:
    """
    Core business logic for web content extraction.

    Orchestrates the extraction process without knowing about
    implementation details of HTTP clients, parsers, or storage.
    """

    def __init__(
        self,
        content_extractor: ContentExtractor,
        link_parser: LinkParser,
        link_classifier: LinkClassifier,
        result_storage: Optional[ResultStorage] = None
    ):
        self._content_extractor = content_extractor
        self._link_parser = link_parser
        self._link_classifier = link_classifier
        self._result_storage = result_storage

    async def extract_and_classify(self, url: str, save_result: bool = False) -> ExtractionResult:
        """
        Main extraction workflow.

        Args:
            url: Target URL to extract links from
            save_result: Whether to persist the result

        Returns:
            Complete extraction result with classified links

        Raises:
            ExtractionError: If any step in the process fails
        """
        start_time = time.time()

        logger.info("extraction_started", url=url)

        try:
            # Step 1: Extract content
            content = await self._content_extractor.extract_content(url)
            logger.debug("content_extracted", url=url, content_length=len(content))

            # Step 2: Parse links
            raw_links = self._link_parser.parse_links(content, url)
            logger.debug("links_parsed", url=url, link_count=len(raw_links))

            # Step 3: Classify links
            classified_links = self._link_classifier.classify_links(raw_links)
            logger.debug("links_classified", url=url, classified_count=len(classified_links))

            # Step 4: Create result
            processing_time = time.time() - start_time
            metadata = ExtractionMetadata(
                total_links_found=len(classified_links),
                processing_time_seconds=processing_time
            )

            result = ExtractionResult(
                source_url=url,
                pdf_links=[link for link in classified_links if link.link_type == "pdf"],
                youtube_links=[link for link in classified_links if link.link_type == "youtube"],
                other_links=[link for link in classified_links if link.link_type == "other"],
                metadata=metadata
            )

            # Step 5: Optionally save result
            if save_result and self._result_storage:
                storage_location = await self._result_storage.save_result(result)
                logger.info("result_saved", url=url, location=storage_location)

            logger.info("extraction_completed",
                       url=url,
                       total_links=result.total_links,
                       processing_time=processing_time)

            return result

        except Exception as e:
            logger.error("extraction_failed", url=url, error=str(e))
            raise ExtractionError(f"Failed to extract content from {url}: {e}") from e
```

**Why This Architecture?**
- **Single Responsibility**: Each class has one clear purpose
- **Dependency Inversion**: Service depends on interfaces, not implementations
- **Testability**: Can mock any component for testing
- **Observability**: Structured logging throughout the process
- **Async Support**: Non-blocking operations for better performance

**4. Simple Dependency Injection**

```python
# src/container.py - Simple DI without complex frameworks
from dataclasses import dataclass
from typing import Optional

from .core.interfaces import ContentExtractor, LinkParser, LinkClassifier, ResultStorage
from .core.service import ExtractionService
from .adapters.http import HttpContentExtractor
from .adapters.parser import BeautifulSoupLinkParser
from .adapters.classifier import RegexLinkClassifier
from .adapters.storage import FileResultStorage
from .settings import Settings

@dataclass
class ServiceContainer:
    """
    Simple dependency injection container.

    Wires together all components with their dependencies.
    Makes testing easy by allowing dependency substitution.
    """
    content_extractor: ContentExtractor
    link_parser: LinkParser
    link_classifier: LinkClassifier
    result_storage: Optional[ResultStorage] = None

    def create_extraction_service(self) -> ExtractionService:
        """Create a fully configured extraction service"""
        return ExtractionService(
            content_extractor=self.content_extractor,
            link_parser=self.link_parser,
            link_classifier=self.link_classifier,
            result_storage=self.result_storage
        )

    @classmethod
    def create_default(cls, settings: Optional[Settings] = None) -> 'ServiceContainer':
        """Create container with default production implementations"""
        if settings is None:
            settings = Settings()

        return cls(
            content_extractor=HttpContentExtractor(
                timeout=settings.http_timeout,
                user_agent=settings.user_agent
            ),
            link_parser=BeautifulSoupLinkParser(),
            link_classifier=RegexLinkClassifier(),
            result_storage=FileResultStorage(settings.output_directory)
        )

    @classmethod
    def create_for_testing(cls) -> 'ServiceContainer':
        """Create container with test-friendly implementations"""
        from .adapters.mock import MockContentExtractor, MockResultStorage

        return cls(
            content_extractor=MockContentExtractor(),
            link_parser=BeautifulSoupLinkParser(),
            link_classifier=RegexLinkClassifier(),
            result_storage=MockResultStorage()
        )
```

**Why Simple DI?**
- **No framework complexity**: Easy to understand and modify
- **Explicit dependencies**: Clear what each service needs
- **Test configuration**: Easy to create test doubles
- **Production ready**: Can scale to more sophisticated DI if needed

---

## **Phase 3: Modern Implementation (1 Hour)**

### **Problem: Outdated Technology Choices**

**Current Issues:**
- **Synchronous HTTP**: `requests` library blocks on network calls
- **No structured logging**: Plain print statements
- **Manual configuration**: Hard-coded values and environment variables
- **Basic CLI**: Limited user experience

### **Solution: Modern Python Stack**

**1. Async HTTP with httpx**

```python
# src/adapters/http.py - Modern async HTTP client
import httpx
import structlog
import asyncio
from typing import Optional

from ..core.interfaces import ContentExtractor
from ..core.exceptions import ContentExtractionError

logger = structlog.get_logger()

class HttpContentExtractor:
    """
    Async HTTP content extractor using httpx.

    Provides non-blocking HTTP requests with proper error handling,
    retries, and timeout management.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "WebExtractor/1.0"
    ):
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent

    async def extract_content(self, url: str) -> str:
        """
        Extract content from URL with retries and proper error handling.

        Args:
            url: Target URL to extract content from

        Returns:
            Raw HTML content as string

        Raises:
            ContentExtractionError: If extraction fails after retries
        """
        headers = {"User-Agent": self._user_agent}

        async with httpx.AsyncClient(
            timeout=self._timeout,
            headers=headers,
            follow_redirects=True
        ) as client:

            for attempt in range(self._max_retries):
                try:
                    logger.info("http_request_started",
                              url=url,
                              attempt=attempt + 1,
                              max_retries=self._max_retries)

                    response = await client.get(url)
                    response.raise_for_status()

                    content = response.text
                    logger.info("http_request_success",
                              url=url,
                              status_code=response.status_code,
                              content_length=len(content))

                    return content

                except httpx.HTTPStatusError as e:
                    logger.warning("http_status_error",
                                 url=url,
                                 status_code=e.response.status_code,
                                 attempt=attempt + 1)
                    if attempt == self._max_retries - 1:
                        raise ContentExtractionError(
                            f"HTTP {e.response.status_code} error for {url}"
                        ) from e

                except httpx.RequestError as e:
                    logger.warning("http_request_error",
                                 url=url,
                                 error=str(e),
                                 attempt=attempt + 1)
                    if attempt == self._max_retries - 1:
                        raise ContentExtractionError(
                            f"Request failed for {url}: {e}"
                        ) from e

                # Wait before retry (exponential backoff)
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info("http_retry_wait", url=url, wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)

        # Should never reach here due to the loop logic
        raise ContentExtractionError(f"Unexpected error extracting {url}")
```

**Why httpx?**
- **Async support**: Non-blocking requests for better performance
- **Modern API**: Similar to requests but with async/await
- **HTTP/2 support**: Better performance for multiple requests
- **Proper error handling**: Distinguishes between different error types

**2. Structured Logging**

```python
# src/logging.py - Professional logging setup
import structlog
import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    service_name: str = "web-extractor"
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to output JSON format (useful for production)
        service_name: Service identifier for log correlation
    """

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add service name to all logs
    processors.append(
        structlog.processors.CallsiteParameterAdder(
            {structlog.processors.CallsiteParameterAdder.pathname,
             structlog.processors.CallsiteParameterAdder.func_name,
             structlog.processors.CallsiteParameterAdder.lineno}
        )
    )

    # Choose output format
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add service context to all logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)

def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with service context"""
    return structlog.get_logger(name)
```

**Why Structured Logging?**
- **Machine readable**: Easy to parse and analyze in production
- **Context preservation**: Maintains context across async operations
- **Correlation**: Track requests across multiple services
- **Development friendly**: Readable console output during development

**3. Settings Management with Pydantic**

```python
# src/settings.py - Type-safe configuration management
from pydantic import BaseSettings, Field, validator
from typing import Optional, Literal
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    Settings can be provided via:
    1. Environment variables (prefixed with WEB_EXTRACTOR_)
    2. .env file
    3. Default values
    """

    # HTTP Settings
    http_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
        gt=0,
        le=300
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of HTTP retry attempts",
        ge=0,
        le=10
    )

    user_agent: str = Field(
        default="WebExtractor/1.0 (+https://github.com/company/web-extractor)",
        description="HTTP User-Agent header"
    )

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )

    json_logs: bool = Field(
        default=False,
        description="Output logs in JSON format (for production)"
    )

    # Storage Settings
    output_directory: Path = Field(
        default=Path("./output"),
        description="Directory for output files"
    )

    # Optional Azure Settings
    azure_storage_connection_string: Optional[str] = Field(
        default=None,
        description="Azure Storage connection string for blob storage"
    )

    azure_storage_container: str = Field(
        default="extraction-results",
        description="Azure Storage container name"
    )

    @validator('output_directory')
    def create_output_directory(cls, v):
        """Ensure output directory exists"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @validator('user_agent')
    def user_agent_not_empty(cls, v):
        """Ensure user agent is not empty"""
        if not v.strip():
            raise ValueError('User agent cannot be empty')
        return v.strip()

    class Config:
        env_file = ".env"
        env_prefix = "WEB_EXTRACTOR_"
        case_sensitive = False

    def is_azure_storage_enabled(self) -> bool:
        """Check if Azure Storage is configured"""
        return self.azure_storage_connection_string is not None

# Global settings instance
settings = Settings()
```

**Why Pydantic Settings?**
- **Type validation**: Catches configuration errors early
- **Environment variable support**: Easy deployment configuration
- **Documentation**: Settings serve as configuration documentation
- **IDE support**: Auto-completion and type checking

**4. Modern CLI with Typer**

```python
# src/cli.py - Modern CLI interface with rich output
import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .container import ServiceContainer
from .settings import Settings
from .logging import setup_logging, get_logger

app = typer.Typer(
    name="web-extractor",
    help="Professional web content extraction and link categorization",
    rich_markup_mode="rich"
)

console = Console()
logger = get_logger()

@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract links from"),

    format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Output format: json, table, or console"
    ),

    output_file: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Save results to file (auto-detects format from extension)"
    ),

    save_to_azure: bool = typer.Option(
        False,
        "--azure",
        help="Save results to Azure Blob Storage"
    ),

    timeout: float = typer.Option(
        30.0,
        "--timeout", "-t",
        help="HTTP timeout in seconds"
    ),

    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging"
    )
):
    """
    Extract and categorize links from a web page.

    Examples:
        web-extractor https://example.com
        web-extractor https://example.com --format table --output results.json
        web-extractor https://example.com --azure --verbose
    """

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)

    # Override settings with CLI parameters
    settings = Settings(http_timeout=timeout)

    # Run async extraction
    asyncio.run(_extract_async(url, format, output_file, save_to_azure, settings))

async def _extract_async(
    url: str,
    format: str,
    output_file: Optional[Path],
    save_to_azure: bool,
    settings: Settings
):
    """Async extraction logic"""

    try:
        # Create service container
        container = ServiceContainer.create_default(settings)
        service = container.create_extraction_service()

        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task("Extracting content...", total=None)

            # Perform extraction
            result = await service.extract_and_classify(url, save_result=save_to_azure)

            progress.update(task, description="✅ Extraction complete!")

        # Display results
        _display_results(result, format)

        # Save to file if requested
        if output_file:
            _save_to_file(result, output_file)
            console.print(f"💾 Results saved to: {output_file}")

    except Exception as e:
        console.print(f"❌ [red]Error:[/red] {e}")
        logger.error("extraction_failed", url=url, error=str(e))
        raise typer.Exit(1)

def _display_results(result, format: str):
    """Display extraction results in specified format"""

    if format == "table":
        _display_table(result)
    elif format == "json":
        _display_json(result)
    else:
        _display_console(result)

def _display_table(result):
    """Display results as a rich table"""

    # Summary panel
    summary = Panel(
        f"🔗 Total Links: {result.total_links}\n"
        f"📄 PDF Links: {len(result.pdf_links)}\n"
        f"🎥 YouTube Links: {len(result.youtube_links)}\n"
        f"🌐 Other Links: {len(result.other_links)}",
        title=f"Extraction Results for {result.source_url}",
        border_style="blue"
    )
    console.print(summary)

    # Links table
    if result.total_links > 0:
        table = Table(title="Extracted Links")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Text", style="white")
        table.add_column("URL", style="blue")

        for link in result.pdf_links:
            table.add_row("📄 PDF", link.text[:50] + "..." if len(link.text) > 50 else link.text, str(link.url))

        for link in result.youtube_links:
            table.add_row("🎥 YouTube", link.text[:50] + "..." if len(link.text) > 50 else link.text, str(link.url))

        for link in result.other_links[:10]:  # Limit to first 10 for readability
            table.add_row("🌐 Other", link.text[:50] + "..." if len(link.text) > 50 else link.text, str(link.url))

        if len(result.other_links) > 10:
            table.add_row("...", f"... and {len(result.other_links) - 10} more other links", "...")

        console.print(table)

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development")
):
    """Start a development server with HTTP API"""

    try:
        import uvicorn
        from .api import create_app

        setup_logging()

        app = create_app()

        console.print(f"🚀 Starting server at http://{host}:{port}")
        console.print(f"📖 API docs at http://{host}:{port}/docs")

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload
        )

    except ImportError:
        console.print("❌ [red]Error:[/red] FastAPI and uvicorn required for serve command")
        console.print("Install with: poetry add fastapi uvicorn")
        raise typer.Exit(1)

async def demo():
    """Demo function for quick testing"""
    console.print("🎯 Running extraction demo...")
    settings = Settings()
    container = ServiceContainer.create_default(settings)
    service = container.create_extraction_service()

    demo_url = "https://httpbin.org/links/10/0"  # Simple test page
    result = await service.extract_and_classify(demo_url)

    _display_table(result)

def main():
    """Main CLI entry point"""
    app()

if __name__ == "__main__":
    main()
```

**Why Modern CLI?**
- **Rich output**: Beautiful tables and progress indicators
- **Type safety**: Typer provides automatic validation and help generation
- **User experience**: Clear error messages and helpful documentation
- **Development friendly**: Built-in help and auto-completion support

---

## **Phase 4: Professional Development Workflow (30 Minutes)**

### **Problem: Manual Quality Control**

**Current Issues:**
- No automated code formatting
- No pre-commit quality checks
- Manual testing process
- Inconsistent code style across team

### **Solution: Automated Quality Pipeline**

**1. Pre-commit Configuration**

```yaml
# .pre-commit-config.yaml - Automated code quality checks
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.290
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--strict, --ignore-missing-imports]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black", "--filter-files"]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

  - repo: https://github.com/python-poetry/poetry
    rev: 1.6.1
    hooks:
      - id: poetry-check
      - id: poetry-lock
        args: [--no-update]
```

**2. Tool Configuration**

```toml
# pyproject.toml - Tool configuration section
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011"]

[tool.mypy]
python_version = "3.10"
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_decorators = true
disallow_untyped_defs = true
ignore_missing_imports = true
no_implicit_optional = true
show_error_codes = true
strict_equality = true
warn_redundant_casts = true
warn_return_any = true
warn_unreachable = true
warn_unused_configs = true
warn_unused_ignores = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/conftest.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101", "B601"]
```

**3. Professional Testing Structure**

```python
# tests/conftest.py - Test configuration and fixtures
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

from src.container import ServiceContainer
from src.settings import Settings
from src.core.models import ExtractionResult, ExtractedLink, ExtractionMetadata

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings() -> Settings:
    """Test-specific settings"""
    return Settings(
        http_timeout=5.0,
        max_retries=1,
        log_level="DEBUG",
        output_directory="./test_output"
    )

@pytest.fixture
def mock_container() -> ServiceContainer:
    """Service container with mocked dependencies for testing"""
    return ServiceContainer.create_for_testing()

@pytest.fixture
async def extraction_service(mock_container):
    """Pre-configured extraction service for testing"""
    return mock_container.create_extraction_service()

@pytest.fixture
def sample_extraction_result() -> ExtractionResult:
    """Sample extraction result for testing"""
    return ExtractionResult(
        source_url="https://example.com",
        pdf_links=[
            ExtractedLink(
                url="https://example.com/doc.pdf",
                text="Sample PDF",
                link_type="pdf"
            )
        ],
        youtube_links=[
            ExtractedLink(
                url="https://youtube.com/watch?v=123",
                text="Sample Video",
                link_type="youtube"
            )
        ],
        other_links=[
            ExtractedLink(
                url="https://example.com/page",
                text="Sample Page",
                link_type="other"
            )
        ],
        metadata=ExtractionMetadata(
            total_links_found=3,
            processing_time_seconds=0.5
        )
    )

# Cleanup
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test"""
    yield
    # Cleanup code here if needed
    import shutil
    import os

    test_dirs = ["./test_output", "./logs"]
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
```

```python
# tests/test_service.py - Service layer tests
import pytest
from unittest.mock import AsyncMock, Mock

from src.core.service import ExtractionService
from src.core.exceptions import ExtractionError

class TestExtractionService:
    """Test the core extraction service"""

    async def test_successful_extraction(self, extraction_service, sample_extraction_result):
        """Test successful extraction workflow"""
        # Arrange
        test_url = "https://example.com"

        # Act
        result = await extraction_service.extract_and_classify(test_url)

        # Assert
        assert result.source_url == test_url
        assert result.total_links >= 0
        assert result.metadata is not None
        assert result.metadata.processing_time_seconds > 0

    async def test_extraction_with_save(self, extraction_service):
        """Test extraction with result saving"""
        # Arrange
        test_url = "https://example.com"

        # Act
        result = await extraction_service.extract_and_classify(test_url, save_result=True)

        # Assert
        assert result is not None
        # Verify that storage was called (would need to check mock)

    async def test_extraction_failure(self, mock_container):
        """Test extraction failure handling"""
        # Arrange
        mock_container.content_extractor.extract_content = AsyncMock(
            side_effect=Exception("Network error")
        )
        service = mock_container.create_extraction_service()

        # Act & Assert
        with pytest.raises(ExtractionError):
            await service.extract_and_classify("https://invalid.com")

    @pytest.mark.integration
    async def test_real_extraction(self):
        """Integration test with real HTTP request"""
        from src.container import ServiceContainer
        from src.settings import Settings

        # Arrange
        settings = Settings(http_timeout=10.0)
        container = ServiceContainer.create_default(settings)
        service = container.create_extraction_service()

        # Act
        result = await service.extract_and_classify("https://httpbin.org/links/3/0")

        # Assert
        assert result.total_links >= 0
        assert result.metadata.processing_time_seconds > 0
```

**4. CI/CD Pipeline Configuration**

```yaml
# .github/workflows/ci.yml - GitHub Actions CI pipeline
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: latest
        virtualenvs-create: true
        virtualenvs-in-project: true

    - name: Load cached venv
      id: cached-poetry-dependencies
      uses: actions/cache@v3
      with:
        path: .venv
        key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}

    - name: Install dependencies
      if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
      run: poetry install --no-interaction --no-root

    - name: Install project
      run: poetry install --no-interaction

    - name: Run pre-commit hooks
      run: |
        poetry run pre-commit run --all-files

    - name: Run tests
      run: |
        poetry run pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  docker:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: |
        docker build -t web-extractor:latest .

    - name: Test Docker image
      run: |
        docker run --rm web-extractor:latest --help
```

**Why This Workflow?**
- **Automated quality**: Catches issues before they reach main branch
- **Consistent formatting**: All team members use same code style
- **Type safety**: MyPy catches type-related bugs early
- **Security**: Bandit scans for security vulnerabilities
- **Fast feedback**: Pre-commit hooks run locally before commit

---

## **Phase 5: Production Deployment (30 Minutes)**

### **Problem: Deployment Complexity**

**Current Issues:**
- Manual deployment steps
- No health checks
- Basic Docker configuration
- No monitoring or observability

### **Solution: Production-Ready Deployment**

**1. Optimized Docker Configuration**

```dockerfile
# Dockerfile - Multi-stage production build
# Build stage
FROM python:3.11-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Production stage
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Create necessary directories with correct permissions
RUN mkdir -p output logs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app \
    WEB_EXTRACTOR_LOG_LEVEL=INFO \
    WEB_EXTRACTOR_JSON_LOGS=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Docker Compose for Development**

```yaml
# docker-compose.yml - Development environment
version: '3.8'

services:
  web-extractor:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: web-extractor-dev
    ports:
      - "8000:8000"
    environment:
      - WEB_EXTRACTOR_LOG_LEVEL=DEBUG
      - WEB_EXTRACTOR_JSON_LOGS=false
      - WEB_EXTRACTOR_OUTPUT_DIRECTORY=/app/output
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - extractor-network

  # Azure Storage Emulator for local development
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:latest
    container_name: azurite-dev
    ports:
      - "10000:10000"  # Blob service
      - "10001:10001"  # Queue service
      - "10002:10002"  # Table service
    volumes:
      - azurite-data:/data
    command: "azurite --silent --location /data --debug /data/debug.log --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0"
    networks:
      - extractor-network

  # Monitoring with Prometheus (optional)
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-dev
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - extractor-network

volumes:
  azurite-data:

networks:
  extractor-network:
    driver: bridge
```

**3. Azure Container Apps Deployment**

```yaml
# azure/container-app.yml - Azure Container Apps configuration
apiVersion: 2022-03-01
location: westus2
identity:
  type: SystemAssigned
properties:
  managedEnvironmentId: /subscriptions/{subscription-id}/resourceGroups/{rg-name}/providers/Microsoft.App/managedEnvironments/{env-name}
  configuration:
    activeRevisionsMode: Single
    ingress:
      external: true
      targetPort: 8000
      allowInsecure: false
      traffic:
        - weight: 100
          latestRevision: true
    secrets:
      - name: azure-storage-connection-string
        value: "{storage-connection-string}"
    registries:
      - server: {acr-name}.azurecr.io
        identity: system
  template:
    containers:
      - image: {acr-name}.azurecr.io/web-extractor:latest
        name: web-extractor
        env:
          - name: WEB_EXTRACTOR_LOG_LEVEL
            value: INFO
          - name: WEB_EXTRACTOR_JSON_LOGS
            value: "true"
          - name: WEB_EXTRACTOR_AZURE_STORAGE_CONNECTION_STRING
            secretRef: azure-storage-connection-string
        resources:
          cpu: 1.0
          memory: 2Gi
        probes:
          - type: Liveness
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
          - type: Readiness
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
    scale:
      minReplicas: 1
      maxReplicas: 10
      rules:
        - name: http-rule
          http:
            metadata:
              concurrentRequests: "30"
```

**4. Infrastructure as Code**

```bash
# scripts/deploy-azure.sh - Automated Azure deployment
#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="rg-web-extractor-prod"
LOCATION="westus2"
ACR_NAME="acrwebextractor"
CONTAINER_APP_ENV="env-web-extractor"
CONTAINER_APP="app-web-extractor"
STORAGE_ACCOUNT="stwebextractor"

echo "🚀 Deploying Web Content Extractor to Azure..."

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Build and push image
echo "🔨 Building and pushing container image..."
az acr build \
    --registry $ACR_NAME \
    --image web-extractor:latest \
    .

# Create storage account
echo "💾 Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# Get storage connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString -o tsv)

# Create Container Apps environment
echo "🌐 Creating Container Apps environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Deploy container app
echo "🚀 Deploying container app..."
az containerapp create \
    --name $CONTAINER_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image "$ACR_NAME.azurecr.io/web-extractor:latest" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 10 \
    --cpu 1.0 \
    --memory 2Gi \
    --secrets "azure-storage-connection-string=$STORAGE_CONNECTION_STRING" \
    --env-vars \
        "WEB_EXTRACTOR_LOG_LEVEL=INFO" \
        "WEB_EXTRACTOR_JSON_LOGS=true" \
        "WEB_EXTRACTOR_AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection-string"

# Get the app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_URL"
echo "📊 Health check: https://$APP_URL/health"
echo "📖 API docs: https://$APP_URL/docs"
```

---

## **Complete Implementation Timeline**

### **Day 1: Foundation (4 hours)**
```bash
# Hour 1: Setup modern tooling
poetry init
make setup

# Hour 2: Clean architecture
# - Create interfaces
# - Implement service layer
# - Simple dependency injection

# Hour 3: Modern implementation
# - Async HTTP with httpx
# - Structured logging
# - Pydantic settings

# Hour 4: Professional CLI
# - Typer integration
# - Rich output
# - Command validation
```

### **Day 2: Quality & Deployment (4 hours)**
```bash
# Hour 1: Development workflow
# - Pre-commit hooks
# - Testing structure
# - CI/CD pipeline

# Hour 2: Docker optimization
# - Multi-stage builds
# - Security hardening
# - Health checks

# Hour 3: Azure deployment
# - Container Apps configuration
# - Infrastructure automation
# - Monitoring setup

# Hour 4: Documentation & testing
# - API documentation
# - Integration tests
# - Performance validation
```

### **Result: Professional Production System**

**Developer Experience:**
```bash
# Simple start
git clone repo && make setup && make run

# Professional workflow
make test      # Full test suite
make lint      # Code quality checks
make docker    # Container testing
make deploy    # Production deployment
```

**Architecture Benefits:**
- ✅ **Testable**: Clean interfaces enable easy mocking
- ✅ **Maintainable**: Single responsibility services
- ✅ **Scalable**: Async design supports high concurrency
- ✅ **Observable**: Structured logging and health checks
- ✅ **Deployable**: Production-ready containerization

**Professional Standards:**
- ✅ **Type Safety**: Full mypy compliance
- ✅ **Code Quality**: Automated formatting and linting
- ✅ **Security**: Non-root containers, dependency scanning
- ✅ **Monitoring**: Health checks and structured logging
- ✅ **Documentation**: Self-documenting code and APIs

This transformation provides a **professional foundation** while maintaining **simplicity for quick starts**. The architecture supports both solo development and team collaboration, with clear pathways for adding features like caching, authentication, and advanced monitoring.

---

## **Quick Reference: Implementation Commands**

### **Getting Started**
```bash
# One-time setup
git clone https://github.com/company/web-content-extractor.git
cd web-content-extractor
make setup

# Daily development
make run        # Quick extraction demo
make test       # Run test suite
make lint       # Check code quality
make format     # Format code
make docker     # Test containerization
```

### **New Feature Development**
```bash
# Create feature branch
git checkout -b feature/new-link-type

# Implement with TDD
poetry run pytest tests/test_new_feature.py --watch

# Quality check before commit
make lint
git commit -m "Add new link classification"

# Pre-commit hooks automatically run:
# - Code formatting (black)
# - Import sorting (isort)
# - Linting (ruff)
# - Type checking (mypy)
# - Security scanning (bandit)
```

### **Production Deployment**
```bash
# Build and test locally
make docker

# Deploy to Azure
./scripts/deploy-azure.sh

# Monitor deployment
az containerapp logs tail --name app-web-extractor --resource-group rg-web-extractor-prod
```

### **Testing Commands**
```bash
# Unit tests only
poetry run pytest tests/unit/ -v

# Integration tests
poetry run pytest tests/integration/ -v -m integration

# Coverage report
poetry run pytest --cov=src --cov-report=html

# Performance tests
poetry run pytest tests/ -m "not slow" --durations=10
```

This guide transforms a simple project into a **professional-grade application** while preserving the **quick start philosophy**. Each improvement adds value immediately and builds toward production readiness.
