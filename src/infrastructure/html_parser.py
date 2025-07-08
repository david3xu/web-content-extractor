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
            for tag in soup.find_all(attrs={"href": True}) + soup.find_all(
                attrs={"src": True}
            ):
                url = tag.get("href") or tag.get("src")

                if not url:
                    continue

                url = url.strip()

                # Skip empty, javascript, and fragment-only links
                if not url or url.startswith(("javascript:", "#", "mailto:", "tel:")):
                    continue

                # Resolve relative URLs to absolute
                full_url = urljoin(base_url, url)

                # Parse text (use tag text, title, img alt, or url as fallback)
                link_text = tag.get_text(strip=True)
                if not link_text:
                    if tag.get("title"):
                        link_text = tag["title"]
                    elif tag.name == "img" and tag.get("alt"):
                        link_text = tag["alt"]
                    elif tag.find("img") and tag.find("img").get("alt"):
                        link_text = tag.find("img")["alt"]
                    else:
                        link_text = full_url

                links.append((full_url, link_text))

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
