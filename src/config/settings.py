from pathlib import Path
import yaml
from typing import Dict, Any


class Settings:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    @property
    def extraction_settings(self) -> Dict[str, Any]:
        return self.config.get('extraction', {})

    @property
    def output_settings(self) -> Dict[str, Any]:
        return self.config.get('output', {})

    @property
    def request_timeout(self) -> int:
        return self.extraction_settings.get('request_timeout', 30)

    @property
    def max_retry_attempts(self) -> int:
        return self.extraction_settings.get('max_retry_attempts', 3)

    @property
    def user_agent(self) -> str:
        return self.extraction_settings.get('user_agent', 'WebContentExtractor/1.0')

    @property
    def output_format(self) -> str:
        return self.output_settings.get('default_format', 'json')

    @property
    def output_directory(self) -> str:
        return self.output_settings.get('output_directory', './output')
