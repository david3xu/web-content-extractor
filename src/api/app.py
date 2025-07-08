"""
FastAPI application for web content extraction.
"""
import time
from typing import Dict, List, Optional, Any

import structlog
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field

from src.core import ExtractionService, ExtractionResult, LinkType
from src.infrastructure import (
    AsyncHttpClient,
    BeautifulSoupLinkParser,
    RegexLinkClassifier,
    LocalFileStorage,
)
from src.settings import settings
from src.logging import setup_logging

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Web Content Extractor API",
    description="Extract and categorize links from web pages",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging(level=settings.log_level, json_logs=settings.json_logs)


# API Models
class ExtractionRequest(BaseModel):
    """Extraction request model"""
    url: HttpUrl = Field(..., description="URL to extract content from")
    save_result: bool = Field(False, description="Whether to save the result")


class ExtractionResponse(BaseModel):
    """Extraction response model"""
    source_url: str = Field(..., description="Source URL")
    total_links: int = Field(..., description="Total number of links")
    pdf_count: int = Field(..., description="Number of PDF links")
    youtube_count: int = Field(..., description="Number of YouTube links")
    other_count: int = Field(..., description="Number of other links")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    links: Dict[str, List[Dict[str, Any]]] = Field(..., description="Categorized links")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


# Startup event
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Runs at startup"""
    logger.info("api_starting")


# Request middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Log request details
    process_time = time.time() - start_time
    logger.info(
        "api_request",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=f"{process_time:.4f}s",
    )

    return response


# Dependencies
def get_extraction_service() -> ExtractionService:
    """Dependency for extraction service"""
    http_client = AsyncHttpClient()
    link_parser = BeautifulSoupLinkParser()
    link_classifier = RegexLinkClassifier()
    storage = LocalFileStorage()

    return ExtractionService(
        content_extractor=http_client,
        link_parser=link_parser,
        link_classifier=link_classifier,
        result_storage=storage
    )


# Routes
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs"""
    return {"message": "API is running. Visit /docs for documentation."}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": time.time() - start_time
    }


@app.post("/extract", response_model=ExtractionResponse, tags=["Extraction"])
async def extract(
    request: ExtractionRequest,
    service: ExtractionService = Depends(get_extraction_service)
):
    """
    Extract and categorize links from a URL.
    """
    try:
        # Extract content
        result = await service.extract_and_classify(
            url=str(request.url),
            save_result=request.save_result
        )

        # Convert to response format
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

        return response

    except Exception as e:
        logger.error("extraction_api_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def create_app() -> FastAPI:
    """Create FastAPI application"""
    return app
