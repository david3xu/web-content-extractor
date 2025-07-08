"""
Value objects for domain-driven design.
"""
from dataclasses import dataclass

from pydantic import HttpUrl


@dataclass(frozen=True)
class SourceUrl:
    """Value object for source URLs with domain logic."""

    value: HttpUrl

    def get_domain(self) -> str:
        """Extract domain name."""
        if self.value.host is None:
            return ""  # Or handle this case as appropriate, e.g., raise ValueError
        return self.value.host.replace("www.", "")

    def is_secure(self) -> bool:
        """Check if URL uses HTTPS."""
        return self.value.scheme == "https"

    def get_path_depth(self) -> int:
        """Calculate URL path depth for complexity analysis."""
        if self.value.path is None:
            return 0  # Or handle this case as appropriate
        path = self.value.path.strip("/")
        return len(path.split("/")) if path else 0

    @classmethod
    def from_string(cls, url_str: str) -> "SourceUrl":
        """Create from string with validation."""
        return cls(HttpUrl(url_str))


@dataclass(frozen=True)
class ProcessingTime:
    """Value object for processing time with business logic."""

    seconds: float

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("Processing time must be positive")

    def to_milliseconds(self) -> int:
        """Convert to milliseconds for logging."""
        return int(self.seconds * 1000)

    def is_slow(self) -> bool:
        """Determine if processing was slow (business rule)."""
        return self.seconds > 5.0

    def get_performance_category(self) -> str:
        """Categorize performance for monitoring."""
        if self.seconds < 1.0:
            return "fast"
        elif self.seconds < 3.0:
            return "normal"
        elif self.seconds < 10.0:
            return "slow"
        else:
            return "critical"


@dataclass(frozen=True)
class CorrelationId:
    """Value object for request correlation tracking."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) < 8:
            raise ValueError("Correlation ID must be at least 8 characters")

    @classmethod
    def generate(cls) -> "CorrelationId":
        """Generate a new correlation ID."""
        import uuid

        return cls(str(uuid.uuid4())[:8])

    def __str__(self) -> str:
        return self.value
