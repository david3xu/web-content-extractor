"""
Unit tests for enhanced domain models.
"""
import pytest
from pydantic import HttpUrl
from datetime import datetime

from src.core.models import ExtractedLink, LinkType, ExtractionMetadata, ExtractionResult
from src.core.value_objects import SourceUrl, ProcessingTime, CorrelationId


class TestExtractedLink:
    """Test enhanced ExtractedLink model."""

    def test_domain_methods(self):
        """Test domain method functionality."""
        link = ExtractedLink(
            url=HttpUrl("https://example.com/document.pdf"),
            link_text="Test PDF",
            link_type=LinkType.PDF
        )

        assert link.get_domain() == "example.com"
        assert link.get_file_extension() == "pdf"
        assert link.is_document() is True
        assert link.is_media() is False
        assert link.get_url_depth() == 1

    def test_pdf_factory(self):
        """Test PDF link factory method."""
        link = ExtractedLink.create_pdf_link(
            "https://example.com/doc.pdf",
            "Test Document"
        )

        assert link.link_type == LinkType.PDF
        assert link.link_text == "Test Document"
        assert link.url == HttpUrl("https://example.com/doc.pdf")

    def test_pdf_factory_with_pdf_in_url(self):
        """Test PDF factory with 'pdf' in URL path."""
        link = ExtractedLink.create_pdf_link(
            "https://example.com/files/pdf/document",
            "Test Document"
        )

        assert link.link_type == LinkType.PDF

    def test_youtube_factory(self):
        """Test YouTube link factory method."""
        link = ExtractedLink.create_youtube_link(
            "https://youtube.com/watch?v=123",
            "Test Video"
        )

        assert link.link_type == LinkType.YOUTUBE
        assert link.link_text == "Test Video"
        assert link.url == HttpUrl("https://youtube.com/watch?v=123")

    def test_youtube_factory_short_url(self):
        """Test YouTube factory with short URL."""
        link = ExtractedLink.create_youtube_link(
            "https://youtu.be/xyz789",
            "Test Video"
        )

        assert link.link_type == LinkType.YOUTUBE

    def test_youtube_factory_embed_url(self):
        """Test YouTube factory with embed URL."""
        link = ExtractedLink.create_youtube_link(
            "https://youtube.com/embed/def456",
            "Test Video"
        )

        assert link.link_type == LinkType.YOUTUBE

    def test_other_factory(self):
        """Test generic link factory method."""
        link = ExtractedLink.create_other_link(
            "https://example.com/page",
            "Test Page"
        )

        assert link.link_type == LinkType.OTHER
        assert link.link_text == "Test Page"

    def test_other_factory_default_text(self):
        """Test generic link factory with default text."""
        link = ExtractedLink.create_other_link(
            "https://example.com/page",
            ""
        )

        assert link.link_type == LinkType.OTHER
        assert link.link_text == "https://example.com/page"

    def test_invalid_pdf_factory(self):
        """Test PDF factory with invalid URL."""
        with pytest.raises(ValueError, match="URL does not appear to be a PDF"):
            ExtractedLink.create_pdf_link(
                "https://example.com/notapdf.html",
                "Not a PDF"
            )

    def test_invalid_youtube_factory(self):
        """Test YouTube factory with invalid URL."""
        with pytest.raises(ValueError, match="URL does not appear to be a YouTube link"):
            ExtractedLink.create_youtube_link(
                "https://example.com/video",
                "Not YouTube"
            )

    def test_media_detection(self):
        """Test media link detection."""
        youtube_link = ExtractedLink(
            url=HttpUrl("https://youtube.com/watch?v=123"),
            link_text="Video",
            link_type=LinkType.YOUTUBE
        )

        assert youtube_link.is_media() is True
        assert youtube_link.is_document() is False

    def test_url_depth_calculation(self):
        """Test URL depth calculation."""
        shallow_link = ExtractedLink(
            url=HttpUrl("https://example.com"),
            link_text="Home",
            link_type=LinkType.OTHER
        )

        deep_link = ExtractedLink(
            url=HttpUrl("https://example.com/path/to/deep/resource"),
            link_text="Deep",
            link_type=LinkType.OTHER
        )

        assert shallow_link.get_url_depth() == 0
        assert deep_link.get_url_depth() == 4


class TestExtractionMetadata:
    """Test enhanced ExtractionMetadata model."""

    def test_link_distribution(self):
        """Test link distribution calculation."""
        processing_time = ProcessingTime(2.5)
        correlation_id = CorrelationId.generate()

        metadata = ExtractionMetadata(
            total_links_found=20,
            pdf_count=8,
            youtube_count=4,
            processing_time=processing_time,
            correlation_id=correlation_id
        )

        distribution = metadata.get_link_distribution()
        assert distribution["pdf"] == 40.0  # 8/20 * 100
        assert distribution["youtube"] == 20.0  # 4/20 * 100
        assert distribution["other"] == 40.0  # 8/20 * 100

    def test_link_distribution_zero_links(self):
        """Test link distribution with no links."""
        processing_time = ProcessingTime(1.0)
        correlation_id = CorrelationId.generate()

        metadata = ExtractionMetadata(
            total_links_found=0,
            pdf_count=0,
            youtube_count=0,
            processing_time=processing_time,
            correlation_id=correlation_id
        )

        distribution = metadata.get_link_distribution()
        assert distribution["pdf"] == 0
        assert distribution["youtube"] == 0
        assert distribution["other"] == 0

    def test_content_rich_detection(self):
        """Test content-rich page detection."""
        processing_time = ProcessingTime(1.0)
        correlation_id = CorrelationId.generate()

        # Rich content
        rich_metadata = ExtractionMetadata(
            total_links_found=15,
            pdf_count=5,
            youtube_count=3,
            processing_time=processing_time,
            correlation_id=correlation_id
        )

        # Poor content
        poor_metadata = ExtractionMetadata(
            total_links_found=5,
            pdf_count=1,
            youtube_count=1,
            processing_time=processing_time,
            correlation_id=correlation_id
        )

        assert rich_metadata.is_content_rich() is True
        assert poor_metadata.is_content_rich() is False

    def test_performance_summary(self):
        """Test performance summary generation."""
        processing_time = ProcessingTime(2.5)
        correlation_id = CorrelationId.generate()

        metadata = ExtractionMetadata(
            total_links_found=10,
            pdf_count=3,
            youtube_count=2,
            processing_time=processing_time,
            correlation_id=correlation_id
        )

        summary = metadata.get_performance_summary()
        assert summary["processing_time_ms"] == 2500
        assert summary["performance_category"] == "normal"
        assert summary["is_slow"] is False
        assert summary["links_per_second"] == 4.0  # 10/2.5


class TestExtractionResult:
    """Test enhanced ExtractionResult model."""

    def test_domain_methods(self):
        """Test domain method functionality."""
        source_url = SourceUrl.from_string("https://example.com")
        pdf_link = ExtractedLink.create_pdf_link("https://docs.example.com/doc.pdf", "PDF")
        youtube_link = ExtractedLink.create_youtube_link("https://youtube.com/watch?v=123", "Video")
        other_link = ExtractedLink.create_other_link("https://other.com/page", "Page")

        result = ExtractionResult(
            source_url=source_url,
            pdf_links=[pdf_link],
            youtube_links=[youtube_link],
            other_links=[other_link]
        )

        assert result.total_links == 3
        assert result.has_content() is True
        assert result.get_quality_score() > 0
        assert len(result.get_all_links()) == 3
        assert len(result.get_document_links()) == 1
        assert len(result.get_media_links()) == 1

    def test_links_by_domain(self):
        """Test grouping links by domain."""
        source_url = SourceUrl.from_string("https://example.com")
        link1 = ExtractedLink.create_pdf_link("https://docs.example.com/doc1.pdf", "PDF1")
        link2 = ExtractedLink.create_pdf_link("https://docs.example.com/doc2.pdf", "PDF2")
        link3 = ExtractedLink.create_other_link("https://other.com/page", "Page")

        result = ExtractionResult(
            source_url=source_url,
            pdf_links=[link1, link2],
            other_links=[link3]
        )

        domains = result.get_links_by_domain()
        assert len(domains["docs.example.com"]) == 2
        assert len(domains["other.com"]) == 1

    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        source_url = SourceUrl.from_string("https://example.com")

        # High quality result
        high_quality_links = [
            ExtractedLink.create_pdf_link("https://docs1.com/doc1.pdf", "PDF1"),
            ExtractedLink.create_pdf_link("https://docs2.com/doc2.pdf", "PDF2"),
            ExtractedLink.create_youtube_link("https://youtube.com/watch?v=123", "Video"),
            ExtractedLink.create_other_link("https://other.com/page", "Page")
        ]

        result = ExtractionResult(
            source_url=source_url,
            pdf_links=high_quality_links[:2],
            youtube_links=[high_quality_links[2]],
            other_links=[high_quality_links[3]]
        )

        score = result.get_quality_score()
        assert score > 50  # Should be high due to multiple PDFs and diversity

    def test_empty_result(self):
        """Test empty extraction result."""
        source_url = SourceUrl.from_string("https://example.com")
        result = ExtractionResult(source_url=source_url)

        assert result.total_links == 0
        assert result.has_content() is False
        assert result.get_quality_score() == 0.0
        assert len(result.get_all_links()) == 0

    def test_summary_properties(self):
        """Test summary property generation."""
        source_url = SourceUrl.from_string("https://secure.example.com")
        pdf_link = ExtractedLink.create_pdf_link("https://docs.com/doc.pdf", "PDF")

        result = ExtractionResult(
            source_url=source_url,
            pdf_links=[pdf_link]
        )

        summary = result.summary
        assert summary["total_links"] == 1
        assert summary["pdf_count"] == 1
        assert summary["youtube_count"] == 0
        assert summary["other_count"] == 0
        assert summary["source_domain"] == "secure.example.com"
        assert summary["is_secure"] is True
