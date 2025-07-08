import azure.functions as func
import logging
import json
import tempfile
from pathlib import Path
import os
import time
from urllib.parse import urlparse

# Add the parent directory to the path so we can import the src package
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractors.web_content_extractor import WebContentExtractor
from src.config.settings import Settings
from src.models.exceptions import WebExtractionError

# Import Azure Blob Storage if available
try:
    from azure.storage.blob import BlobServiceClient
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    BLOB_STORAGE_AVAILABLE = False
    logging.warning("Azure Blob Storage SDK not available. Blob storage features disabled.")

app = func.FunctionApp()

@app.route(route="extract", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def extract_web_content(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Web content extraction request received')

    try:
        # Get URL from request
        req_body = req.get_json() if req.get_body() else {}
        url = req_body.get('url') or req.params.get('url')

        if not url:
            return func.HttpResponse(
                json.dumps({
                    "error": "Please provide a URL parameter."
                }),
                mimetype="application/json",
                status_code=400
            )

        # Get optional parameters
        output_format = req_body.get('format') or req.params.get('format') or "json"
        save_to_blob = req_body.get('save_to_blob') or req.params.get('save_to_blob') or False

        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Load settings but override output directory
            settings = Settings()

            # Initialize extractor
            extractor = WebContentExtractor(
                timeout=settings.request_timeout,
                max_retries=settings.max_retry_attempts,
                user_agent=settings.user_agent,
                output_directory=temp_dir
            )

            try:
                # Extract content
                result = extractor.extract_and_categorize(url)

                # Format the output based on requested format
                if output_format.lower() == 'json':
                    formatted_output = extractor.output_formatter.generate_json_report(result)
                else:
                    formatted_output = extractor.output_formatter.generate_console_output(result)

                # Save to blob storage if requested
                blob_url = None
                if save_to_blob and BLOB_STORAGE_AVAILABLE:
                    blob_url = _save_to_blob_storage(formatted_output, url, output_format)

                # Create response
                response_data = {
                    "status": "success",
                    "result": json.loads(formatted_output) if output_format == 'json' else formatted_output,
                }

                # Add blob URL if available
                if blob_url:
                    response_data["blob_url"] = blob_url

                # Return the results
                return func.HttpResponse(
                    json.dumps(response_data),
                    mimetype="application/json",
                    status_code=200
                )
            finally:
                # Clean up resources
                extractor.close()

    except WebExtractionError as e:
        logging.error(f"Extraction error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Extraction error: {str(e)}"}),
            mimetype="application/json",
            status_code=422
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Unexpected error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "web-content-extractor"}),
        status_code=200,
        mimetype="application/json"
    )

def _save_to_blob_storage(content: str, source_url: str, format_type: str):
    """Save extraction results to Azure Blob Storage"""
    try:
        # Get connection string from environment
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logging.warning("No Azure Storage connection string found")
            return None

        # Initialize blob service
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = "extraction-results"

        # Get container client - create if not exists
        try:
            container_client = blob_service.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception as e:
            logging.error(f"Failed to get or create container: {str(e)}")
            return None

        # Generate blob name
        domain = urlparse(source_url).netloc.replace('.', '-')
        timestamp = int(time.time())
        blob_name = f"{domain}/extraction_{timestamp}.{format_type}"

        # Upload to blob
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        blob_client.upload_blob(content, overwrite=True)

        # Return blob URL
        return blob_client.url

    except Exception as e:
        logging.error(f"Failed to save to blob storage: {str(e)}")
        return None
