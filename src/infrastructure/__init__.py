"""
Infrastructure implementations of core interfaces.
"""
from .http_client import AsyncHttpClient
from .html_parser import BeautifulSoupLinkParser
from .link_classifier import RegexLinkClassifier
from .formatters import OutputFormatters, OutputFormat
from .local_storage import LocalFileStorage

__all__ = [
    'AsyncHttpClient',
    'BeautifulSoupLinkParser',
    'RegexLinkClassifier',
    'OutputFormatters',
    'OutputFormat',
    'LocalFileStorage',
]

# Conditionally export AzureBlobStorage only if the package is available
try:
    from .cloud_storage import AzureBlobStorage
    __all__.append('AzureBlobStorage')
except ImportError:
    # Azure Storage SDK not installed
    pass
