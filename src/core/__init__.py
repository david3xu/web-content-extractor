"""
Core domain models, interfaces, and business logic for the web content extractor.
"""

from .exceptions import (
    ConfigurationError,
    ContentExtractionError,
    ExtractionError,
    LinkClassificationError,
    LinkParsingError,
    ResultFormattingError,
    ResultStorageError,
)
from .models import ExtractedLink, ExtractionMetadata, ExtractionResult, LinkType
from .service import ExtractionService
from .value_objects import CorrelationId, ProcessingTime, SourceUrl

__all__ = [
    "LinkType",
    "ExtractedLink",
    "ExtractionMetadata",
    "ExtractionResult",
    "SourceUrl",
    "ProcessingTime",
    "CorrelationId",
    "ExtractionError",
    "ContentExtractionError",
    "LinkParsingError",
    "LinkClassificationError",
    "ResultFormattingError",
    "ResultStorageError",
    "ConfigurationError",
    "ExtractionService",
]
