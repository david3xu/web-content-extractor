"""
HTML parser for extracting and processing links.
"""
from typing import List, Tuple
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup

from src.core.interfaces import LinkParser
from src.core.exceptions import LinkParsingError

logger = structlog.get_logger(__name__)


class BeautifulSoupLinkParser(LinkParser):
    """
    HTML link parser using BeautifulSoup.

    Implements the LinkParser protocol.
    """

    def parse_links(self, content: str, base_url: str) -> List[Tuple[str, str]]:
        """
        Parse links from HTML content.

        Args:
            content: HTML content as string
            base_url: Base URL for resolving relative links

        Returns:
            List of tuples containing (url, link_text)

        Raises:
            LinkParsingError: If parsing fails
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Get page title if available
            title = soup.title.string if soup.title else "Unknown Page"
            logger.debug("parsing_page", title=title, base_url=base_url)

            # Find all links
            links = []
            for anchor in soup.find_all('a', href=True):
                href = anchor['href'].strip()

                # Skip empty, javascript, and fragment-only links
                if not href or href.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                    continue

                # Resolve relative URLs to absolute
                full_url = urljoin(base_url, href)

                # Parse text (use href as fallback)
                link_text = anchor.get_text(strip=True)
                if not link_text:
                    # Try to use title attribute or image alt text
                    if anchor.get('title'):
                        link_text = anchor['title']
                    elif anchor.find('img') and anchor.find('img').get('alt'):
                        link_text = anchor.find('img')['alt']
                    else:
                        link_text = full_url

                links.append((full_url, link_text))

            logger.debug("links_found", count=len(links), base_url=base_url)
            return links

        except Exception as e:
            logger.error("parsing_failed", error=str(e), base_url=base_url)
            raise LinkParsingError(f"Failed to parse links from {base_url}: {e}") from e

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
        except:
            return False
