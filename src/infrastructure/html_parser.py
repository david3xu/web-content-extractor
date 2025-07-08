"""
HTML parser for extracting and processing links.
"""

import re
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
            links = []

            # Extract anchor links
            links.extend(self._extract_anchor_links(soup, base_url))

            # Extract iframe sources (YouTube embeds)
            links.extend(self._extract_iframe_sources(soup, base_url))

            # Extract object/embed sources (PDFs)
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
        for anchor in soup.find_all("a", href=True):
            href = SafeAttributeExtractor.get_optional_string_attribute(anchor, "href")
            if href and not href.startswith(("javascript:", "#", "mailto:", "tel:")):
                full_url = urljoin(base_url, href)
                # Use helper to obtain clean, de-duplicated text
                text = self._get_link_text(anchor, full_url)
                extracted.append((full_url, text))
        return extracted

    def _extract_iframe_sources(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        extracted = []
        for iframe in soup.find_all("iframe", src=True):
            src = iframe.get("src")
            if src:
                full_url = urljoin(base_url, src)
                text = iframe.get("title") or "Embedded Content"
                extracted.append((full_url, text))
        return extracted

    def _extract_embedded_objects(
        self, soup: BeautifulSoup, base_url: str
    ) -> list[tuple[str, str]]:
        extracted = []
        # Object tags
        for obj in soup.find_all("object", data=True):
            data = obj.get("data")
            if data:
                full_url = urljoin(base_url, data)
                text = obj.get("title") or "Embedded Object"
                extracted.append((full_url, text))

        # Embed tags
        for embed in soup.find_all("embed", src=True):
            src = embed.get("src")
            if src:
                full_url = urljoin(base_url, src)
                text = embed.get("title") or "Embedded Content"
                extracted.append((full_url, text))

        return extracted

    def _get_link_text(self, element: Tag, url: str) -> str:
        """Get text for <a> tags, prioritizing download attribute if present."""
        # Candidate texts: download attr, inner text, href fallback
        download_name = SafeAttributeExtractor.get_optional_string_attribute(
            element, "download"
        )

        candidates: list[str | None] = [download_name]

        element_text = element.get_text(strip=True)
        if element_text:
            candidates.append(element_text)

        candidates.append(
            SafeAttributeExtractor.get_string_attribute(element, "href", url)
        )

        # Pick first non-empty candidate
        raw_text: str = next((c for c in candidates if c), url)

        # Post-process: collapse duplicate ".pdf" suffixes (e.g. "file.pdfpdf" → "file.pdf")
        cleaned_text: str = re.sub(r"(\.pdf)+$", ".pdf", raw_text, flags=re.I)

        return cleaned_text.strip()

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

    def find_navigation_links(self, content: str, base_url: str) -> list[str]:
        """Find sub-pages to crawl using existing parsing logic."""
        soup = BeautifulSoup(content, "html.parser")
        navigation_links: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = SafeAttributeExtractor.get_optional_string_attribute(anchor, "href")
            if href:
                full_url = urljoin(base_url, href)
                # Filter out external links, javascript, mailto, and fragment identifiers
                if (
                    self._is_valid_url(full_url)
                    and urlparse(full_url).netloc == urlparse(base_url).netloc
                    and not full_url.startswith(("javascript:", "mailto:", "#"))
                    and not full_url.endswith(
                        (".pdf", ".zip", ".tar.gz", ".docx", ".xlsx", ".pptx")
                    )  # Exclude common file downloads
                ):
                    navigation_links.add(full_url)

        return list(navigation_links)
