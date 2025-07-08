"""
Link classifier implementation.
"""
import re
from re import Pattern

import structlog

from src.core.interfaces import LinkClassifier
from src.core.models import ExtractedLink, LinkType

logger = structlog.get_logger(__name__)


class RegexLinkClassifier(LinkClassifier):
    """
    Link classifier using regular expressions.

    Implements the LinkClassifier protocol.
    """

    def __init__(self) -> None:
        # OPTIMIZED: Combined efficient patterns
        self._patterns: dict[LinkType, list[Pattern[str]]] = {
            LinkType.PDF: [
                re.compile(r"\.pdf[?&#]?", re.I),  # Covers all PDF cases
                re.compile(r"download.*pdf", re.I),  # Download context
            ],
            LinkType.YOUTUBE: [
                re.compile(
                    r"(youtube|youtu\.be|iframe\.ly)", re.I
                ),  # All video sources
                re.compile(r"embed.*video", re.I),  # Generic embeds
            ],
        }

    def classify_links(self, links: list[tuple[str, str]]) -> list[ExtractedLink]:
        """Streamlined classification"""
        classified_links = []
        for url, text in links:
            # Skip invalid links that cannot be created by ExtractedLink
            try:
                classified_links.append(self._classify_single_link(url, text))
            except ValueError as e:
                logger.warning("link_classification_failed", url=url, error=str(e))
                continue  # Skip the invalid link

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

    def _classify_single_link(self, url: str, text: str) -> ExtractedLink:
        """Single method handles all classification logic"""
        link_type = self._get_type_from_patterns(url, text)
        logger.debug(
            "classifying_single_link",
            url=url,
            text=text,
            determined_type=link_type.value,
        )

        # Factory methods handle validation
        if link_type == LinkType.PDF:
            return ExtractedLink.create_pdf_link(url, text)
        elif link_type == LinkType.YOUTUBE:
            return ExtractedLink.create_youtube_link(url, text)
        else:
            return ExtractedLink.create_other_link(url, text)

    def _get_type_from_patterns(self, url: str, text: str) -> LinkType:
        """Determine link type using optimized patterns and text context."""
        text_lower = text.lower()

        # Prioritize text-based classification
        if any(
            re.search(pattern, text_lower)
            for pattern in self._patterns.get(LinkType.PDF, [])
        ):
            return LinkType.PDF
        if any(
            re.search(pattern, text_lower)
            for pattern in self._patterns.get(LinkType.YOUTUBE, [])
        ):
            return LinkType.YOUTUBE

        # Fallback to URL pattern matching
        if any(pattern.search(url) for pattern in self._patterns.get(LinkType.PDF, [])):
            return LinkType.PDF
        if any(
            pattern.search(url) for pattern in self._patterns.get(LinkType.YOUTUBE, [])
        ):
            return LinkType.YOUTUBE

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
