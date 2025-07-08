"""
Core domain models for the web content extractor.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse
import re

from pydantic import BaseModel, HttpUrl, Field, field_validator

from .value_objects import SourceUrl, ProcessingTime, CorrelationId


class LinkType(str, Enum):
    """Enumeration of supported link types"""
    PDF = "pdf"
    YOUTUBE = "youtube"
    OTHER = "other"


class ExtractedLink(BaseModel):
    """A single extracted and classified link with domain logic"""
    url: HttpUrl
    link_text: str = Field(..., min_length=1, description="Link text content")
    link_type: LinkType
    is_valid: bool = Field(default=True, description="Whether link is accessible")

    @field_validator('link_text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Link text cannot be empty')
        return v.strip()

    # Domain Methods
    def get_domain(self) -> str:
        """Extract domain name from URL."""
        return self.url.host.replace("www.", "")

    def get_file_extension(self) -> Optional[str]:
        """Extract file extension if present."""
        path = self.url.path.lower()
        if '.' in path:
            return path.split('.')[-1]
        return None

    def is_document(self) -> bool:
        """Check if link points to a document."""
        return self.link_type == LinkType.PDF

    def is_media(self) -> bool:
        """Check if link points to media content."""
        return self.link_type == LinkType.YOUTUBE

    def get_url_depth(self) -> int:
        """Calculate URL path depth."""
        path = self.url.path.strip("/")
        return len(path.split("/")) if path else 0

    # Factory Methods
    @classmethod
    def create_pdf_link(cls, url: str, text: str) -> "ExtractedLink":
        """Create PDF link with validation."""
        if not url.lower().endswith('.pdf') and 'pdf' not in url.lower():
            raise ValueError(f"URL does not appear to be a PDF: {url}")

        return cls(
            url=HttpUrl(url),
            link_text=text or "PDF Document",
            link_type=LinkType.PDF
        )

    @classmethod
    def create_youtube_link(cls, url: str, text: str) -> "ExtractedLink":
        """Create YouTube link with validation."""
        youtube_patterns = [
            r'youtube\.com/watch',
            r'youtu\.be/',
            r'youtube\.com/embed'
        ]

        if not any(re.search(pattern, url.lower()) for pattern in youtube_patterns):
            raise ValueError(f"URL does not appear to be a YouTube link: {url}")

        return cls(
            url=HttpUrl(url),
            link_text=text or "YouTube Video",
            link_type=LinkType.YOUTUBE
        )

    @classmethod
    def create_other_link(cls, url: str, text: str) -> "ExtractedLink":
        """Create generic link."""
        return cls(
            url=HttpUrl(url),
            link_text=text or url,
            link_type=LinkType.OTHER
        )


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process with business logic"""
    page_title: Optional[str] = None
    total_links_found: int = Field(..., ge=0)
    pdf_count: int = Field(..., ge=0)
    youtube_count: int = Field(..., ge=0)
    processing_time: ProcessingTime
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    user_agent: str = Field(default="WebExtractor/1.0")
    correlation_id: CorrelationId

    # Domain Methods
    def get_link_distribution(self) -> dict:
        """Get percentage distribution of link types."""
        if self.total_links_found == 0:
            return {"pdf": 0, "youtube": 0, "other": 0}

        other_count = self.total_links_found - self.pdf_count - self.youtube_count
        return {
            "pdf": round((self.pdf_count / self.total_links_found) * 100, 1),
            "youtube": round((self.youtube_count / self.total_links_found) * 100, 1),
            "other": round((other_count / self.total_links_found) * 100, 1)
        }

    def is_content_rich(self) -> bool:
        """Determine if page is content-rich (business rule)."""
        return self.total_links_found >= 10

    def get_performance_summary(self) -> dict:
        """Get performance analysis."""
        return {
            "processing_time_ms": self.processing_time.to_milliseconds(),
            "performance_category": self.processing_time.get_performance_category(),
            "is_slow": self.processing_time.is_slow(),
            "links_per_second": round(self.total_links_found / self.processing_time.seconds, 2)
        }


class ExtractionResult(BaseModel):
    """Complete result of link extraction and classification with domain logic"""
    source_url: SourceUrl
    pdf_links: List[ExtractedLink] = Field(default_factory=list)
    youtube_links: List[ExtractedLink] = Field(default_factory=list)
    other_links: List[ExtractedLink] = Field(default_factory=list)
    metadata: Optional[ExtractionMetadata] = None

    @property
    def total_links(self) -> int:
        """Total number of links across all categories"""
        return len(self.pdf_links) + len(self.youtube_links) + len(self.other_links)

    @property
    def summary(self) -> dict:
        """Summary statistics for quick overview"""
        return {
            "total_links": self.total_links,
            "pdf_count": len(self.pdf_links),
            "youtube_count": len(self.youtube_links),
            "other_count": len(self.other_links),
            "source_domain": self.source_url.get_domain(),
            "is_secure": self.source_url.is_secure()
        }

    # Domain Methods
    def get_links_by_domain(self) -> dict:
        """Group links by domain for analysis."""
        domains = {}
        for link in self.get_all_links():
            domain = link.get_domain()
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(link)
        return domains

    def get_all_links(self) -> List[ExtractedLink]:
        """Get all links regardless of type."""
        return self.pdf_links + self.youtube_links + self.other_links

    def get_document_links(self) -> List[ExtractedLink]:
        """Get all document-type links."""
        return [link for link in self.get_all_links() if link.is_document()]

    def get_media_links(self) -> List[ExtractedLink]:
        """Get all media-type links."""
        return [link for link in self.get_all_links() if link.is_media()]

    def has_content(self) -> bool:
        """Check if extraction found any content."""
        return self.total_links > 0

    def get_quality_score(self) -> float:
        """Calculate content quality score (0-100)."""
        if not self.has_content():
            return 0.0

        # Simple scoring algorithm
        base_score = min(self.total_links * 5, 50)  # Max 50 for quantity
        diversity_bonus = len(set(link.get_domain() for link in self.get_all_links())) * 5  # Max ~25 for diversity
        document_bonus = len(self.pdf_links) * 10  # Bonus for documents

        return min(base_score + diversity_bonus + document_bonus, 100.0)
