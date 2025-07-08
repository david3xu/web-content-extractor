import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from ..models.exceptions import ContentScrapingError


class HttpClient:
    def __init__(self, timeout: int = 30, max_retries: int = 3, user_agent: str = None):
        self.session = requests.Session()
        self.timeout = timeout

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})

    def get_content(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise ContentScrapingError(f"Failed to fetch content from {url}: {str(e)}")

    def close(self):
        self.session.close()
