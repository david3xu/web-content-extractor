"""
Unit tests for enhanced domain models.
"""

import pytest
from pydantic import ValidationError

from src.core.models import ExtractedLink, LinkType


class TestExtractedLink:
    def test_basic_link_creation(self) -> None:
        link = ExtractedLink.create_other_link(
            "https://example.com/page", "Example Page"
        )
        assert isinstance(link, ExtractedLink)
        assert str(link.url) == "https://example.com/page"
        assert link.link_text == "Example Page"
        assert link.link_type == LinkType.OTHER

    def test_pdf_factory_valid_url(self) -> None:
        link = ExtractedLink.create_pdf_link(
            "https://example.com/document.pdf", "Download Document"
        )
        assert isinstance(link, ExtractedLink)
        assert str(link.url) == "https://example.com/document.pdf"
        assert link.link_text == "Download Document"
        assert link.link_type == LinkType.PDF

    def test_youtube_factory_valid_url(self) -> None:
        link = ExtractedLink.create_youtube_link(
            "https://www.youtube.com/watch?v=123", "Watch Video"
        )
        assert isinstance(link, ExtractedLink)
        assert str(link.url) == "https://www.youtube.com/watch?v=123"
        assert link.link_text == "Watch Video"
        assert link.link_type == LinkType.YOUTUBE

    def test_link_text_strip(self) -> None:
        link = ExtractedLink.create_other_link("https://example.com", "  Padded Text  ")
        assert link.link_text == "Padded Text"

    def test_link_text_empty_falls_back_to_url(self) -> None:
        link = ExtractedLink.create_other_link("https://example.com/other", "")
        assert link.link_text == "https://example.com/other"

    def test_link_text_none_falls_back_to_url(self) -> None:
        link = ExtractedLink.create_other_link("https://example.com/other", None)  # type: ignore
        assert link.link_text == "https://example.com/other"

    def test_get_domain(self) -> None:
        link = ExtractedLink.create_other_link(
            "https://www.sub.example.com/path", "Subdomain Link"
        )
        assert link.get_domain() == "sub.example.com"

        link_no_www = ExtractedLink.create_other_link(
            "https://example.com/path", "Domain Link"
        )
        assert link_no_www.get_domain() == "example.com"

    def test_get_file_extension(self) -> None:
        link_pdf = ExtractedLink.create_other_link("https://example.com/doc.pdf", "PDF")
        assert link_pdf.get_file_extension() == "pdf"

        link_no_ext = ExtractedLink.create_other_link(
            "https://example.com/page", "Page"
        )
        assert link_no_ext.get_file_extension() is None

    def test_is_document(self) -> None:
        link_pdf = ExtractedLink.create_pdf_link("https://example.com/doc.pdf", "PDF")
        assert link_pdf.is_document() is True

        link_other = ExtractedLink.create_other_link("https://example.com/page", "Page")
        assert link_other.is_document() is False

    def test_is_media(self) -> None:
        link_youtube = ExtractedLink.create_youtube_link(
            "https://www.youtube.com/watch?v=123", "Video"
        )
        assert link_youtube.is_media() is True

        link_other = ExtractedLink.create_other_link("https://example.com/page", "Page")
        assert link_other.is_media() is False

    def test_get_url_depth(self) -> None:
        link_root = ExtractedLink.create_other_link("https://example.com", "Root")
        assert link_root.get_url_depth() == 0

        link_single_depth = ExtractedLink.create_other_link(
            "https://example.com/path1", "Depth 1"
        )
        assert link_single_depth.get_url_depth() == 1

        link_multi_depth = ExtractedLink.create_other_link(
            "https://example.com/path1/path2/path3", "Depth 3"
        )
        assert link_multi_depth.get_url_depth() == 3

    def test_invalid_url_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ExtractedLink.create_other_link("invalid-url", "Invalid")


# NOTE: TestExtractedLink has been updated to remove specific factory validation tests.
# Validation of URL patterns for PDF/YouTube is now handled by the LinkClassifier.
# The factory methods in ExtractedLink now focus on creating the object given a URL and text.
