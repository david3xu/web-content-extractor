"""
HTML parser for extracting and processing links.
"""
from datetime import datetime
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup

from src.core.exceptions import ExtractionContext, LinkParsingError
from src.core.interfaces import LinkParser
from src.core.value_objects import CorrelationId

logger = structlog.get_logger(__name__)


class BeautifulSoupLinkParser(LinkParser):
    """
    HTML link parser using BeautifulSoup.

    Implements the LinkParser protocol.
    """

    def parse_links(self, content: str, base_url: str) -> list[tuple[str, str]]:
        """
        Parse links from HTML content with enhanced error context.
        """
        try:
            soup = BeautifulSoup(content, "html.parser")

            # Get page title if available
            title = soup.title.string if soup.title else "Unknown Page"
            logger.debug("parsing_page", title=title, base_url=base_url)

            # Find all links (broad search for href or src attributes)
            links = []

            # EXISTING: <a> tag extraction
            links.extend(self._extract_anchor_links(soup, base_url))

            # NEW: Add iframe sources (YouTube embeds)
            links.extend(self._extract_iframe_sources(soup, base_url))

            # NEW: Add embedded content
            links.extend(self._extract_embedded_objects(soup, base_url))

            logger.debug("links_found", count=len(links), base_url=base_url)
            return links

        except Exception as e:
            logger.error("parsing_failed", error=str(e), base_url=base_url)
            context = ExtractionContext(
                url=base_url,
                correlation_id=CorrelationId.generate(),
                start_time=datetime.now(),
            )
            raise LinkParsingError(
                f"Failed to parse links from {base_url}", context, e
            ) from e

    def _extract_anchor_links(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        extracted = []
        for tag in soup.find_all("a", href=True):
            url = tag.get("href")
            if not url or url.startswith(("javascript:", "#", "mailto:", "tel:")):
                continue
            full_url = urljoin(base_url, url)
            link_text = tag.get_text(strip=True) or full_url
            extracted.append((full_url, link_text))
        return extracted

    def _extract_iframe_sources(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        """Extract YouTube and other embedded content from iframes."""
        extracted = []
        for tag in soup.find_all("iframe", src=True):
            url = tag.get("src")
            if url:
                full_url = urljoin(base_url, url)
                if self._is_valid_url(full_url):
                    extracted.append((full_url, full_url))  # Use full_url as text fallback
        return extracted

    def _extract_embedded_objects(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        """Extract PDF embeds and download elements from object and embed tags."""
        extracted = []
        for tag in soup.find_all("object", data=True):
            url = tag.get("data")
            if url:
                full_url = urljoin(base_url, url)
                if self._is_valid_url(full_url):
                    extracted.append((full_url, full_url))  # Use full_url as text fallback
        for tag in soup.find_all("embed", src=True):
            url = tag.get("src")
            if url:
                full_url = urljoin(base_url, url)
                if self._is_valid_url(full_url):
                    extracted.append((full_url, full_url))  # Use full_url as text fallback
        return extracted

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid.

        Args:
            url: URL string to check

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:  # More specific exception handling
            return False
