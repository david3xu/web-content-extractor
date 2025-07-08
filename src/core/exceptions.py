"""
Custom exceptions for the web content extractor.
"""


class ExtractionError(Exception):
    """Base exception for all extraction errors"""
    pass


class ContentExtractionError(ExtractionError):
    """Raised when content extraction fails"""
    pass


class LinkParsingError(ExtractionError):
    """Raised when link parsing fails"""
    pass


class LinkClassificationError(ExtractionError):
    """Raised when link classification fails"""
    pass


class ResultFormattingError(ExtractionError):
    """Raised when result formatting fails"""
    pass


class ResultStorageError(ExtractionError):
    """Raised when result storage fails"""
    pass


class ConfigurationError(ExtractionError):
    """Raised when there is a configuration issue"""
    pass
