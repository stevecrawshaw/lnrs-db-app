"""Performance monitoring and operational metrics.

This module provides decorators and utilities for monitoring
operation performance and logging metrics.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def monitor_performance(operation_name: str):
    """Decorator to monitor operation performance.

    Tracks execution time and logs performance metrics.
    Issues warnings for slow operations (>5 seconds).

    Args:
        operation_name: Name of the operation for logging

    Returns:
        Decorator function

    Example:
        @monitor_performance("measure_delete_cascade")
        def delete_with_cascade(self, measure_id: int) -> bool:
            # ... implementation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                logger.info(
                    f"Performance: {operation_name} completed in {elapsed:.3f}s"
                )

                # Alert if slow
                if elapsed > 5.0:
                    logger.warning(
                        f"Slow operation: {operation_name} took {elapsed:.3f}s"
                    )

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Performance: {operation_name} failed after {elapsed:.3f}s: {e}"
                )
                raise

        return wrapper

    return decorator


def log_operation_start(operation_name: str, **context):
    """Log the start of an operation with context.

    Args:
        operation_name: Name of the operation
        **context: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"Starting {operation_name} ({context_str})")


def log_operation_complete(operation_name: str, duration: float, **context):
    """Log successful completion of an operation.

    Args:
        operation_name: Name of the operation
        duration: Duration in seconds
        **context: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(
        f"Completed {operation_name} in {duration:.3f}s ({context_str})"
    )


def log_operation_error(operation_name: str, error: Exception, duration: float):
    """Log operation failure with error details.

    Args:
        operation_name: Name of the operation
        error: Exception that occurred
        duration: Duration before failure in seconds
    """
    logger.error(
        f"Failed {operation_name} after {duration:.3f}s: {error}",
        exc_info=True,
    )


class OperationTimer:
    """Context manager for timing operations.

    Example:
        with OperationTimer("snapshot_create") as timer:
            # ... perform operation
            timer.add_context(entity_id=123)
    """

    def __init__(self, operation_name: str):
        """Initialize operation timer.

        Args:
            operation_name: Name of the operation to time
        """
        self.operation_name = operation_name
        self.start_time = None
        self.context = {}

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        log_operation_start(self.operation_name, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log results."""
        duration = time.time() - self.start_time

        if exc_type is None:
            log_operation_complete(self.operation_name, duration, **self.context)
        else:
            log_operation_error(self.operation_name, exc_val, duration)

        return False  # Don't suppress exceptions

    def add_context(self, **context):
        """Add context information for logging.

        Args:
            **context: Key-value pairs to add to context
        """
        self.context.update(context)


def get_operation_stats() -> dict:
    """Get current operation statistics.

    This is a placeholder for future metrics collection.

    Returns:
        dict: Operation statistics
    """
    return {
        "status": "monitoring_active",
        "note": "Detailed metrics collection can be added here",
    }
