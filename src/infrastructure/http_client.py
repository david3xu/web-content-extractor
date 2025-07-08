"""
Async HTTP client for web content extraction.
"""
import asyncio
from typing import Optional, Dict, Any

import httpx
import structlog

from src.core.interfaces import ContentExtractor
from src.core.exceptions import ContentExtractionError
from src.settings import settings

logger = structlog.get_logger(__name__)


class AsyncHttpClient(ContentExtractor):
    """
    Async HTTP client for web content extraction.

    Implements the ContentExtractor protocol.
    """

    def __init__(
        self,
        timeout: float = None,
        max_retries: int = None,
        user_agent: str = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout = timeout or settings.http_timeout
        self.max_retries = max_retries or settings.max_retries
        self.user_agent = user_agent or settings.user_agent

        self._headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if headers:
            self._headers.update(headers)

    async def extract_content(self, url: str) -> str:
        """
        Extract HTML content from a URL with retries.

        Args:
            url: The URL to fetch

        Returns:
            The HTML content as string

        Raises:
            ContentExtractionError: If extraction fails after retries
        """
        logger.debug("extracting_content", url=url)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.get(url, headers=self._headers)
                    response.raise_for_status()

                    # Log successful extraction
                    content_length = len(response.text)
                    logger.debug(
                        "content_extracted",
                        url=url,
                        content_length=content_length,
                        status_code=response.status_code
                    )

                    return response.text

                except httpx.TimeoutException:
                    logger.warning(
                        "request_timeout",
                        url=url,
                        attempt=attempt,
                        max_retries=self.max_retries
                    )

                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)  # exponential backoff
                    else:
                        raise ContentExtractionError(f"Timeout extracting content from {url}")

                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "http_error",
                        url=url,
                        status_code=e.response.status_code,
                        attempt=attempt
                    )

                    if 500 <= e.response.status_code < 600 and attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise ContentExtractionError(
                            f"HTTP error {e.response.status_code} extracting content from {url}"
                        ) from e

                except httpx.HTTPError as e:
                    logger.error("http_exception", url=url, error=str(e), attempt=attempt)
                    raise ContentExtractionError(f"HTTP error extracting content from {url}") from e

        # This should not be reached due to exceptions above
        raise ContentExtractionError(f"Failed to extract content from {url}")
