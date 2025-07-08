"""
Pytest configuration and fixtures.
"""
import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import pytest

from src.core.exceptions import ExtractionContext
from src.core.value_objects import CorrelationId, SourceUrl
from src.logging import setup_logging

_T = TypeVar("_T")


@pytest.fixture(scope="session", autouse=True)  # type: ignore[misc]
def setup_test_logging() -> None:
    """Set up logging for tests."""
    setup_logging(level="WARNING", json_logs=False)


@pytest.fixture  # type: ignore[misc]
def temp_output_dir() -> Generator[Path, Any, None]:
    """Create a temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture  # type: ignore[misc]
def sample_html_content() -> str:
    """Sample HTML content for testing."""
    return """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Welcome to Test Page</h1>
            <p>This is a test page with various links.</p>

            <h2>Documents</h2>
            <ul>
                <li><a href="https://example.com/document.pdf">Download PDF Document</a></li>
                <li><a href="https://docs.example.com/report.PDF">Annual Report</a></li>
                <li><a href="/files/manual.pdf">User Manual</a></li>
            </ul>

            <h2>Videos</h2>
            <ul>
                <li><a href="https://youtube.com/watch?v=abc123">Tutorial Video</a></li>
                <li><a href="https://youtu.be/xyz789">Quick Demo</a></li>
                <li><a href="https://youtube.com/embed/def456">Embedded Video</a></li>
            </ul>

            <h2>Other Links</h2>
            <ul>
                <li><a href="https://example.com">Home Page</a></li>
                <li><a href="https://github.com/user/repo">GitHub Repository</a></li>
                <li><a href="https://stackoverflow.com">Stack Overflow</a></li>
                <li><a href="javascript:void(0)">JavaScript Link</a></li>
                <li><a href="#section">Internal Link</a></li>
                <li><a href="mailto:test@example.com">Email Link</a></li>
            </ul>
        </body>
    </html>
    """


@pytest.fixture  # type: ignore[misc]
def sample_urls() -> list[str]:
    """Sample URLs for testing."""
    return [
        "https://example.com",
        "https://python.org",
        "https://github.com",
        "https://stackoverflow.com",
    ]


@pytest.fixture  # type: ignore[misc]
def sample_correlation_id() -> CorrelationId:
    """Sample correlation ID for testing."""
    return CorrelationId.generate()


@pytest.fixture  # type: ignore[misc]
def sample_source_url() -> SourceUrl:
    """Sample source URL for testing."""
    return SourceUrl.from_string("https://example.com")


@pytest.fixture  # type: ignore[misc]
def sample_extraction_context(
    sample_correlation_id: "CorrelationId",
) -> ExtractionContext:
    """Sample extraction context for testing."""
    return ExtractionContext(
        url="https://example.com",
        correlation_id=sample_correlation_id,
        start_time=datetime.now(),
    )
