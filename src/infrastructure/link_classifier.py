"""
Link classifier implementation.
"""

import re
from re import Pattern

import structlog

from src.core.models import ExtractedLink

logger = structlog.get_logger(__name__)


class RegexLinkClassifier:
    def __init__(self) -> None:
        # Enhanced PDF patterns
        self._pdf_patterns: list[Pattern[str]] = [
            re.compile(r"\.pdf$", re.I),
            re.compile(r"\.pdf[?#]", re.I),
            re.compile(r"\.pdf.*download", re.I),
            re.compile(r"[^/]*\.pdf[^/]*$", re.I),  # Better PDF detection
        ]

        # Enhanced YouTube patterns
        self._youtube_patterns: list[Pattern[str]] = [
            re.compile(r"youtube\.com/watch", re.I),
            re.compile(r"youtu\.be/", re.I),
            re.compile(r"youtube\.com/embed/", re.I),
            re.compile(r"youtube-nocookie\.com", re.I),
        ]

    def classify_links(self, links: list[tuple[str, str]]) -> list[ExtractedLink]:
        classified_links = []

        for url, text in links:
            # Debug logging
            logger.debug("classifying_link", url=url[:100], text=text[:50])

            try:
                if self._is_pdf_link(url, text):
                    link = ExtractedLink.create_pdf_link(url, text)
                elif self._is_youtube_link(url, text):
                    link = ExtractedLink.create_youtube_link(url, text)
                else:
                    link = ExtractedLink.create_other_link(url, text)

                classified_links.append(link)

            except ValueError as e:
                logger.warning("invalid_link_skipped", url=url, error=str(e))
                continue

        return classified_links

    def _is_pdf_link(self, url: str, text: str) -> bool:
        # Check URL patterns
        if any(pattern.search(url) for pattern in self._pdf_patterns):
            return True
        # Check text content
        if re.search(r"\.pdf\b", text, re.I) or "PDF" in text.upper():
            return True
        return False

    def _is_youtube_link(self, url: str, text: str) -> bool:
        # Check URL patterns
        if any(pattern.search(url) for pattern in self._youtube_patterns):
            return True
        # Check text content
        if "youtube" in text.lower() or "watch" in text.lower():
            return True
        return False
