"""
Link classifier implementation.
"""
from typing import List, Tuple, Pattern, Dict
import re

import structlog

from src.core.interfaces import LinkClassifier
from src.core.models import ExtractedLink, LinkType
from src.core.exceptions import LinkClassificationError

logger = structlog.get_logger(__name__)


class RegexLinkClassifier(LinkClassifier):
    """
    Link classifier based on regex patterns.

    Implements the LinkClassifier protocol.
    """

    def __init__(self):
        # Regex patterns for identifying link types
        self._pdf_patterns: List[Pattern] = [
            re.compile(r'\.pdf$', re.I),  # File extension
            re.compile(r'/pdf/', re.I),   # URL path
            re.compile(r'pdf', re.I)      # Text content
        ]

        self._youtube_patterns: List[Pattern] = [
            re.compile(r'youtube\.com/watch', re.I),    # YouTube watch
            re.compile(r'youtu\.be/', re.I),            # YouTube short URL
            re.compile(r'youtube\.com/embed/', re.I),   # YouTube embed
            re.compile(r'youtube\.com/playlist', re.I)  # YouTube playlist
        ]

    def classify_links(self, links: List[Tuple[str, str]]) -> List[ExtractedLink]:
        """
        Classify links into predefined categories.

        Args:
            links: List of (url, text) tuples

        Returns:
            List of ExtractedLink objects with assigned types

        Raises:
            LinkClassificationError: If classification fails
        """
        try:
            classified_links = []

            for url, text in links:
                link_type = self._determine_link_type(url, text)

                extracted_link = ExtractedLink(
                    url=url,
                    link_text=text or url,
                    link_type=link_type,
                    is_valid=True
                )

                classified_links.append(extracted_link)

            # Log classification stats
            type_counts = self._count_by_type(classified_links)
            logger.debug(
                "links_classified",
                total=len(classified_links),
                pdf_count=type_counts.get(LinkType.PDF, 0),
                youtube_count=type_counts.get(LinkType.YOUTUBE, 0),
                other_count=type_counts.get(LinkType.OTHER, 0)
            )

            return classified_links

        except Exception as e:
            logger.error("classification_failed", error=str(e))
            raise LinkClassificationError(f"Failed to classify links: {e}") from e

    def _determine_link_type(self, url: str, text: str) -> LinkType:
        """
        Determine the link type based on URL and text.

        Args:
            url: Link URL
            text: Link text

        Returns:
            LinkType enum value
        """
        # Check for PDF links (URL first, then text)
        for pattern in self._pdf_patterns:
            if pattern.search(url):
                return LinkType.PDF

        # Check for YouTube links
        for pattern in self._youtube_patterns:
            if pattern.search(url):
                return LinkType.YOUTUBE

        # Last check for PDF in text
        for pattern in self._pdf_patterns:
            if text and pattern.search(text):
                return LinkType.PDF

        # Default to other
        return LinkType.OTHER

    def _count_by_type(self, links: List[ExtractedLink]) -> Dict[LinkType, int]:
        """
        Count links by type.

        Args:
            links: List of ExtractedLink objects

        Returns:
            Dictionary with LinkType keys and counts as values
        """
        counts = {link_type: 0 for link_type in LinkType}
        for link in links:
            counts[link.link_type] += 1
        return counts
