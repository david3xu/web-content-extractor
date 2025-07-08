"""
Unit tests for core domain models.
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.core.models import (
    ExtractedLink,
    ExtractionMetadata,
    ExtractionResult,
    LinkType,
)
from src.core.value_objects import CorrelationId, ProcessingTime, SourceUrl


class TestLinkType:
    """Test LinkType enum."""

    def test_link_type_values(self) -> None:
        """Test that LinkType has expected values."""
        assert LinkType.PDF.value == "pdf"
        assert LinkType.YOUTUBE.value == "youtube"
        assert LinkType.OTHER.value == "other"


class TestExtractedLink:
    """Test ExtractedLink model."""

    def test_valid_extracted_link(self) -> None:
        """Test creating a valid ExtractedLink."""
        link = ExtractedLink(
            url="https://example.com/document.pdf",
            link_text="Download PDF",
            link_type=LinkType.PDF,
        )

        assert str(link.url) == "https://example.com/document.pdf"
        assert link.link_text == "Download PDF"
        assert link.link_type == LinkType.PDF
        assert link.is_valid is True

    def test_empty_link_text_validation(self) -> None:
        """Test that empty link text raises validation error."""
        with pytest.raises(ValidationError):
            ExtractedLink(
                url="https://example.com", link_text="", link_type=LinkType.OTHER
            )

    def test_whitespace_link_text_validation(self) -> None:
        """Test that whitespace-only link text raises validation error."""
        with pytest.raises(ValidationError):
            ExtractedLink(
                url="https://example.com", link_text="   ", link_type=LinkType.OTHER
            )

    def test_link_text_stripped(self) -> None:
        """Test that link text is stripped of whitespace."""
        link = ExtractedLink(
            url="https://example.com",
            link_text="  Test Link  ",
            link_type=LinkType.OTHER,
        )

        assert link.link_text == "Test Link"


class TestExtractionMetadata:
    """Test ExtractionMetadata model."""

    def test_valid_metadata(self) -> None:
        """Test creating valid ExtractionMetadata."""
        metadata = ExtractionMetadata(
            page_title="Test Page",
            total_links_found=10,
            pdf_count=3,
            youtube_count=2,
            processing_time=ProcessingTime(seconds=1.5),
            correlation_id=CorrelationId.generate(),
        )

        assert metadata.page_title == "Test Page"
        assert metadata.total_links_found == 10
        assert metadata.pdf_count == 3
        assert metadata.youtube_count == 2
        assert metadata.processing_time.seconds == 1.5
        assert isinstance(metadata.extraction_timestamp, datetime)
        assert metadata.user_agent == "WebExtractor/1.0"
        assert isinstance(metadata.correlation_id, CorrelationId)

    def test_negative_counts_validation(self) -> None:
        """Test that negative counts raise validation error."""
        with pytest.raises(ValidationError):
            ExtractionMetadata(
                total_links_found=-1,
                pdf_count=0,
                youtube_count=0,
                processing_time=ProcessingTime(seconds=1.0),
                correlation_id=CorrelationId.generate(),
            )

    def test_zero_processing_time_validation(self) -> None:
        """Test that zero processing time raises validation error."""
        with pytest.raises(ValueError, match="Processing time must be positive"):
            ExtractionMetadata(
                total_links_found=0,
                pdf_count=0,
                youtube_count=0,
                processing_time=ProcessingTime(seconds=0.0),
                correlation_id=CorrelationId.generate(),
            )


class TestExtractionResult:
    """Test ExtractionResult model."""

    def test_valid_extracted_link(self) -> None:
        """Test creating a valid ExtractedLink."""
        link = ExtractedLink(
            url="https://example.com/document.pdf",
            link_text="Download PDF",
            link_type=LinkType.PDF,
        )

        assert str(link.url) == "https://example.com/document.pdf"
        assert link.link_text == "Download PDF"
        assert link.link_type == LinkType.PDF
        assert link.is_valid is True

    def test_valid_extraction_result(self) -> None:
        """Test creating a valid ExtractionResult."""
        pdf_link = ExtractedLink.create_pdf_link(
            "https://example.com/doc.pdf", "PDF Document"
        )

        youtube_link = ExtractedLink.create_youtube_link(
            "https://youtube.com/watch?v=123", "Video Tutorial"
        )

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[pdf_link],
            youtube_links=[youtube_link],
            other_links=[],
        )

        assert str(result.source_url.value) == "https://example.com/"
        assert len(result.pdf_links) == 1
        assert len(result.youtube_links) == 1
        assert len(result.other_links) == 0
        assert result.total_links == 2

    def test_total_links_property(self) -> None:
        """Test total_links property calculation."""
        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[
                ExtractedLink(
                    url="https://a.com", link_text="A", link_type=LinkType.PDF
                )
            ],
            youtube_links=[
                ExtractedLink(
                    url="https://b.com", link_text="B", link_type=LinkType.YOUTUBE
                )
            ],
            other_links=[
                ExtractedLink(
                    url="https://c.com", link_text="C", link_type=LinkType.OTHER
                )
            ],
        )

        assert result.total_links == 3

    def test_summary_property(self) -> None:
        """Test summary property."""
        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[
                ExtractedLink(
                    url="https://a.com", link_text="A", link_type=LinkType.PDF
                )
            ],
            youtube_links=[
                ExtractedLink(
                    url="https://b.com", link_text="B", link_type=LinkType.YOUTUBE
                )
            ],
            other_links=[
                ExtractedLink(
                    url="https://c.com", link_text="C", link_type=LinkType.OTHER
                )
            ],
        )

        summary = result.summary
        assert summary["total_links"] == 3
        assert summary["pdf_count"] == 1
        assert summary["youtube_count"] == 1
        assert summary["other_count"] == 1
        assert summary["source_domain"] == "example.com"
        assert summary["is_secure"] is True

    def test_get_links_by_domain(self) -> None:
        """Test grouping links by domain."""
        link1 = ExtractedLink.create_other_link("https://example.com/page1", "Page 1")
        link2 = ExtractedLink.create_other_link(
            "https://sub.example.com/page2", "Page 2"
        )
        link3 = ExtractedLink.create_other_link(
            "https://anothersite.com", "Another Site"
        )

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://original.com"),
            other_links=[link1, link2, link3],
        )

        domains = result.get_links_by_domain()

        assert len(domains) == 3
        assert "example.com" in domains
        assert "sub.example.com" in domains
        assert "anothersite.com" in domains
        assert len(domains["example.com"]) == 1
        assert len(domains["sub.example.com"]) == 1
        assert len(domains["anothersite.com"]) == 1

    def test_get_all_links(self) -> None:
        """Test getting all links."""
        pdf_link = ExtractedLink.create_pdf_link("https://a.com/doc.pdf", "Doc")
        youtube_link = ExtractedLink.create_youtube_link(
            "https://youtube.com/watch?v=1", "Video"
        )
        other_link = ExtractedLink.create_other_link("https://b.com", "Site")

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[pdf_link],
            youtube_links=[youtube_link],
            other_links=[other_link],
        )

        all_links = result.get_all_links()
        assert len(all_links) == 3
        assert pdf_link in all_links
        assert youtube_link in all_links
        assert other_link in all_links

    def test_get_document_links(self) -> None:
        """Test getting document links."""
        pdf_link = ExtractedLink.create_pdf_link("https://a.com/doc.pdf", "Doc")
        other_link = ExtractedLink.create_other_link("https://b.com", "Site")

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[pdf_link],
            other_links=[other_link],
        )

        doc_links = result.get_document_links()
        assert len(doc_links) == 1
        assert pdf_link in doc_links
        assert other_link not in doc_links

    def test_get_media_links(self) -> None:
        """Test getting media links."""
        youtube_link = ExtractedLink.create_youtube_link(
            "https://youtube.com/watch?v=1", "Video"
        )
        other_link = ExtractedLink.create_other_link("https://b.com", "Site")

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            youtube_links=[youtube_link],
            other_links=[other_link],
        )

        media_links = result.get_media_links()
        assert len(media_links) == 1
        assert youtube_link in media_links
        assert other_link not in media_links

    def test_has_content(self) -> None:
        """Test has_content property."""
        result_with_content = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[
                ExtractedLink(
                    url="https://a.com", link_text="A", link_type=LinkType.PDF
                )
            ],
        )
        result_no_content = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com")
        )

        assert result_with_content.has_content() is True
        assert result_no_content.has_content() is False

    def test_get_quality_score(self) -> None:
        """Test quality score calculation."""
        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[
                ExtractedLink(
                    url="https://a.com", link_text="A", link_type=LinkType.PDF
                )
            ],
            youtube_links=[
                ExtractedLink(
                    url="https://b.com", link_text="B", link_type=LinkType.YOUTUBE
                )
            ],
            other_links=[
                ExtractedLink(
                    url="https://c.com", link_text="C", link_type=LinkType.OTHER
                )
            ],
        )

        assert result.get_quality_score() > 0

    def test_get_quality_score_no_content(self) -> None:
        """Test quality score with no content."""
        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com")
        )
        assert result.get_quality_score() == 0.0
