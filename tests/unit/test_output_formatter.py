import unittest
import os
import json
import tempfile
from pathlib import Path
from src.extractors.output_formatter import OutputFormatterService
from src.models.exceptions import OutputFormattingError
from ..fixtures.sample_data import SAMPLE_CATEGORIZATION_RESULT


class TestOutputFormatterService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

        # Create formatter instance
        self.formatter = OutputFormatterService(str(self.output_dir))

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_generate_json_report(self):
        # Generate JSON report
        json_output = self.formatter.generate_json_report(SAMPLE_CATEGORIZATION_RESULT)

        # Verify it's valid JSON
        parsed_json = json.loads(json_output)

        # Check for expected keys
        self.assertIn("source_url", parsed_json)
        self.assertIn("pdf_links", parsed_json)
        self.assertIn("youtube_links", parsed_json)
        self.assertIn("other_links", parsed_json)

        # Check content
        self.assertEqual(parsed_json["source_url"], "https://example.com")
        self.assertEqual(len(parsed_json["pdf_links"]), 2)
        self.assertEqual(len(parsed_json["youtube_links"]), 2)

    def test_generate_console_output(self):
        # Generate console output
        console_output = self.formatter.generate_console_output(SAMPLE_CATEGORIZATION_RESULT)

        # Verify output contains expected sections
        self.assertIn("Web Content Extraction Results", console_output)
        self.assertIn("Source URL: https://example.com", console_output)
        self.assertIn("PDF Links:", console_output)
        self.assertIn("YouTube Links:", console_output)

        # Verify PDF links are included
        for pdf_link in SAMPLE_CATEGORIZATION_RESULT.pdf_links:
            self.assertIn(pdf_link.url, console_output)

    def test_export_to_file(self):
        # Test content to export
        test_content = "Test content for file export"

        # Export to file
        file_path = self.formatter.export_to_file(
            test_content,
            "test_export",
            "txt"
        )

        # Verify file exists
        self.assertTrue(os.path.exists(file_path))

        # Verify file content
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertEqual(content, test_content)

    def test_link_to_dict(self):
        # Test with sample link
        sample_link = SAMPLE_CATEGORIZATION_RESULT.pdf_links[0]
        link_dict = self.formatter._link_to_dict(sample_link)

        # Verify dictionary structure
        self.assertIn("url", link_dict)
        self.assertIn("text", link_dict)
        self.assertIn("type", link_dict)
        self.assertIn("is_valid", link_dict)

        # Verify values
        self.assertEqual(link_dict["url"], sample_link.url)
        self.assertEqual(link_dict["text"], sample_link.link_text)
        self.assertEqual(link_dict["type"], sample_link.link_type.value)

    def test_metadata_to_dict(self):
        # Test with sample metadata
        metadata_dict = self.formatter._metadata_to_dict(SAMPLE_CATEGORIZATION_RESULT.metadata)

        # Verify dictionary structure
        self.assertIn("total_links_found", metadata_dict)
        self.assertIn("pdf_count", metadata_dict)
        self.assertIn("youtube_count", metadata_dict)
        self.assertIn("processing_time_seconds", metadata_dict)
        self.assertIn("page_title", metadata_dict)
        self.assertIn("extraction_timestamp", metadata_dict)

        # Verify values
        self.assertEqual(metadata_dict["total_links_found"],
                         SAMPLE_CATEGORIZATION_RESULT.metadata.total_links_found)
        self.assertEqual(metadata_dict["pdf_count"],
                         SAMPLE_CATEGORIZATION_RESULT.metadata.pdf_count)


if __name__ == "__main__":
    unittest.main()
