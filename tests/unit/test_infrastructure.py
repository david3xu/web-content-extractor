"""
Unit tests for infrastructure components.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.infrastructure.html_parser import BeautifulSoupLinkParser
from src.infrastructure.link_classifier import RegexLinkClassifier
from src.infrastructure.formatters import OutputFormatters, OutputFormat
from src.infrastructure.local_storage import LocalFileStorage
from src.core.models import ExtractedLink, LinkType, ExtractionResult


class TestBeautifulSoupLinkParser:
    """Test HTML link parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = BeautifulSoupLinkParser()

    def test_parse_links_basic(self):
        """Test basic link parsing."""
        html_content = """
        <html>
            <body>
                <a href="https://example.com">Example</a>
                <a href="https://test.com/document.pdf">PDF Document</a>
                <a href="https://youtube.com/watch?v=123">Video</a>
            </body>
        </html>
        """

        links = self.parser.parse_links(html_content, "https://base.com")

        assert len(links) == 3
        assert ("https://example.com", "Example") in links
        assert ("https://test.com/document.pdf", "PDF Document") in links
        assert ("https://youtube.com/watch?v=123", "Video") in links

    def test_parse_links_relative_urls(self):
        """Test parsing relative URLs."""
        html_content = '<a href="/relative/path">Relative Link</a>'

        links = self.parser.parse_links(html_content, "https://example.com")

        assert len(links) == 1
        assert links[0][0] == "https://example.com/relative/path"
        assert links[0][1] == "Relative Link"

    def test_parse_links_skip_invalid(self):
        """Test that invalid links are skipped."""
        html_content = """
        <a href="javascript:void(0)">JS Link</a>
        <a href="#fragment">Fragment</a>
        <a href="mailto:test@example.com">Email</a>
        <a href="https://valid.com">Valid</a>
        """

        links = self.parser.parse_links(html_content, "https://base.com")

        assert len(links) == 1
        assert links[0][0] == "https://valid.com"

    def test_parse_links_empty_text(self):
        """Test handling of links with empty text."""
        html_content = '<a href="https://example.com"></a>'

        links = self.parser.parse_links(html_content, "https://base.com")

        assert len(links) == 1
        assert links[0][0] == "https://example.com"
        assert links[0][1] == "https://example.com"  # Falls back to URL


class TestRegexLinkClassifier:
    """Test link classifier."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = RegexLinkClassifier()

    def test_classify_pdf_links(self):
        """Test PDF link classification."""
        links = [
            ("https://example.com/document.pdf", "PDF Document"),
            ("https://test.com/files/report.PDF", "Report"),
            ("https://docs.com/path/to/file.pdf", "Documentation")
        ]

        classified = self.classifier.classify_links(links)

        assert len(classified) == 3
        for link in classified:
            assert link.link_type == LinkType.PDF

    def test_classify_youtube_links(self):
        """Test YouTube link classification."""
        links = [
            ("https://youtube.com/watch?v=abc123", "Video"),
            ("https://youtu.be/xyz789", "Short Video"),
            ("https://youtube.com/embed/def456", "Embedded Video")
        ]

        classified = self.classifier.classify_links(links)

        assert len(classified) == 3
        for link in classified:
            assert link.link_type == LinkType.YOUTUBE

    def test_classify_other_links(self):
        """Test other link classification."""
        links = [
            ("https://example.com", "Example"),
            ("https://github.com/user/repo", "GitHub"),
            ("https://stackoverflow.com", "Stack Overflow")
        ]

        classified = self.classifier.classify_links(links)

        assert len(classified) == 3
        for link in classified:
            assert link.link_type == LinkType.OTHER

    def test_classify_mixed_links(self):
        """Test classification of mixed link types."""
        links = [
            ("https://example.com/doc.pdf", "PDF"),
            ("https://youtube.com/watch?v=123", "Video"),
            ("https://example.com", "Website")
        ]

        classified = self.classifier.classify_links(links)

        assert len(classified) == 3
        assert classified[0].link_type == LinkType.PDF
        assert classified[1].link_type == LinkType.YOUTUBE
        assert classified[2].link_type == LinkType.OTHER


class TestOutputFormatters:
    """Test output formatters."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = OutputFormatters()
        self.result = ExtractionResult(
            source_url="https://example.com",
            pdf_links=[
                ExtractedLink(url="https://example.com/doc.pdf", link_text="Document", link_type=LinkType.PDF)
            ],
            youtube_links=[
                ExtractedLink(url="https://youtube.com/watch?v=123", link_text="Video", link_type=LinkType.YOUTUBE)
            ],
            other_links=[]
        )

    def test_format_json(self):
        """Test JSON formatting."""
        formatted = self.formatter.format_result(self.result, "json")

        assert formatted.startswith("{")
        assert formatted.endswith("}")
        assert "source_url" in formatted
        assert "pdf_links" in formatted

    def test_format_text(self):
        """Test text formatting."""
        formatted = self.formatter.format_result(self.result, "text")

        assert "Extraction Results for: https://example.com" in formatted
        assert "PDF Links (1):" in formatted
        assert "YouTube Links (1):" in formatted
        assert "Document: https://example.com/doc.pdf" in formatted

    def test_format_markdown(self):
        """Test markdown formatting."""
        formatted = self.formatter.format_result(self.result, "markdown")

        assert "# Extraction Results for: https://example.com" in formatted
        assert "## PDF Links (1)" in formatted
        assert "## YouTube Links (1)" in formatted
        assert "[Document](https://example.com/doc.pdf)" in formatted

    def test_format_csv(self):
        """Test CSV formatting."""
        formatted = self.formatter.format_result(self.result, "csv")

        lines = formatted.split("\n")
        assert lines[0] == "Type,Text,URL"
        assert "PDF,\"Document\",https://example.com/doc.pdf" in lines
        assert "YouTube,\"Video\",https://youtube.com/watch?v=123" in lines

    def test_unsupported_format(self):
        """Test handling of unsupported format."""
        with pytest.raises(Exception):
            self.formatter.format_result(self.result, "unsupported")


class TestLocalFileStorage:
    """Test local file storage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path("/tmp/test_output")
        self.storage = LocalFileStorage(self.temp_dir)

    @pytest.mark.asyncio
    async def test_save_result(self):
        """Test saving result to file."""
        result = ExtractionResult(
            source_url="https://example.com",
            pdf_links=[],
            youtube_links=[],
            other_links=[]
        )

        # Mock the file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            file_path = await self.storage.save_result(result, "test.json")

            assert file_path.endswith("test.json")
            mock_file.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_result_auto_filename(self):
        """Test saving result with auto-generated filename."""
        result = ExtractionResult(
            source_url="https://example.com",
            pdf_links=[],
            youtube_links=[],
            other_links=[]
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            file_path = await self.storage.save_result(result)

            assert file_path.endswith(".json")
            assert "extraction_example_" in file_path
