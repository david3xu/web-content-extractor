import pytest

from src.core.models import LinkType
from src.infrastructure.html_parser import BeautifulSoupLinkParser
from src.infrastructure.link_classifier import RegexLinkClassifier


class TestEnhancedLinkParsing:
    @pytest.fixture  # type: ignore[misc]
    def parser(self) -> BeautifulSoupLinkParser:
        return BeautifulSoupLinkParser()

    @pytest.fixture  # type: ignore[misc]
    def classifier(self) -> RegexLinkClassifier:
        return RegexLinkClassifier()

    def test_parse_links_combines_all_types(
        self, parser: BeautifulSoupLinkParser
    ) -> None:
        html_content = """
        <html>
        <body>
            <a href="/regular-link">Regular Link</a>
            <a href="/download.pdf" download>Download PDF</a>
            <iframe src="https://www.youtube.com/embed/somevideo"></iframe>
            <img src="image.jpg">
        </body>
        </html>
        """
        base_url = "https://example.com"
        links = parser.parse_links(html_content, base_url)
        assert len(links) == 3
        assert ("https://example.com/regular-link", "Regular Link") in links
        assert ("https://example.com/download.pdf", "Download PDF") in links
        assert (
            "https://www.youtube.com/embed/somevideo",
            "Embedded Video Content",
        ) in links

    def test_parse_links_with_no_links(self, parser: BeautifulSoupLinkParser) -> None:
        html_content = "<html><body>No links here.</body></html>"
        base_url = "https://example.com"
        links = parser.parse_links(html_content, base_url)
        assert len(links) == 0

    def test_parse_links_with_invalid_urls(
        self, parser: BeautifulSoupLinkParser
    ) -> None:
        html_content = (
            '<a href="javascript:void(0)">JS Link</a><a href="#anchor">Anchor</a>'
        )
        base_url = "https://example.com"
        links = parser.parse_links(html_content, base_url)
        assert len(links) == 0

    def test_classify_links_with_various_types(
        self, classifier: RegexLinkClassifier
    ) -> None:
        links_to_classify = [
            ("https://example.com/document.pdf", "Download PDF"),
            ("https://www.youtube.com/watch?v=123", "Watch Video"),
            ("https://example.com/page", "Visit Page"),
            ("https://cdn.iframe.ly/video123", "Embedded Video"),
            ("https://files.gitbook.io/document.pdf", "Read Document"),
        ]
        classified = classifier.classify_links(links_to_classify)

        assert len(classified) == 5

        pdf_links = [link for link in classified if link.link_type == LinkType.PDF]
        youtube_links = [
            link for link in classified if link.link_type == LinkType.YOUTUBE
        ]
        other_links = [link for link in classified if link.link_type == LinkType.OTHER]

        assert len(pdf_links) == 2
        assert any(
            str(link.url) == "https://example.com/document.pdf" for link in pdf_links
        )
        assert any(
            str(link.url) == "https://files.gitbook.io/document.pdf"
            for link in pdf_links
        )

        assert len(youtube_links) == 2
        assert any(
            str(link.url) == "https://www.youtube.com/watch?v=123"
            for link in youtube_links
        )
        assert any(
            str(link.url) == "https://cdn.iframe.ly/video123" for link in youtube_links
        )

        assert len(other_links) == 1
        assert any(str(link.url) == "https://example.com/page" for link in other_links)

    def test_classify_links_empty_list(self, classifier: RegexLinkClassifier) -> None:
        classified = classifier.classify_links([])
        assert len(classified) == 0

    def test_classify_links_invalid_url_handling(
        self, classifier: RegexLinkClassifier
    ) -> None:
        links_to_classify = [("invalid-url", "Invalid")]
        classified = classifier.classify_links(links_to_classify)
        assert len(classified) == 0  # Should now be 0 as invalid links are skipped
