import re
from re import Pattern
from urllib.parse import parse_qs, urlparse

from src.core.interfaces import LinkClassifier
from src.core.models import ExtractedLink, LinkType


class ContextAwareClassifier(LinkClassifier):
    """Enhanced classifier using content context"""

    def __init__(self) -> None:
        self._pdf_patterns: list[Pattern[str]] = [
            re.compile(r"\.pdf$", re.I),
            re.compile(r"\.pdf[?#]", re.I),  # PDFs with query params
            re.compile(r"pdf.*download", re.I),  # Download contexts
        ]

        self._youtube_patterns: list[Pattern[str]] = [
            re.compile(r"youtube\.com/watch", re.I),
            re.compile(r"youtu\.be/", re.I),
            # NEW: Add embed patterns
            re.compile(r"youtube\.com/embed/", re.I),
            re.compile(r"youtube-nocookie\.com", re.I),
            re.compile(
                r"cdn\.iframe\.ly/.*", re.I
            ),  # Broader pattern for iframe.ly YouTube embeds
        ]

    def classify_links(self, links: list[tuple[str, str]]) -> list[ExtractedLink]:
        classified_links = []

        for url, text in links:
            # Use MULTIPLE detection methods
            link_type = self._classify_with_context(url, text)
            classified_links.append(
                ExtractedLink(url=url, link_text=text, link_type=link_type)
            )

        return classified_links

    def _classify_with_context(self, url: str, text: str) -> LinkType:
        """Enhanced classification using URL + text context"""
        # 1) Try strict URL pattern matching first (covers cdn.iframe.ly etc.)
        url_pattern_type = self._classify_by_url_patterns(url)
        if url_pattern_type != LinkType.OTHER:
            return url_pattern_type

        # 2) Detect file size hints such as "3MB pdf"
        if re.search(r"\d+\s*MB.*pdf", text, re.I):
            return LinkType.PDF

        lowered_url = url.lower()

        # 3) Special handling for iframe.ly proxies that wrap YouTube URLs
        if "iframe.ly" in lowered_url:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            proxied_url: str | None = qs.get("url", [""])[0] or None
            if proxied_url and any(
                p.search(proxied_url) for p in self._youtube_patterns
            ):
                return LinkType.YOUTUBE

        # 4) Heuristic YouTube detection from link text
        if "watch" in text.lower():
            return LinkType.YOUTUBE

        return LinkType.OTHER

    def _classify_by_url_patterns(self, url: str) -> LinkType:
        if any(pattern.search(url) for pattern in self._pdf_patterns):
            return LinkType.PDF
        if any(pattern.search(url) for pattern in self._youtube_patterns):
            return LinkType.YOUTUBE
        return LinkType.OTHER
