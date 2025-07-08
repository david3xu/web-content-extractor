"""
Local file storage implementation.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from src.core.interfaces import ResultStorage
from src.core.models import ExtractionResult
from src.core.exceptions import ResultStorageError
from src.settings import settings

logger = structlog.get_logger(__name__)


class LocalFileStorage(ResultStorage):
    """
    Local file storage implementation.

    Implements the ResultStorage protocol.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.output_directory
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure output directory exists"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("directory_creation_failed", path=str(self.output_dir), error=str(e))
            raise ResultStorageError(f"Failed to create directory {self.output_dir}: {e}")

    async def save_result(self, result: ExtractionResult, filename: Optional[str] = None) -> str:
        """
        Save extraction result to a local JSON file.

        Args:
            result: The extraction result to save
            filename: Optional filename, generated if not provided

        Returns:
            Path to saved file

        Raises:
            ResultStorageError: If saving fails
        """
        try:
            # Generate filename if not provided
            if filename is None:
                domain = result.source_url.host.replace("www.", "")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"extraction_{domain}_{timestamp}.json"

            # Make sure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'

            # Create full path
            file_path = self.output_dir / filename

            # Convert result to JSON
            result_json = result.model_dump_json(indent=2)

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result_json)

            logger.info("result_saved", path=str(file_path), size=len(result_json))
            return str(file_path)

        except Exception as e:
            logger.error("save_failed", error=str(e))
            raise ResultStorageError(f"Failed to save result: {e}") from e
