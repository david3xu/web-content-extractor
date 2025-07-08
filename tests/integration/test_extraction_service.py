"""
Integration tests for the extraction service.
"""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.core import ExtractionService
from src.core.value_objects import CorrelationId
from src.core.exceptions import ContentExtractionError, ExtractionContext
from src.core.models import LinkType
from src.infrastructure import (
    AsyncHttpClient,
    BeautifulSoupLinkParser,
    LocalFileStorage,
    ContextAwareClassifier,
)


class TestExtractionServiceIntegration:
    """Integration tests for ExtractionService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.http_client = AsyncHttpClient()
        self.link_parser = BeautifulSoupLinkParser()
        self.link_classifier = ContextAwareClassifier()
        self.storage = LocalFileStorage()

        self.service = ExtractionService(
            content_extractor=self.http_client,
            link_parser=self.link_parser,
            link_classifier=self.link_classifier,
            result_storage=self.storage,
        )

    @pytest.mark.asyncio  # type: ignore[misc]
    @patch("src.infrastructure.http_client.httpx.AsyncClient")
    async def test_extract_and_classify_mock_http(self, mock_client: AsyncMock) -> None:
        """Test extraction with mocked HTTP client."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <a href="https://example.com/document.pdf">Download PDF</a>
                <a href="https://youtube.com/watch?v=abc123">Watch Video</a>
                <a href="https://example.com">Home Page</a>
            </body>
        </html>
        """
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Run extraction
        result = await self.service.extract_and_classify("https://example.com")

        # Verify results
        assert str(result.source_url.value) == "https://example.com/"
        assert result.total_links == 3

        # Check PDF links
        assert len(result.pdf_links) == 1
        assert str(result.pdf_links[0].url) == "https://example.com/document.pdf"
        assert result.pdf_links[0].link_text == "Download PDF"
        assert result.pdf_links[0].link_type == LinkType.PDF

        # Check YouTube links
        assert len(result.youtube_links) == 1
        assert str(result.youtube_links[0].url) == "https://youtube.com/watch?v=abc123"
        assert result.youtube_links[0].link_text == "Watch Video"
        assert result.youtube_links[0].link_type == LinkType.YOUTUBE

        # Check other links
        assert len(result.other_links) == 1
        assert str(result.other_links[0].url) == "https://example.com/"
        assert result.other_links[0].link_text == "Home Page"
        assert result.other_links[0].link_type == LinkType.OTHER

        # Check metadata
        assert result.metadata is not None
        assert result.metadata.total_links_found == 3
        assert result.metadata.pdf_count == 1
        assert result.metadata.youtube_count == 1
        assert result.metadata.processing_time.seconds > 0

    @pytest.mark.asyncio  # type: ignore[misc]
    @patch("src.infrastructure.http_client.httpx.AsyncClient")
    async def test_extract_with_storage(self, mock_client: AsyncMock) -> None:
        """Test extraction with result storage."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.text = '<a href="https://example.com/doc.pdf">PDF</a>'
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Mock storage
        with patch.object(
            self.storage, "save_result", new_callable=AsyncMock
        ) as mock_save:
            mock_save.return_value = "/tmp/test_output.json"

            # Run extraction with storage
            result = await self.service.extract_and_classify(
                "https://example.com", save_result=True
            )

            # Verify storage was called
            mock_save.assert_called_once()
            assert result.total_links == 1

    @pytest.mark.asyncio  # type: ignore[misc]
    @patch("src.infrastructure.http_client.httpx.AsyncClient")
    async def test_extract_http_error_handling(self, mock_client: AsyncMock) -> None:
        """Test handling of HTTP errors."""
        # Mock HTTP error
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = ContentExtractionError(
            "Connection failed",
            ExtractionContext(
                url="https://example.com",
                correlation_id=CorrelationId.generate(),
                start_time=datetime.now(),
            ),
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Run extraction and expect error
        with pytest.raises(ContentExtractionError):
            await self.service.extract_and_classify("https://example.com")

    @pytest.mark.asyncio  # type: ignore[misc]
    @patch("src.infrastructure.http_client.httpx.AsyncClient")
    async def test_extract_empty_page(self, mock_client: AsyncMock) -> None:
        """Test extraction from page with no links."""
        # Mock HTTP response with no links
        mock_response = AsyncMock()
        mock_response.text = "<html><body><p>No links here</p></body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Run extraction
        result = await self.service.extract_and_classify("https://example.com")

        # Verify empty results
        assert result.total_links == 0
        assert len(result.pdf_links) == 0
        assert len(result.youtube_links) == 0
        assert len(result.other_links) == 0
