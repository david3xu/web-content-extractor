"""
Unit tests for enhanced error context and exceptions.
"""
import pytest
from datetime import datetime

from src.core.exceptions import (
    ExtractionContext, ContextualExtractionError, ContentExtractionError,
    LinkParsingError, LinkClassificationError
)
from src.core.value_objects import CorrelationId


class TestExtractionContext:
    """Test ExtractionContext dataclass."""

    def test_context_creation(self):
        """Test context creation with basic parameters."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time
        )

        assert context.url == "https://example.com"
        assert context.correlation_id == correlation_id
        assert context.start_time == start_time
        assert context.attempt == 1
        assert context.total_attempts == 1
        assert context.user_agent == "WebExtractor/1.0"
        assert context.additional_data is None

    def test_context_with_custom_values(self):
        """Test context creation with custom values."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time,
            attempt=3,
            total_attempts=5,
            user_agent="CustomAgent/2.0",
            additional_data={"key": "value"}
        )

        assert context.attempt == 3
        assert context.total_attempts == 5
        assert context.user_agent == "CustomAgent/2.0"
        assert context.additional_data == {"key": "value"}

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        start_time = datetime.now()
        context = ExtractionContext(
            url="https://example.com",
            correlation_id=CorrelationId.generate(),
            start_time=start_time
        )

        # Should be very small since we just created it
        elapsed = context.get_elapsed_time()
        assert elapsed >= 0
        assert elapsed < 1.0  # Should be less than 1 second

    def test_to_dict(self):
        """Test context serialization to dictionary."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time,
            attempt=2,
            total_attempts=3,
            user_agent="TestAgent/1.0",
            additional_data={"test": "data"}
        )

        context_dict = context.to_dict()

        assert context_dict["url"] == "https://example.com"
        assert context_dict["correlation_id"] == str(correlation_id)
        assert context_dict["attempt"] == 2
        assert context_dict["total_attempts"] == 3
        assert context_dict["user_agent"] == "TestAgent/1.0"
        assert context_dict["additional_data"] == {"test": "data"}
        assert "elapsed_time" in context_dict
        assert context_dict["elapsed_time"] >= 0


class TestContextualExtractionError:
    """Test ContextualExtractionError base class."""

    def test_error_creation(self):
        """Test contextual error creation."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time
        )

        error = ContextualExtractionError(
            message="Test error message",
            context=context
        )

        assert str(correlation_id) in str(error)
        assert "Test error message" in str(error)
        assert error.context == context
        assert error.cause is None

    def test_error_with_cause(self):
        """Test contextual error with cause."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time
        )

        original_error = ValueError("Original error")
        error = ContextualExtractionError(
            message="Wrapped error message",
            context=context,
            cause=original_error
        )

        assert error.cause == original_error
        assert str(correlation_id) in str(error)

    def test_debug_info(self):
        """Test debug information generation."""
        correlation_id = CorrelationId.generate()
        start_time = datetime.now()

        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=start_time,
            additional_data={"debug": "info"}
        )

        original_error = ValueError("Original error")
        error = ContextualExtractionError(
            message="Test error",
            context=context,
            cause=original_error
        )

        debug_info = error.get_debug_info()

        assert debug_info["error_type"] == "ContextualExtractionError"
        assert "Test error" in debug_info["message"]
        assert debug_info["context"]["url"] == "https://example.com"
        assert debug_info["context"]["correlation_id"] == str(correlation_id)
        assert debug_info["cause"] == "Original error"


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_content_extraction_error(self):
        """Test ContentExtractionError."""
        correlation_id = CorrelationId.generate()
        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=datetime.now()
        )

        error = ContentExtractionError(
            message="Content extraction failed",
            context=context
        )

        assert isinstance(error, ContextualExtractionError)
        assert "Content extraction failed" in str(error)
        assert str(correlation_id) in str(error)

    def test_link_parsing_error(self):
        """Test LinkParsingError."""
        correlation_id = CorrelationId.generate()
        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=datetime.now()
        )

        error = LinkParsingError(
            message="Link parsing failed",
            context=context
        )

        assert isinstance(error, ContextualExtractionError)
        assert "Link parsing failed" in str(error)
        assert str(correlation_id) in str(error)

    def test_link_classification_error(self):
        """Test LinkClassificationError."""
        correlation_id = CorrelationId.generate()
        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=datetime.now()
        )

        error = LinkClassificationError(
            message="Link classification failed",
            context=context
        )

        assert isinstance(error, ContextualExtractionError)
        assert "Link classification failed" in str(error)
        assert str(correlation_id) in str(error)

    def test_error_inheritance_hierarchy(self):
        """Test that all contextual errors inherit properly."""
        correlation_id = CorrelationId.generate()
        context = ExtractionContext(
            url="https://example.com",
            correlation_id=correlation_id,
            start_time=datetime.now()
        )

        content_error = ContentExtractionError("test", context)
        parsing_error = LinkParsingError("test", context)
        classification_error = LinkClassificationError("test", context)

        # All should inherit from ContextualExtractionError
        assert isinstance(content_error, ContextualExtractionError)
        assert isinstance(parsing_error, ContextualExtractionError)
        assert isinstance(classification_error, ContextualExtractionError)

        # All should inherit from ExtractionError
        assert isinstance(content_error, Exception)
        assert isinstance(parsing_error, Exception)
        assert isinstance(classification_error, Exception)
