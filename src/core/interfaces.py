"""
Core interfaces using protocols to define the contract between components.
"""
from typing import Protocol, List, Tuple, runtime_checkable


@runtime_checkable
class ContentExtractor(Protocol):
    """Protocol for extracting content from URLs"""
    async def extract_content(self, url: str) -> str:
        """Extract raw HTML content from URL"""
        ...


@runtime_checkable
class LinkParser(Protocol):
    """Protocol for parsing links from content"""
    def parse_links(self, content: str, base_url: str) -> List[Tuple[str, str]]:
        """Parse links from HTML content, return (url, text) tuples"""
        ...


@runtime_checkable
class LinkClassifier(Protocol):
    """Protocol for classifying link types"""
    def classify_links(self, links: List[Tuple[str, str]]) -> List["ExtractedLink"]:
        """Classify links into categories (PDF, YouTube, other)"""
        ...


@runtime_checkable
class ResultFormatter(Protocol):
    """Protocol for formatting extraction results"""
    def format_result(self, result: "ExtractionResult", format_type: str) -> str:
        """Format extraction result into specified format (json, console, etc.)"""
        ...


@runtime_checkable
class ResultStorage(Protocol):
    """Protocol for storing extraction results"""
    async def save_result(self, result: "ExtractionResult", filename: str = None) -> str:
        """Save extraction result, return storage location"""
        ...
