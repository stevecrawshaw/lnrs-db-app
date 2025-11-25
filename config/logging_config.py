"""Logging configuration for the LNRS application.

This module sets up application-wide logging with separate handlers for
transactions, backups, performance metrics, and console output.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application-wide logging.

    Creates separate log files for:
    - transactions.log: All transaction and database operations
    - backups.log: Backup and restore operations
    - performance.log: Performance metrics and timing
    - Console: Warnings and errors only

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Parse log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Detailed formatter for file logs
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Simple formatter for performance logs
    performance_formatter = logging.Formatter("%(asctime)s - %(message)s")

    # Console formatter
    console_formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")

    # Console handler - only warnings and errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)

    # Transaction log handler - all database operations
    transaction_handler = logging.FileHandler(log_dir / "transactions.log")
    transaction_handler.setLevel(logging.DEBUG)
    transaction_handler.setFormatter(detailed_formatter)

    # Backup log handler - backup and restore operations
    backup_handler = logging.FileHandler(log_dir / "backups.log")
    backup_handler.setLevel(logging.INFO)
    backup_handler.setFormatter(detailed_formatter)
    # Filter to only log from backup module
    backup_handler.addFilter(lambda record: "backup" in record.name.lower())

    # Performance log handler - performance metrics
    performance_handler = logging.FileHandler(log_dir / "performance.log")
    performance_handler.setLevel(logging.INFO)
    performance_handler.setFormatter(performance_formatter)
    # Filter to only log performance metrics
    performance_handler.addFilter(
        lambda record: "Performance:" in record.getMessage()
        or "monitor" in record.name.lower()
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add all handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(transaction_handler)
    root_logger.addHandler(backup_handler)
    root_logger.addHandler(performance_handler)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized with separate handlers for transactions, backups, and performance"
    )


# Initialize logging when module is imported
setup_logging()
