"""
HTML parser for extracting and processing links.
"""

from datetime import datetime
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup, Tag

from src.core.exceptions import ExtractionContext, LinkParsingError
from src.core.interfaces import LinkParser
from src.core.value_objects import CorrelationId


class SafeAttributeExtractor:
    """Encapsulates type-safe HTML attribute extraction"""

    @staticmethod
    def get_string_attribute(element: Tag, attr: str, default: str = "") -> str:
        """Type-safe string attribute extraction"""
        value = element.get(attr)
        if isinstance(value, str):
            return value
        return default

    @staticmethod
    def get_optional_string_attribute(element: Tag, attr: str) -> str | None:
        """Type-safe optional string extraction"""
        value = element.get(attr)
        if isinstance(value, str):
            return value
        return None


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

            # ENHANCED: One unified extraction method
            links = self._extract_all_content(soup, base_url)

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

    def _extract_all_content(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        """Unified content extraction - replaces multiple scattered methods"""
        content_items = []

        # Standard links + download attributes + iframes + embeds
        for element in soup.find_all(["a", "iframe", "embed"]):
            if item := self._process_element(element, base_url):
                content_items.append(item)

        return content_items

    def _process_element(self, element: Tag, base_url: str) -> tuple[str, str] | None:
        """Process any content element - single responsibility"""
        # Handle <a> tags
        if element.name == "a":
            href = SafeAttributeExtractor.get_optional_string_attribute(element, "href")
            if href and not href.startswith(("javascript:", "#", "mailto:", "tel:")):
                url = urljoin(base_url, href)
                text = self._get_link_text(element, url)
                return (url, text)

        # Handle iframes
        elif element.name == "iframe":
            src = SafeAttributeExtractor.get_optional_string_attribute(element, "src")
            if src:
                url = urljoin(base_url, src)
                text = self._get_iframe_text(element, url)
                return (url, text)

        # Handle embed tags (for generic embedded content)
        elif element.name == "embed":
            src = SafeAttributeExtractor.get_optional_string_attribute(element, "src")
            if src:
                url = urljoin(base_url, src)
                text = self._get_embed_text(element, url)
                return (url, text)

        return None

    def _get_link_text(self, element: Tag, url: str) -> str:
        """Get text for <a> tags, prioritizing download attribute if present."""
        download_name = SafeAttributeExtractor.get_optional_string_attribute(
            element, "download"
        )
        if download_name is not None:
            return download_name

        element_text = element.get_text(strip=True)
        if element_text:
            return str(element_text)

        return SafeAttributeExtractor.get_string_attribute(element, "href", url)

    def _get_iframe_text(self, element: Tag, url: str) -> str:
        """Generate descriptive text for iframe content."""
        # Check for YouTube indicators
        if any(
            indicator in url.lower()
            for indicator in ["youtube", "youtu.be", "embed", "iframe.ly"]
        ):
            return "Embedded Video Content"

        # Use title attribute if available
        if title := SafeAttributeExtractor.get_optional_string_attribute(
            element, "title"
        ):
            return title

        # Fallback to URL
        return f"Embedded Content: {url}"

    def _get_embed_text(self, element: Tag, url: str) -> str:
        """Generate descriptive text for <embed> content."""
        # Use type attribute if available, otherwise fallback to URL
        if embed_type := SafeAttributeExtractor.get_optional_string_attribute(
            element, "type"
        ):
            return f"Embedded {embed_type.split('/')[-1].upper()} Content"
        return f"Embedded Content: {url}"

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
