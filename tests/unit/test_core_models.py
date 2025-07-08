"""
Unit tests for core domain models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.models import (
    LinkType, ExtractedLink, ExtractionMetadata, ExtractionResult
)
from src.core.value_objects import SourceUrl, ProcessingTime, CorrelationId


class TestLinkType:
    """Test LinkType enum."""

    def test_link_type_values(self):
        """Test that LinkType has expected values."""
        assert LinkType.PDF == "pdf"
        assert LinkType.YOUTUBE == "youtube"
        assert LinkType.OTHER == "other"


class TestExtractedLink:
    """Test ExtractedLink model."""

    def test_valid_extracted_link(self):
        """Test creating a valid ExtractedLink."""
        link = ExtractedLink(
            url="https://example.com/document.pdf",
            link_text="Download PDF",
            link_type=LinkType.PDF
        )

        assert link.url == "https://example.com/document.pdf"
        assert link.link_text == "Download PDF"
        assert link.link_type == LinkType.PDF
        assert link.is_valid is True

    def test_empty_link_text_validation(self):
        """Test that empty link text raises validation error."""
        with pytest.raises(ValidationError):
            ExtractedLink(
                url="https://example.com",
                link_text="",
                link_type=LinkType.OTHER
            )

    def test_whitespace_link_text_validation(self):
        """Test that whitespace-only link text raises validation error."""
        with pytest.raises(ValidationError):
            ExtractedLink(
                url="https://example.com",
                link_text="   ",
                link_type=LinkType.OTHER
            )

    def test_link_text_stripped(self):
        """Test that link text is stripped of whitespace."""
        link = ExtractedLink(
            url="https://example.com",
            link_text="  Test Link  ",
            link_type=LinkType.OTHER
        )

        assert link.link_text == "Test Link"


class TestExtractionMetadata:
    """Test ExtractionMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid ExtractionMetadata."""
        metadata = ExtractionMetadata(
            page_title="Test Page",
            total_links_found=10,
            pdf_count=3,
            youtube_count=2,
            processing_time_seconds=1.5
        )

        assert metadata.page_title == "Test Page"
        assert metadata.total_links_found == 10
        assert metadata.pdf_count == 3
        assert metadata.youtube_count == 2
        assert metadata.processing_time_seconds == 1.5
        assert isinstance(metadata.extraction_timestamp, datetime)
        assert metadata.user_agent == "WebExtractor/1.0"

    def test_negative_counts_validation(self):
        """Test that negative counts raise validation error."""
        with pytest.raises(ValidationError):
            ExtractionMetadata(
                total_links_found=-1,
                pdf_count=0,
                youtube_count=0,
                processing_time_seconds=1.0
            )

    def test_zero_processing_time_validation(self):
        """Test that zero processing time raises validation error."""
        with pytest.raises(ValidationError):
            ExtractionMetadata(
                total_links_found=0,
                pdf_count=0,
                youtube_count=0,
                processing_time_seconds=0.0
            )


class TestExtractionResult:
    """Test ExtractionResult model."""

    def test_valid_extraction_result(self):
        """Test creating a valid ExtractionResult."""
        pdf_link = ExtractedLink.create_pdf_link(
            "https://example.com/doc.pdf",
            "PDF Document"
        )

        youtube_link = ExtractedLink.create_youtube_link(
            "https://youtube.com/watch?v=123",
            "Video Tutorial"
        )

        result = ExtractionResult(
            source_url=SourceUrl.from_string("https://example.com"),
            pdf_links=[pdf_link],
            youtube_links=[youtube_link],
            other_links=[]
        )

        assert str(result.source_url.value) == "https://example.com"
        assert len(result.pdf_links) == 1
        assert len(result.youtube_links) == 1
        assert len(result.other_links) == 0
        assert result.total_links == 2

    def test_total_links_property(self):
        """Test total_links property calculation."""
        result = ExtractionResult(
            source_url="https://example.com",
            pdf_links=[ExtractedLink(url="https://a.com", link_text="A", link_type=LinkType.PDF)],
            youtube_links=[ExtractedLink(url="https://b.com", link_text="B", link_type=LinkType.YOUTUBE)],
            other_links=[ExtractedLink(url="https://c.com", link_text="C", link_type=LinkType.OTHER)]
        )

        assert result.total_links == 3

    def test_summary_property(self):
        """Test summary property."""
        result = ExtractionResult(
            source_url="https://example.com",
            pdf_links=[ExtractedLink(url="https://a.com", link_text="A", link_type=LinkType.PDF)],
            youtube_links=[ExtractedLink(url="https://b.com", link_text="B", link_type=LinkType.YOUTUBE)],
            other_links=[ExtractedLink(url="https://c.com", link_text="C", link_type=LinkType.OTHER)]
        )

        summary = result.summary
        assert summary["total_links"] == 3
        assert summary["pdf_count"] == 1
        assert summary["youtube_count"] == 1
        assert summary["other_count"] == 1
