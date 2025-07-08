"""
Core domain models, interfaces, and business logic for the web content extractor.
"""

from .models import LinkType, ExtractedLink, ExtractionMetadata, ExtractionResult
from .value_objects import SourceUrl, ProcessingTime, CorrelationId
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
    'SourceUrl',
    'ProcessingTime',
    'CorrelationId',
    'ExtractionError',
    'ContentExtractionError',
    'LinkParsingError',
    'LinkClassificationError',
    'ResultFormattingError',
    'ResultStorageError',
    'ConfigurationError',
    'ExtractionService',
]
