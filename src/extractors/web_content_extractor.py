import time
from typing import Optional
from ..utils.http_client import HttpClient
from ..models.extraction_models import LinkCategorizationResult, ExtractionMetadata
from .content_scraper import ContentScrapingService
from .link_classifier import LinkClassifierService
from .output_formatter import OutputFormatterService


class WebContentExtractor:
    def __init__(self,
                 timeout: int = 30,
                 max_retries: int = 3,
                 user_agent: str = None,
                 output_directory: str = "./output"):

        self.http_client = HttpClient(timeout, max_retries, user_agent)
        self.content_scraper = ContentScrapingService(self.http_client)
        self.link_classifier = LinkClassifierService()
        self.output_formatter = OutputFormatterService(output_directory)

    def extract_and_categorize(self, url: str) -> LinkCategorizationResult:
        """Main extraction and categorization workflow"""
        start_time = time.time()

        # Extract web content
        soup, raw_content = self.content_scraper.extract_web_content(url)
        page_title = self.content_scraper.get_page_title(soup)

        # Extract all links
        raw_links = self.content_scraper.extract_all_links(soup, url)

        # Classify links
        classified_links = self.link_classifier.classify_links(raw_links)
        pdf_links, youtube_links, other_links = self.link_classifier.categorize_by_type(classified_links)

        # Create metadata
        processing_time = time.time() - start_time
        metadata = ExtractionMetadata(
            total_links_found=len(classified_links),
            pdf_count=len(pdf_links),
            youtube_count=len(youtube_links),
            processing_time_seconds=processing_time,
            page_title=page_title
        )

        # Create result
        result = LinkCategorizationResult(
            source_url=url,
            pdf_links=pdf_links,
            youtube_links=youtube_links,
            other_links=other_links,
            metadata=metadata
        )

        return result

    def extract_and_export(self, url: str, output_format: str = "json",
                          export_to_file: bool = True) -> str:
        """Extract, categorize, and export results"""
        result = self.extract_and_categorize(url)

        if output_format.lower() == "json":
            formatted_output = self.output_formatter.generate_json_report(result)
        else:
            formatted_output = self.output_formatter.generate_console_output(result)

        if export_to_file:
            timestamp = int(time.time())
            filename = f"extraction_results_{timestamp}"
            file_path = self.output_formatter.export_to_file(
                formatted_output, filename, output_format
            )
            return file_path

        return formatted_output

    def close(self):
        """Clean up resources"""
        self.http_client.close()
