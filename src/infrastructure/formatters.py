"""
Formatters for extraction result output in different formats.
"""
from collections.abc import Callable
from enum import Enum

import structlog

from src.core.exceptions import ResultFormattingError
from src.core.interfaces import ResultFormatter
from src.core.models import ExtractionResult

logger = structlog.get_logger(__name__)


class OutputFormat(str, Enum):
    """Supported output formats"""

    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    CSV = "csv"


class OutputFormatters(ResultFormatter):
    """
    Result formatters for different output formats.

    Implements the ResultFormatter protocol.
    """

    def __init__(self) -> None:
        # Register formatters
        self._formatters: dict[str, Callable[[ExtractionResult], str]] = {
            OutputFormat.JSON: self._format_json,
            OutputFormat.TEXT: self._format_text,
            OutputFormat.MARKDOWN: self._format_markdown,
            OutputFormat.CSV: self._format_csv,
        }

    def format_result(self, result: ExtractionResult, format_type: str) -> str:
        """
        Format extraction result into specified format.

        Args:
            result: The extraction result to format
            format_type: Output format (json, text, markdown, csv)

        Returns:
            Formatted string

        Raises:
            ResultFormattingError: If formatting fails or format is unsupported
        """
        try:
            format_type = format_type.lower()

            if format_type not in self._formatters:
                raise ValueError(f"Unsupported format: {format_type}")

            formatter = self._formatters[format_type]
            formatted_output = formatter(result)

            logger.debug("result_formatted", format=format_type)
            return formatted_output

        except Exception as e:
            logger.error("formatting_failed", format=format_type, error=str(e))
            raise ResultFormattingError(
                f"Failed to format result as {format_type}: {e}"
            ) from e

    def _format_json(self, result: ExtractionResult) -> str:
        """Format result as JSON"""
        return result.model_dump_json(indent=2)

    def _format_text(self, result: ExtractionResult) -> str:
        """Format result as plain text"""
        lines = [
            f"Extraction Results for: {result.source_url}",
            f"Total Links Found: {result.total_links}",
            "",
            f"PDF Links ({len(result.pdf_links)}):",
        ]

        for link in result.pdf_links:
            lines.append(f"- {link.link_text}: {link.url}")

        lines.append("")
        lines.append(f"YouTube Links ({len(result.youtube_links)}):")
        for link in result.youtube_links:
            lines.append(f"- {link.link_text}: {link.url}")

        if result.metadata:
            lines.append("")
            lines.append("Extraction Information:")
            lines.append(
                f"- Processing Time: {result.metadata.processing_time.seconds:.2f} seconds"
            )
            lines.append(f"- Extraction Date: {result.metadata.extraction_timestamp}")

        return "\n".join(lines)

    def _format_markdown(self, result: ExtractionResult) -> str:
        """Format result as Markdown"""
        lines = [
            f"# Extraction Results for: {result.source_url}",
            f"**Total Links Found:** {result.total_links}",
            "",
            f"## PDF Links ({len(result.pdf_links)})",
        ]

        for link in result.pdf_links:
            lines.append(f"- [{link.link_text}]({link.url})")

        lines.append("")
        lines.append(f"## YouTube Links ({len(result.youtube_links)})")
        for link in result.youtube_links:
            lines.append(f"- [{link.link_text}]({link.url})")

        lines.append("")
        lines.append(f"## Other Links ({len(result.other_links)})")
        for link in result.other_links:
            lines.append(f"- [{link.link_text}]({link.url})")

        if result.metadata:
            lines.append("")
            lines.append("## Extraction Information")
            lines.append(
                f"- **Processing Time:** {result.metadata.processing_time.seconds:.2f} seconds"
            )
            lines.append(
                f"- **Extraction Date:** {result.metadata.extraction_timestamp}"
            )

        return "\n".join(lines)

    def _format_csv(self, result: ExtractionResult) -> str:
        """Format result as CSV"""
        lines = ["Type,Text,URL"]

        for link in result.pdf_links:
            lines.append(f'PDF,"{link.link_text}",{link.url}')

        for link in result.youtube_links:
            lines.append(f'YouTube,"{link.link_text}",{link.url}')

        for link in result.other_links:
            lines.append(f'Other,"{link.link_text}",{link.url}')

        return "\n".join(lines)
