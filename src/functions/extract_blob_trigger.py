"""
Azure Function Blob trigger for batch web content extraction.
"""
import json
import logging
import time
import os
import asyncio

import azure.functions as func
import structlog

from src.core import ExtractionService
from src.infrastructure import (
    AsyncHttpClient, BeautifulSoupLinkParser, RegexLinkClassifier
)
from src.infrastructure.cloud_storage import AzureBlobStorage
from src.logging import setup_logging

# Configure structured logging
setup_logging(level="INFO", json_logs=True, service_name="web-extractor-blob-trigger")
logger = structlog.get_logger(__name__)


async def main(blob: func.InputStream, outputBlob: func.Out[str]) -> None:
    """
    Azure Function Blob trigger for batch web content extraction.

    This function is triggered when a new blob is uploaded to the input container.
    It expects the blob to contain a JSON array of URLs or JSON objects with a "url" field.

    Parameters:
        blob (func.InputStream): The input blob
        outputBlob (func.Out[str]): The output blob
    """
    logger.info("blob_trigger_invoked", blob_name=blob.name)
    start_time = time.time()

    try:
        # Read and parse blob content
        blob_content = blob.read().decode('utf-8')
        urls_data = json.loads(blob_content)

        # Ensure we have a list of URLs
        if not isinstance(urls_data, list):
            urls_data = [urls_data]

        # Extract URLs from input data
        urls = []
        for item in urls_data:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict) and "url" in item:
                urls.append(item["url"])

        if not urls:
            logger.warning("no_urls_found", blob_name=blob.name)
            outputBlob.set(json.dumps({
                "error": "No valid URLs found in input blob",
                "blob_name": blob.name
            }))
            return

        logger.info("processing_urls", count=len(urls), blob_name=blob.name)

        # Set up components
        http_client = AsyncHttpClient()
        link_parser = BeautifulSoupLinkParser()
        link_classifier = RegexLinkClassifier()

        # Set up storage
        try:
            connection_string = os.environ.get("AzureWebJobsStorage")
            storage = AzureBlobStorage(connection_string=connection_string)
        except Exception as e:
            logger.warning("storage_initialization_failed", error=str(e))
            storage = None

        # Create service
        service = ExtractionService(
            content_extractor=http_client,
            link_parser=link_parser,
            link_classifier=link_classifier,
            result_storage=storage
        )

        # Process each URL
        results = []
        errors = []

        for url in urls:
            try:
                # Extract content
                result = await service.extract_and_classify(url, True)

                # Format result
                result_data = {
                    "source_url": str(result.source_url),
                    "total_links": result.total_links,
                    "pdf_count": len(result.pdf_links),
                    "youtube_count": len(result.youtube_links),
                    "other_count": len(result.other_links),
                    "links": {
                        "pdf": [link.model_dump() for link in result.pdf_links],
                        "youtube": [link.model_dump() for link in result.youtube_links],
                        "other": [link.model_dump() for link in result.other_links]
                    }
                }

                results.append(result_data)
                logger.info("url_processed", url=url, total_links=result.total_links)

            except Exception as e:
                logger.error("url_processing_error", url=url, error=str(e))
                errors.append({
                    "url": url,
                    "error": str(e)
                })

        # Create output
        output = {
            "processed_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
            "processing_time_seconds": time.time() - start_time
        }

        # Write output blob
        outputBlob.set(json.dumps(output, indent=2))

        logger.info(
            "blob_processing_completed",
            processed_count=len(results),
            error_count=len(errors),
            processing_time=f"{time.time() - start_time:.2f}s"
        )

    except Exception as e:
        logger.error("blob_processing_failed", blob_name=blob.name, error=str(e))
        outputBlob.set(json.dumps({
            "error": str(e),
            "blob_name": blob.name,
            "processing_time_seconds": time.time() - start_time
        }))
