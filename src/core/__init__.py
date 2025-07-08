"""
Core domain models, interfaces, and business logic for the web content extractor.
"""

from .models import LinkType, ExtractedLink, ExtractionMetadata, ExtractionResult
from .exceptions import (
    ExtractionError, ContentExtractionError, LinkParsingError,
    LinkClassificationError, ResultFormattingError, ResultStorageError,
    ConfigurationError
)
from .service import ExtractionService

__all__ = [
    'LinkType',
    'ExtractedLink',
    'ExtractionMetadata',
    'ExtractionResult',
    'ExtractionError',
    'ContentExtractionError',
    'LinkParsingError',
    'LinkClassificationError',
    'ResultFormattingError',
    'ResultStorageError',
    'ConfigurationError',
    'ExtractionService',
]
