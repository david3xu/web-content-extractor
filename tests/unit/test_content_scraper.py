import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

from src.extractors.content_scraper import ContentScrapingService
from src.utils.http_client import HttpClient
from src.models.exceptions import ContentScrapingError


class TestContentScrapingService(unittest.TestCase):
    def setUp(self):
        self.mock_http_client = MagicMock(spec=HttpClient)
        self.scraper = ContentScrapingService(self.mock_http_client)

    def test_extract_web_content(self):
        # Setup
        html_content = "<html><head><title>Test Page</title></head><body><a href='test.pdf'>PDF Link</a></body></html>"
        self.mock_http_client.get_content.return_value = html_content

        # Execute
        soup, content = self.scraper.extract_web_content("https://example.com")

        # Assert
        self.assertEqual(content, html_content)
        self.assertIsInstance(soup, BeautifulSoup)
        self.mock_http_client.get_content.assert_called_once_with("https://example.com")

    def test_extract_web_content_error(self):
        # Setup
        self.mock_http_client.get_content.side_effect = Exception("Connection error")

        # Execute & Assert
        with self.assertRaises(ContentScrapingError):
            self.scraper.extract_web_content("https://example.com")

    def test_extract_all_links(self):
        # Setup
        html = """
        <html>
            <body>
                <a href="https://example.com/doc.pdf">PDF</a>
                <a href="/relative/path">Relative</a>
                <a href="https://youtube.com/watch?v=12345">YouTube</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com"

        # Execute
        links = self.scraper.extract_all_links(soup, base_url)

        # Assert
        self.assertEqual(len(links), 3)
        self.assertIn(("https://example.com/doc.pdf", "PDF"), links)
        self.assertIn(("https://example.com/relative/path", "Relative"), links)
        self.assertIn(("https://youtube.com/watch?v=12345", "YouTube"), links)

    def test_get_page_title(self):
        # Setup
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')

        # Execute
        title = self.scraper.get_page_title(soup)

        # Assert
        self.assertEqual(title, "Test Title")

    def test_get_page_title_missing(self):
        # Setup
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')

        # Execute
        title = self.scraper.get_page_title(soup)

        # Assert
        self.assertIsNone(title)


if __name__ == '__main__':
    unittest.main()
