"""
Link classifier implementation.
"""
import re
from datetime import datetime
from re import Pattern

import structlog

from src.core.exceptions import ExtractionContext, LinkClassificationError
from src.core.interfaces import LinkClassifier
from src.core.models import ExtractedLink, LinkType
from src.core.value_objects import CorrelationId

logger = structlog.get_logger(__name__)


class RegexLinkClassifier(LinkClassifier):
    """
    Link classifier based on regex patterns.

    Implements the LinkClassifier protocol.
    """

    def __init__(self) -> None:
        # Regex patterns for identifying link types
        self._pdf_patterns: list[Pattern[str]] = [
            re.compile(r"\.pdf$", re.I)  # File extension
        ]

        self._youtube_patterns: list[Pattern[str]] = [
            re.compile(r"youtube\.com/watch", re.I),  # YouTube watch
            re.compile(r"youtu\.be/", re.I),  # YouTube short URL
            re.compile(r"youtube\.com/embed/", re.I),  # YouTube embed
            re.compile(r"youtube\.com/playlist", re.I),  # YouTube playlist
        ]

    def classify_links(self, links: list[tuple[str, str]]) -> list[ExtractedLink]:
        """
        Classify links using factory methods and enhanced error context.
        """
        try:
            classified_links = []

            for url, text in links:
                logger.debug("classifying_link", url=url, text=text)
                try:
                    # Use factory methods instead of direct construction
                    if any(pattern.search(url) for pattern in self._pdf_patterns):
                        link = ExtractedLink.create_pdf_link(url, text)
                    elif any(pattern.search(url) for pattern in self._youtube_patterns):
                        link = ExtractedLink.create_youtube_link(url, text)
                    else:
                        link = ExtractedLink.create_other_link(url, text)

                    classified_links.append(link)

                except ValueError as e:
                    # Skip invalid links but log the issue
                    logger.warning("invalid_link_skipped", url=url, error=str(e))
                    continue

            # Log classification stats
            type_counts = self._count_by_type(classified_links)
            logger.debug(
                "links_classified",
                total=len(classified_links),
                pdf_count=type_counts.get(LinkType.PDF, 0),
                youtube_count=type_counts.get(LinkType.YOUTUBE, 0),
                other_count=type_counts.get(LinkType.OTHER, 0),
            )

            return classified_links

        except Exception as e:
            logger.error("classification_failed", error=str(e))
            context = ExtractionContext(
                url="batch_classification",
                correlation_id=CorrelationId.generate(),
                start_time=datetime.now(),
            )
            raise LinkClassificationError("Failed to classify links", context, e) from e

    def _determine_link_type(self, url: str, text: str) -> LinkType:
        """
        Determine the link type based on URL and text.

        Args:
            url: Link URL
            text: Link text

        Returns:
            LinkType enum value
        """
        # Check for PDF links (URL only)
        for pattern in self._pdf_patterns:
            if pattern.search(url):
                return LinkType.PDF

        # Check for YouTube links
        for pattern in self._youtube_patterns:
            if pattern.search(url):
                return LinkType.YOUTUBE

        # Default to other
        return LinkType.OTHER

    def _count_by_type(self, links: list[ExtractedLink]) -> dict[LinkType, int]:
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
