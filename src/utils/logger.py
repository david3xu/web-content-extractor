import logging
from pathlib import Path


def setup_logger(name: str = "web_extractor", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

        # Ensure the logs directory exists
        logs_dir = Path("./logs")
        logs_dir.mkdir(exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(logs_dir / "web_extractor.log")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
