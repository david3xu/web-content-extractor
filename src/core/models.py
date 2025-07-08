"""
Core domain models for the web content extractor.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field, field_validator


class LinkType(str, Enum):
    """Enumeration of supported link types"""
    PDF = "pdf"
    YOUTUBE = "youtube"
    OTHER = "other"


class ExtractedLink(BaseModel):
    """A single extracted and classified link"""
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


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    page_title: Optional[str] = None
    total_links_found: int = Field(..., ge=0)
    pdf_count: int = Field(..., ge=0)
    youtube_count: int = Field(..., ge=0)
    processing_time_seconds: float = Field(..., gt=0)
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    user_agent: str = Field(default="WebExtractor/1.0")


class ExtractionResult(BaseModel):
    """Complete result of link extraction and classification"""
    source_url: HttpUrl
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
            "other_count": len(self.other_links)
        }
