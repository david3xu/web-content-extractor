class WebExtractionError(Exception):
    """Base exception for web extraction operations"""
    pass


class ContentScrapingError(WebExtractionError):
    """Exception raised during web content scraping"""
    pass


class LinkClassificationError(WebExtractionError):
    """Exception raised during link classification"""
    pass


class OutputFormattingError(WebExtractionError):
    """Exception raised during output formatting"""
    pass


class ConfigurationError(WebExtractionError):
    """Exception raised for configuration issues"""
    pass
