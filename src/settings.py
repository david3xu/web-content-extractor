"""
Application settings with validation and environment variable support.
"""
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    Settings can be provided via:
    1. Environment variables (prefixed with WEB_EXTRACTOR_)
    2. .env file
    3. Default values
    """

    # HTTP Settings
    http_timeout: float = Field(
        default=30.0, description="HTTP request timeout in seconds", gt=0, le=300
    )

    max_retries: int = Field(
        default=3, description="Maximum number of HTTP retry attempts", ge=0, le=10
    )

    user_agent: str = Field(
        default="WebExtractor/1.0 (+https://github.com/company/web-extractor)",
        description="HTTP User-Agent header",
    )

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    json_logs: bool = Field(
        default=False, description="Output logs in JSON format (for production)"
    )

    # Storage Settings
    output_directory: Path = Field(
        default=Path("./output"), description="Directory for output files"
    )

    # Optional Azure Settings
    azure_storage_connection_string: str | None = Field(
        default=None, description="Azure Storage connection string for blob storage"
    )

    azure_storage_container: str = Field(
        default="extraction-results", description="Azure Storage container name"
    )

    @field_validator("output_directory")
    @classmethod
    def create_output_directory(cls, v: Path) -> Path:
        """Ensure output directory exists"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("user_agent")
    @classmethod
    def user_agent_not_empty(cls, v: str) -> str:
        """Ensure user agent is not empty"""
        if not v.strip():
            raise ValueError("User agent cannot be empty")
        return v.strip()

    class Config:
        env_file = ".env"
        env_prefix = "WEB_EXTRACTOR_"
        case_sensitive = False

    def is_azure_storage_enabled(self) -> bool:
        """Check if Azure Storage is configured"""
        return self.azure_storage_connection_string is not None


# Global settings instance
settings = Settings()
