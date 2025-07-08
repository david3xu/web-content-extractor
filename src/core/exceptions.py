"""
Custom exceptions for the web content extractor with enhanced context.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .value_objects import CorrelationId


@dataclass
class ExtractionContext:
    """Rich context for error reporting and debugging."""

    url: str
    correlation_id: CorrelationId
    start_time: datetime
    attempt: int = 1
    total_attempts: int = 1
    user_agent: str = "WebExtractor/1.0"
    additional_data: dict[str, Any] | None = None

    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return (datetime.now() - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "url": self.url,
            "correlation_id": str(self.correlation_id),
            "elapsed_time": self.get_elapsed_time(),
            "attempt": self.attempt,
            "total_attempts": self.total_attempts,
            "user_agent": self.user_agent,
            "additional_data": self.additional_data or {},
        }


class ExtractionError(Exception):
    """Base exception for all extraction errors"""

    pass


class ContextualExtractionError(ExtractionError):
    """Base exception with extraction context."""

    def __init__(
        self,
        message: str,
        context: ExtractionContext,
        cause: Exception | None = None,
    ):
        correlation_msg = f"{message} [correlation_id={context.correlation_id}]"
        super().__init__(correlation_msg)
        self.context = context
        self.cause = cause

    def get_debug_info(self) -> dict[str, Any]:
        """Get debug information for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "context": self.context.to_dict(),
            "cause": str(self.cause) if self.cause else None,
        }


class ContentExtractionError(ContextualExtractionError):
    """Raised when content extraction fails"""

    pass


class LinkParsingError(ContextualExtractionError):
    """Raised when link parsing fails"""

    pass


class LinkClassificationError(ContextualExtractionError):
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
