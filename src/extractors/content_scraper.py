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
