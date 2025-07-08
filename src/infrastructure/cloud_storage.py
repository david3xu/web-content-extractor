"""
Cloud storage implementation using Azure Blob Storage.
"""
import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import structlog
import azure.core.exceptions
from azure.storage.blob import BlobServiceClient, ContentSettings

from src.core.interfaces import ResultStorage
from src.core.models import ExtractionResult
from src.core.exceptions import ResultStorageError
from src.settings import settings

logger = structlog.get_logger(__name__)


class AzureBlobStorage(ResultStorage):
    """
    Azure Blob Storage implementation.

    Implements the ResultStorage protocol.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: Optional[str] = None
    ):
        self.connection_string = connection_string or settings.azure_storage_connection_string
        self.container_name = container_name or settings.azure_storage_container

        if not self.connection_string:
            logger.warning("azure_storage_not_configured")
            raise ResultStorageError("Azure Storage connection string is not provided")

        # Create blob service client and ensure container exists
        try:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self._container_client = self._blob_service_client.get_container_client(
                self.container_name
            )

            # Create container if it doesn't exist
            if not self._container_client.exists():
                logger.info("creating_container", container=self.container_name)
                self._container_client.create_container()

        except Exception as e:
            logger.error("azure_storage_init_failed", error=str(e))
            raise ResultStorageError(f"Failed to initialize Azure Blob Storage: {e}") from e

    async def save_result(self, result: ExtractionResult, filename: Optional[str] = None) -> str:
        """
        Save extraction result to Azure Blob Storage.

        Args:
            result: The extraction result to save
            filename: Optional blob name, generated if not provided

        Returns:
            URL of the saved blob

        Raises:
            ResultStorageError: If saving fails
        """
        try:
            # Generate blob name if not provided
            if filename is None:
                domain = result.source_url.host.replace("www.", "")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"extraction_{domain}_{timestamp}.json"

            # Make sure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'

            # Convert result to JSON
            result_json = result.model_dump_json(indent=2)

            # Upload to blob storage
            blob_client = self._container_client.get_blob_client(filename)

            blob_client.upload_blob(
                result_json,
                overwrite=True,
                content_settings=ContentSettings(content_type='application/json')
            )

            # Get blob URL
            blob_url = blob_client.url

            logger.info(
                "result_saved_to_azure",
                container=self.container_name,
                blob=filename,
                size=len(result_json)
            )

            return blob_url

        except azure.core.exceptions.ResourceExistsError:
            # Handle case when blob already exists (unlikely with timestamp)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            new_filename = f"{filename.rsplit('.', 1)[0]}_{timestamp}.json"
            logger.warning("blob_already_exists_retrying", original=filename, new=new_filename)
            return await self.save_result(result, new_filename)

        except Exception as e:
            logger.error("azure_save_failed", error=str(e))
            raise ResultStorageError(f"Failed to save result to Azure Blob Storage: {e}") from e
