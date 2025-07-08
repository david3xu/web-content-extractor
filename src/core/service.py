"""
Core extraction service that orchestrates the extraction process.
"""
import time
from typing import Optional

import structlog

from .exceptions import ExtractionError
from .interfaces import ContentExtractor, LinkParser, LinkClassifier, ResultStorage
from .models import ExtractionResult, ExtractionMetadata, LinkType, ExtractedLink

logger = structlog.get_logger()


class ExtractionService:
    """
    Core business logic for web content extraction.

    Orchestrates the extraction process without knowing about
    implementation details of HTTP clients, parsers, or storage.
    """

    def __init__(
        self,
        content_extractor: ContentExtractor,
        link_parser: LinkParser,
        link_classifier: LinkClassifier,
        result_storage: Optional[ResultStorage] = None
    ):
        self._content_extractor = content_extractor
        self._link_parser = link_parser
        self._link_classifier = link_classifier
        self._result_storage = result_storage

    async def extract_and_classify(self, url: str, save_result: bool = False) -> ExtractionResult:
        """
        Main extraction workflow.

        Args:
            url: Target URL to extract links from
            save_result: Whether to persist the result

        Returns:
            Complete extraction result with classified links

        Raises:
            ExtractionError: If any step in the process fails
        """
        start_time = time.time()

        logger.info("extraction_started", url=url)

        try:
            # Step 1: Extract content
            content = await self._content_extractor.extract_content(url)
            logger.debug("content_extracted", url=url, content_length=len(content))

            # Step 2: Parse links
            raw_links = self._link_parser.parse_links(content, url)
            logger.debug("links_parsed", url=url, link_count=len(raw_links))

            # Step 3: Classify links
            classified_links = self._link_classifier.classify_links(raw_links)
            logger.debug("links_classified", url=url, classified_count=len(classified_links))

            # Sort links by type
            pdf_links = [link for link in classified_links if link.link_type == LinkType.PDF]
            youtube_links = [link for link in classified_links if link.link_type == LinkType.YOUTUBE]
            other_links = [link for link in classified_links if link.link_type == LinkType.OTHER]

            # Step 4: Create result
            processing_time = time.time() - start_time
            metadata = ExtractionMetadata(
                total_links_found=len(classified_links),
                pdf_count=len(pdf_links),
                youtube_count=len(youtube_links),
                processing_time_seconds=processing_time
            )

            result = ExtractionResult(
                source_url=url,
                pdf_links=pdf_links,
                youtube_links=youtube_links,
                other_links=other_links,
                metadata=metadata
            )

            # Step 5: Optionally save result
            if save_result and self._result_storage:
                storage_location = await self._result_storage.save_result(result)
                logger.info("result_saved", url=url, location=storage_location)

            logger.info("extraction_completed",
                       url=url,
                       total_links=result.total_links,
                       processing_time=processing_time)

            return result

        except Exception as e:
            logger.error("extraction_failed", url=url, error=str(e))
            raise ExtractionError(f"Failed to extract content from {url}: {e}") from e
