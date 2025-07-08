import json
from pathlib import Path
from typing import Dict, Any
from ..models.extraction_models import LinkCategorizationResult, ExtractedLink
from ..models.exceptions import OutputFormattingError


class OutputFormatterService:
    def __init__(self, output_directory: str = "./output"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)

    def generate_json_report(self, result: LinkCategorizationResult) -> str:
        """Generate JSON formatted report"""
        try:
            report_data = {
                "source_url": result.source_url,
                "extraction_timestamp": result.metadata.extraction_timestamp.isoformat() if result.metadata else None,
                "summary": {
                    "total_links": len(result.get_all_links()),
                    "pdf_count": len(result.pdf_links),
                    "youtube_count": len(result.youtube_links),
                    "other_count": len(result.other_links)
                },
                "pdf_links": [self._link_to_dict(link) for link in result.pdf_links],
                "youtube_links": [self._link_to_dict(link) for link in result.youtube_links],
                "other_links": [self._link_to_dict(link) for link in result.other_links],
                "metadata": self._metadata_to_dict(result.metadata) if result.metadata else None
            }

            return json.dumps(report_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OutputFormattingError(f"Failed to generate JSON report: {str(e)}")

    def generate_console_output(self, result: LinkCategorizationResult) -> str:
        """Generate human-readable console output"""
        output_lines = [
            f"Web Content Extraction Results",
            f"Source URL: {result.source_url}",
            f"",
            f"Summary:",
            f"  Total Links Found: {len(result.get_all_links())}",
            f"  PDF Links: {len(result.pdf_links)}",
            f"  YouTube Links: {len(result.youtube_links)}",
            f"  Other Links: {len(result.other_links)}",
            f""
        ]

        if result.pdf_links:
            output_lines.extend([
                "PDF Links:",
                *[f"  • {link.link_text}: {link.url}" for link in result.pdf_links],
                ""
            ])

        if result.youtube_links:
            output_lines.extend([
                "YouTube Links:",
                *[f"  • {link.link_text}: {link.url}" for link in result.youtube_links],
                ""
            ])

        return "\n".join(output_lines)

    def export_to_file(self, content: str, filename: str, format_type: str = "json"):
        """Export content to file"""
        try:
            file_path = self.output_directory / f"{filename}.{format_type}"
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return str(file_path)
        except Exception as e:
            raise OutputFormattingError(f"Failed to export to file: {str(e)}")

    def _link_to_dict(self, link: ExtractedLink) -> Dict[str, Any]:
        return {
            "url": link.url,
            "text": link.link_text,
            "type": link.link_type.value,
            "is_valid": link.is_valid
        }

    def _metadata_to_dict(self, metadata) -> Dict[str, Any]:
        return {
            "total_links_found": metadata.total_links_found,
            "pdf_count": metadata.pdf_count,
            "youtube_count": metadata.youtube_count,
            "processing_time_seconds": metadata.processing_time_seconds,
            "page_title": metadata.page_title,
            "extraction_timestamp": metadata.extraction_timestamp.isoformat()
        }
