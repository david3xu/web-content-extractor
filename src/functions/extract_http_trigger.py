"""
Azure Function HTTP trigger for web content extraction.
"""
import json
import logging
import time
import os
from typing import Dict, Any
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
setup_logging(level="INFO", json_logs=True, service_name="web-extractor-function")
logger = structlog.get_logger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger for web content extraction.

    Parameters:
        req (func.HttpRequest): The HTTP request

    Returns:
        func.HttpResponse: The HTTP response
    """
    logger.info("function_invoked")
    start_time = time.time()

    try:
        # Parse request
        req_body = req.get_json() if req.get_body() else {"url": None}
        url = req_body.get("url") or req.params.get("url")
        save_result = req_body.get("save_result", True)

        # Validate URL
        if not url:
            return func.HttpResponse(
                json.dumps({"error": "Missing URL parameter"}),
                mimetype="application/json",
                status_code=400
            )

        logger.info("processing_url", url=url)

        # Set up components
        http_client = AsyncHttpClient()
        link_parser = BeautifulSoupLinkParser()
        link_classifier = RegexLinkClassifier()

        # Set up storage
        storage = None
        if save_result:
            try:
                connection_string = os.environ.get("AzureWebJobsStorage")
                storage = AzureBlobStorage(connection_string=connection_string)
            except Exception as e:
                logger.warning("storage_initialization_failed", error=str(e))

        # Create service and extract content
        service = ExtractionService(
            content_extractor=http_client,
            link_parser=link_parser,
            link_classifier=link_classifier,
            result_storage=storage
        )

        # Run extraction
        result = await service.extract_and_classify(url, save_result)

        # Format response
        response = {
            "source_url": str(result.source_url),
            "total_links": result.total_links,
            "pdf_count": len(result.pdf_links),
            "youtube_count": len(result.youtube_links),
            "other_count": len(result.other_links),
            "processing_time_seconds": result.metadata.processing_time_seconds if result.metadata else 0,
            "links": {
                "pdf": [link.model_dump() for link in result.pdf_links],
                "youtube": [link.model_dump() for link in result.youtube_links],
                "other": [link.model_dump() for link in result.other_links]
            }
        }

        processing_time = time.time() - start_time
        logger.info(
            "function_completed",
            url=url,
            total_links=result.total_links,
            processing_time=f"{processing_time:.4f}s"
        )

        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json"
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "function_failed",
            error=str(e),
            processing_time=f"{processing_time:.4f}s"
        )

        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
