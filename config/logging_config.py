"""Logging configuration for the LNRS application.

This module sets up application-wide logging with separate handlers for
transactions, general application logs, and console output.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application-wide logging.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Parse log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Console handler - only warnings and errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        "%(levelname)s - %(name)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_dir / "transactions.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")


# Initialize logging when module is imported
setup_logging()
