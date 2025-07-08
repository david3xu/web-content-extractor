"""
Infrastructure implementations of core interfaces.
"""
from .formatters import OutputFormat, OutputFormatters
from .html_parser import BeautifulSoupLinkParser
from .http_client import AsyncHttpClient
from .link_classifier import RegexLinkClassifier
from .local_storage import LocalFileStorage

__all__ = [
    "AsyncHttpClient",
    "BeautifulSoupLinkParser",
    "RegexLinkClassifier",
    "OutputFormatters",
    "OutputFormat",
    "LocalFileStorage",
]

# Conditionally export AzureBlobStorage only if the package is available
try:
    from .cloud_storage import AzureBlobStorage

    __all__.append("AzureBlobStorage")
except ImportError:
    # Azure Storage SDK not installed
    pass
