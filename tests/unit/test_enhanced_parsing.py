import pytest
from bs4 import BeautifulSoup

from src.infrastructure.html_parser import BeautifulSoupLinkParser
from src.infrastructure.context_classifier import ContextAwareClassifier
from src.core.models import LinkType, ExtractedLink

class TestEnhancedLinkParsing:
    @pytest.fixture
    def parser(self) -> BeautifulSoupLinkParser:
        return BeautifulSoupLinkParser()

    def test_extract_iframe_sources(self, parser: BeautifulSoupLinkParser) -> None:
        html_content = """
        <html>
        <body>
            <iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" width="560" height="315" frameborder="0" allowfullscreen></iframe>
            <iframe src="https://player.vimeo.com/video/12345" width="640" height="360" frameborder="0" allowfullscreen></iframe>
            <iframe src="/local/path/to/embed.html"></iframe>
        </body>
        </html>
        """
        base_url = "https://example.com"
        extracted_links = parser._extract_iframe_sources(BeautifulSoup(html_content, "html.parser"), base_url)
        assert len(extracted_links) == 3 # Should now extract local embed as well
        assert ("https://www.youtube.com/embed/dQw4w9WgXcQ", "https://www.youtube.com/embed/dQw4w9WgXcQ") in extracted_links
        assert ("https://player.vimeo.com/video/12345", "https://player.vimeo.com/video/12345") in extracted_links
        assert ("https://example.com/local/path/to/embed.html", "https://example.com/local/path/to/embed.html") in extracted_links

    def test_extract_embedded_objects(self, parser: BeautifulSoupLinkParser) -> None:
        html_content = """
        <html>
        <body>
            <object data="document.pdf" type="application/pdf" width="600" height="400"></object>
            <embed src="presentation.ppt" type="application/vnd.ms-powerpoint" width="500" height="300">
            <a href="report.pdf">Download Report</a>
            <a href="data.zip">Download Data</a>
        </body>
        </html>
        """
        base_url = "https://example.com/files/"
        extracted_links = parser._extract_embedded_objects(BeautifulSoup(html_content, "html.parser"), base_url)
        assert len(extracted_links) == 2
        assert ("https://example.com/files/document.pdf", "https://example.com/files/document.pdf") in extracted_links
        assert ("https://example.com/files/presentation.ppt", "https://example.com/files/presentation.ppt") in extracted_links

class TestEnhancedLinkClassification:
    @pytest.fixture
    def classifier(self) -> ContextAwareClassifier:
        return ContextAwareClassifier()

    def test_pdf_pattern_enhancement(self, classifier: ContextAwareClassifier) -> None:
        links = [
            ("https://example.com/document.pdf?version=1", "document.pdf"),
            ("https://example.com/report.PDF#page=1", "report.PDF"),
            ("https://example.com/download.php?file=my_doc.pdf", "Download PDF"),
            ("https://example.com/image.jpg", "image.jpg"),
            ("https://example.com/report-3MB.pdf", "3MB pdf report"),  # Test context-aware classification
        ]
        classified_links = classifier.classify_links(links)
        pdf_links = [link for link in classified_links if link.link_type == LinkType.PDF]
        other_links = [link for link in classified_links if link.link_type == LinkType.OTHER]

        assert len(pdf_links) == 4  # Expected 4 PDF links
        assert len(other_links) == 1  # Expected 1 other link

        # Assert specific URLs/texts that should be classified as PDF
        pdf_urls_or_texts = [
            "https://example.com/document.pdf?version=1",
            "https://example.com/report.PDF#page=1",
            "https://example.com/download.php?file=my_doc.pdf",
            "3MB pdf report", # This is based on text content
        ]
        for link in pdf_links:
            assert str(link.url) in pdf_urls_or_texts or link.link_text in pdf_urls_or_texts


    def test_youtube_pattern_enhancement(self, classifier: ContextAwareClassifier) -> None:
        links = [
            ("https://www.youtube.com/watch?v=123", "YouTube Video 1"),
            ("https://youtu.be/456", "YouTube Short"),
            ("https://www.youtube.com/embed/789", "Embedded YouTube"),
            ("https://www.youtube-nocookie.com/embed/abc", "No Cookie Video"),
            ("https://vimeo.com/123", "Vimeo Video"),
            ("https://example.com/video.html", "watch this youtube video"),  # Test context-aware classification
        ]
        classified_links = classifier.classify_links(links)
        youtube_links = [link for link in classified_links if link.link_type == LinkType.YOUTUBE]
        other_links = [link for link in classified_links if link.link_type == LinkType.OTHER]

        assert len(youtube_links) == 5  # Expected 5 YouTube links
        assert len(other_links) == 1  # Expected 1 other link

        # Assert specific URLs/texts that should be classified as YouTube
        youtube_urls_or_texts = [
            "https://www.youtube.com/watch?v=123",
            "https://youtu.be/456",
            "https://www.youtube.com/embed/789",
            "https://www.youtube-nocookie.com/embed/abc",
            "watch this youtube video", # This is based on text content
        ]
        for link in youtube_links:
            assert str(link.url) in youtube_urls_or_texts or link.link_text in youtube_urls_or_texts
