import re
from typing import List, Tuple
from ..models.extraction_models import ExtractedLink, LinkType
from ..models.exceptions import LinkClassificationError


class LinkClassifierService:
    def __init__(self):
        self.pdf_pattern = re.compile(r'\.pdf$', re.IGNORECASE)
        self.youtube_patterns = [
            re.compile(r'youtube\.com/watch\?v=', re.IGNORECASE),
            re.compile(r'youtu\.be/', re.IGNORECASE),
            re.compile(r'youtube\.com/embed/', re.IGNORECASE)
        ]

    def classify_links(self, links: List[Tuple[str, str]]) -> List[ExtractedLink]:
        """Classify links into categories"""
        try:
            classified_links = []

            for url, text in links:
                link_type = self._determine_link_type(url)
                extracted_link = ExtractedLink(
                    url=url,
                    link_text=text,
                    link_type=link_type,
                    is_valid=True  # Could add validation here
                )
                classified_links.append(extracted_link)

            return classified_links
        except Exception as e:
            raise LinkClassificationError(f"Failed to classify links: {str(e)}")

    def _determine_link_type(self, url: str) -> LinkType:
        """Determine the type of link"""
        if self.pdf_pattern.search(url):
            return LinkType.PDF

        for pattern in self.youtube_patterns:
            if pattern.search(url):
                return LinkType.YOUTUBE

        return LinkType.OTHER

    def categorize_by_type(self, links: List[ExtractedLink]) -> Tuple[List[ExtractedLink], List[ExtractedLink], List[ExtractedLink]]:
        """Separate links by type"""
        pdf_links = [link for link in links if link.link_type == LinkType.PDF]
        youtube_links = [link for link in links if link.link_type == LinkType.YOUTUBE]
        other_links = [link for link in links if link.link_type == LinkType.OTHER]

        return pdf_links, youtube_links, other_links
