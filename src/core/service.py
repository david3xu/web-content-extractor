"""
Core extraction service that orchestrates the extraction process.
"""

from datetime import datetime

import structlog

from .exceptions import ContextualExtractionError, ExtractionContext
from .interfaces import ContentExtractor, LinkClassifier, LinkParser, ResultStorage
from .models import ExtractionMetadata, ExtractionResult, LinkType
from .value_objects import CorrelationId, ProcessingTime, SourceUrl

logger = structlog.get_logger()


class ExtractionService:
    """
    Core business logic for web content extraction with enhanced error handling.
    """

    def __init__(
        self,
        content_extractor: ContentExtractor,
        link_parser: LinkParser,
        link_classifier: LinkClassifier,
        result_storage: ResultStorage | None = None,
    ):
        self._content_extractor = content_extractor
        self._link_parser = link_parser
        self._link_classifier = link_classifier
        self._result_storage = result_storage

    async def extract_and_classify(
        self, url: str, save_result: bool = False
    ) -> tuple[ExtractionResult, str]:
        """
        Main extraction workflow with enhanced error context.
        """
        # Create extraction context
        correlation_id = CorrelationId.generate()
        context = ExtractionContext(
            url=url, correlation_id=correlation_id, start_time=datetime.now()
        )

        logger.info("extraction_started", url=url, correlation_id=str(correlation_id))

        try:
            # Step 1: Extract content
            content = await self._content_extractor.extract_content(url)
            logger.debug(
                "content_extracted",
                url=url,
                content_length=len(content),
                correlation_id=str(correlation_id),
            )

            # Step 2: Parse links
            raw_links = self._link_parser.parse_links(content, url)
            logger.debug(
                "links_parsed",
                url=url,
                link_count=len(raw_links),
                correlation_id=str(correlation_id),
            )

            # Step 3: Classify links
            classified_links = self._link_classifier.classify_links(raw_links)
            logger.debug(
                "links_classified",
                url=url,
                classified_count=len(classified_links),
                correlation_id=str(correlation_id),
            )

            # Step 4: Create result
            processing_time = ProcessingTime(context.get_elapsed_time())

            # Sort links by type
            pdf_links = [
                link for link in classified_links if link.link_type == LinkType.PDF
            ]
            youtube_links = [
                link for link in classified_links if link.link_type == LinkType.YOUTUBE
            ]
            other_links = [
                link for link in classified_links if link.link_type == LinkType.OTHER
            ]

            metadata = ExtractionMetadata(
                total_links_found=len(classified_links),
                pdf_count=len(pdf_links),
                youtube_count=len(youtube_links),
                processing_time=processing_time,
                correlation_id=correlation_id,
            )

            result = ExtractionResult(
                source_url=SourceUrl.from_string(url),
                pdf_links=pdf_links,
                youtube_links=youtube_links,
                other_links=other_links,
                metadata=metadata,
            )

            # Step 5: Optionally save result
            if save_result and self._result_storage:
                storage_location = await self._result_storage.save_result(result)
                logger.info(
                    "result_saved",
                    url=url,
                    location=storage_location,
                    correlation_id=str(correlation_id),
                )

            logger.info(
                "extraction_completed",
                url=url,
                total_links=result.total_links,
                processing_time=processing_time.seconds,
                correlation_id=str(correlation_id),
            )

            return result, content

        except Exception as e:
            logger.error(
                "extraction_failed",
                url=url,
                error=str(e),
                correlation_id=str(correlation_id),
            )

            # Wrap in contextual error if not already
            if isinstance(e, ContextualExtractionError):
                raise
            else:
                raise ContextualExtractionError(
                    f"Failed to extract content from {url}: {e}", context, cause=e
                ) from e

    async def crawl_and_extract(
        self, start_url: str, max_pages: int = 15
    ) -> ExtractionResult:
        """Crawl multiple pages using existing extraction logic and aggregate results."""
        visited_urls: set[str] = set()
        urls_to_visit: list[str] = [start_url]
        final_result: ExtractionResult | None = None

        logger.info("crawling_started", start_url=start_url, max_pages=max_pages)

        while urls_to_visit and len(visited_urls) < max_pages:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                logger.debug("skipping_visited_url", url=current_url)
                continue

            visited_urls.add(current_url)
            logger.info(
                "extracting_page", url=current_url, pages_crawled=len(visited_urls)
            )

            try:
                # Extract and classify content for the current page
                page_result, content = await self.extract_and_classify(
                    current_url, save_result=False
                )

                if final_result is None:
                    final_result = page_result
                else:
                    final_result = final_result.merge_with(page_result)

                # Discover new links for crawling
                if self._link_parser:
                    navigation_links = self._link_parser.find_navigation_links(
                        content,
                        current_url,
                    )

                    # Prioritise course or module specific pages first
                    priority_keywords = (
                        "module",
                        "lesson",
                        "course",
                        "chapter",
                        "part",
                    )
                    priority_links = [
                        link
                        for link in navigation_links
                        if any(k in link.lower() for k in priority_keywords)
                    ]
                    other_links = [
                        link for link in navigation_links if link not in priority_links
                    ]

                    ordered_links = priority_links + other_links

                    for link in ordered_links:
                        if link not in visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)

            except ContextualExtractionError as e:
                logger.warning("page_extraction_failed", url=current_url, error=str(e))
            except Exception as e:
                logger.error(
                    "unexpected_error_during_crawl", url=current_url, error=str(e)
                )

        if final_result is None:  # Handle case where no pages were crawled successfully
            final_result = ExtractionResult(
                source_url=SourceUrl.from_string(start_url),
                metadata=ExtractionMetadata(
                    total_links_found=0,
                    pdf_count=0,
                    youtube_count=0,
                    processing_time=ProcessingTime(0.0),
                    correlation_id=CorrelationId.generate(),
                ),
            )

        logger.info(
            "crawling_completed",
            start_url=start_url,
            total_pages_crawled=len(visited_urls),
            total_links_found=final_result.total_links,
        )
        return final_result
