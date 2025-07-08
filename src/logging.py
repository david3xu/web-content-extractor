"""
Structured logging configuration for the application.
"""
import logging
import sys

import structlog
from structlog.processors import CallsiteParameter


def setup_logging(
    level: str = "INFO", json_logs: bool = False, service_name: str = "web-extractor"
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to output JSON format (useful for production)
        service_name: Service identifier for log correlation
    """

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper())
    )

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add service name to all logs
    processors.append(
        structlog.processors.CallsiteParameterAdder(
            {CallsiteParameter.FILENAME, CallsiteParameter.FUNC_NAME}
        )
    )

    # Choose output format
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add service context to all logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with service context"""
    return structlog.get_logger(name)
