import unittest
import os
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from src.extractors.web_content_extractor import WebContentExtractor
from src.models.extraction_models import LinkCategorizationResult
from ..fixtures.sample_data import SAMPLE_HTML, SAMPLE_CATEGORIZATION_RESULT


class TestWebExtractorIntegration(unittest.TestCase):

    def setUp(self):
        # Create temporary output directory for tests
        self.test_output_dir = "./test_output"
        os.makedirs(self.test_output_dir, exist_ok=True)

        # Create extractor instance
        self.extractor = WebContentExtractor(
            timeout=10,
            max_retries=1,
            user_agent="TestUserAgent",
            output_directory=self.test_output_dir
        )

    def tearDown(self):
        # Close extractor and clean up resources
        self.extractor.close()

        # Clean up test output files (optional - leave commented for debugging)
        # import shutil
        # shutil.rmtree(self.test_output_dir)

    @patch('src.utils.http_client.HttpClient.get_content')
    def test_extract_and_categorize_workflow(self, mock_get_content):
        # Setup
        test_url = "https://example.com"
        mock_get_content.return_value = SAMPLE_HTML

        # Execute
        result = self.extractor.extract_and_categorize(test_url)

        # Assert - check that the result is the right type
        self.assertIsInstance(result, LinkCategorizationResult)

        # Verify links were categorized correctly
        self.assertEqual(len(result.pdf_links), 2)  # Two PDF links in the sample
        self.assertEqual(len(result.youtube_links), 2)  # Two YouTube links in the sample
        self.assertEqual(len(result.other_links), 3)  # Three other links in the sample

        # Check content of specific links
        pdf_urls = [link.url for link in result.pdf_links]
        self.assertIn("https://example.com/document.pdf", pdf_urls)

        youtube_urls = [link.url for link in result.youtube_links]
        self.assertIn("https://youtube.com/watch?v=abcdef", youtube_urls)

    @patch('src.extractors.web_content_extractor.WebContentExtractor.extract_and_categorize')
    def test_extract_and_export_json(self, mock_extract):
        # Setup
        mock_extract.return_value = SAMPLE_CATEGORIZATION_RESULT
        test_url = "https://example.com"

        # Execute
        file_path = self.extractor.extract_and_export(
            test_url,
            output_format="json",
            export_to_file=True
        )

        # Assert
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".json"))

        # Verify file content
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertTrue("source_url" in content)
            self.assertTrue("pdf_links" in content)
            self.assertTrue("youtube_links" in content)

    @patch('src.extractors.web_content_extractor.WebContentExtractor.extract_and_categorize')
    def test_extract_and_export_console_no_file(self, mock_extract):
        # Setup
        mock_extract.return_value = SAMPLE_CATEGORIZATION_RESULT
        test_url = "https://example.com"

        # Execute
        output = self.extractor.extract_and_export(
            test_url,
            output_format="console",
            export_to_file=False
        )

        # Assert
        self.assertIsInstance(output, str)
        self.assertTrue("Web Content Extraction Results" in output)
        self.assertTrue("PDF Links:" in output)
        self.assertTrue("YouTube Links:" in output)


if __name__ == "__main__":
    unittest.main()
