"""
Unit tests for value objects.
"""
import pytest
from pydantic import HttpUrl

from src.core.value_objects import CorrelationId, ProcessingTime, SourceUrl


class TestSourceUrl:
    """Test SourceUrl value object."""

    def test_get_domain(self) -> None:
        """Test domain extraction."""
        url = SourceUrl(HttpUrl("https://www.example.com/path"))
        assert url.get_domain() == "example.com"

    def test_is_secure(self) -> None:
        """Test security check."""
        secure_url = SourceUrl(HttpUrl("https://example.com"))
        insecure_url = SourceUrl(HttpUrl("http://example.com"))

        assert secure_url.is_secure() is True
        assert insecure_url.is_secure() is False

    def test_get_path_depth(self) -> None:
        """Test path depth calculation."""
        shallow_url = SourceUrl(HttpUrl("https://example.com"))
        deep_url = SourceUrl(HttpUrl("https://example.com/path/to/resource"))

        assert shallow_url.get_path_depth() == 0
        assert deep_url.get_path_depth() == 3

    def test_from_string(self) -> None:
        """Test creation from string."""
        url = SourceUrl.from_string("https://example.com")
        assert url.get_domain() == "example.com"

    def test_from_string_with_www(self) -> None:
        """Test creation from string with www prefix."""
        url = SourceUrl.from_string("https://www.example.com")
        assert url.get_domain() == "example.com"


class TestProcessingTime:
    """Test ProcessingTime value object."""

    def test_valid_processing_time(self) -> None:
        """Test valid processing time."""
        pt = ProcessingTime(1.5)
        assert pt.seconds == 1.5
        assert pt.to_milliseconds() == 1500

    def test_invalid_processing_time_zero(self) -> None:
        """Test invalid processing time raises error."""
        with pytest.raises(ValueError, match="Processing time must be positive"):
            ProcessingTime(0.0)

    def test_invalid_processing_time_negative(self) -> None:
        """Test negative processing time raises error."""
        with pytest.raises(ValueError, match="Processing time must be positive"):
            ProcessingTime(-1.0)

    def test_performance_categories(self) -> None:
        """Test performance categorization."""
        fast = ProcessingTime(0.5)
        normal = ProcessingTime(2.0)
        slow = ProcessingTime(7.0)
        critical = ProcessingTime(15.0)

        assert fast.get_performance_category() == "fast"
        assert normal.get_performance_category() == "normal"
        assert slow.get_performance_category() == "slow"
        assert critical.get_performance_category() == "critical"

    def test_is_slow(self) -> None:
        """Test slow processing detection."""
        fast = ProcessingTime(2.0)
        slow = ProcessingTime(7.0)

        assert fast.is_slow() is False
        assert slow.is_slow() is True

    def test_milliseconds_conversion(self) -> None:
        """Test milliseconds conversion."""
        pt = ProcessingTime(1.234)
        assert pt.to_milliseconds() == 1234


class TestCorrelationId:
    """Test CorrelationId value object."""

    def test_valid_correlation_id(self) -> None:
        """Test valid correlation ID."""
        cid = CorrelationId("12345678")
        assert str(cid) == "12345678"

    def test_invalid_correlation_id_short(self) -> None:
        """Test invalid correlation ID raises error."""
        with pytest.raises(
            ValueError, match="Correlation ID must be at least 8 characters"
        ):
            CorrelationId("short")

    def test_invalid_correlation_id_empty(self) -> None:
        """Test empty correlation ID raises error."""
        with pytest.raises(
            ValueError, match="Correlation ID must be at least 8 characters"
        ):
            CorrelationId("")

    def test_generate(self) -> None:
        """Test correlation ID generation."""
        cid = CorrelationId.generate()
        assert len(str(cid)) == 8
        assert isinstance(str(cid), str)

    def test_string_representation(self) -> None:
        """Test string representation."""
        cid = CorrelationId("test1234")
        assert str(cid) == "test1234"
        assert repr(cid) == "CorrelationId(value='test1234')"
