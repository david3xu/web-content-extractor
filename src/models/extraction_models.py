from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class LinkType(Enum):
    PDF = "pdf"
    YOUTUBE = "youtube"
    OTHER = "other"


@dataclass
class ExtractedLink:
    url: str
    link_text: str
    link_type: LinkType
    is_valid: bool = True
    context: Optional[str] = None


@dataclass
class ExtractionMetadata:
    total_links_found: int
    pdf_count: int
    youtube_count: int
    processing_time_seconds: float
    page_title: Optional[str] = None
    extraction_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LinkCategorizationResult:
    source_url: str
    pdf_links: List[ExtractedLink] = field(default_factory=list)
    youtube_links: List[ExtractedLink] = field(default_factory=list)
    other_links: List[ExtractedLink] = field(default_factory=list)
    metadata: Optional[ExtractionMetadata] = None

    def get_all_links(self) -> List[ExtractedLink]:
        return self.pdf_links + self.youtube_links + self.other_links
