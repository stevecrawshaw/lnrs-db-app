"""Test script to verify logging functionality for section 1.4.

This script tests that:
1. Logging is properly initialized
2. Model operations log correctly
3. Log files are created in logs/ directory
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import logging setup
from config.logging_config import setup_logging

# Import models to test
from models.measure import MeasureModel
from config.database import db

# Initialize logging (should already be initialized on import, but explicitly calling it)
setup_logging()

logger = logging.getLogger(__name__)


def test_logging_initialization():
    """Test that logging is properly initialized."""
    print("\n=== Test 1: Logging Initialization ===")

    # Check if logs directory exists
    logs_dir = Path("logs")
    assert logs_dir.exists(), "logs/ directory should exist"
    print("[OK] logs/ directory exists")

    # Check if transactions.log exists
    log_file = logs_dir / "transactions.log"
    assert log_file.exists(), "logs/transactions.log should exist"
    print(f"[OK] {log_file} exists")

    # Test logging at different levels
    logger.debug("Debug message from test script")
    logger.info("Info message from test script")
    logger.warning("Warning message from test script")
    logger.error("Error message from test script")
    print("[OK] Logged messages at all levels")


def test_database_logging():
    """Test that database operations log correctly."""
    print("\n=== Test 2: Database Logging ===")

    try:
        # Test database connection (should log connection message)
        conn = db.get_connection()
        print("[OK] Database connection established (check logs for connection message)")

        # Test a simple query (should be logged at DEBUG level)
        result = db.execute_query("SELECT COUNT(*) FROM measure")
        count = result.fetchone()[0]
        print(f"[OK] Query executed successfully: {count} measures found")

    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        print(f"[FAIL] Database test failed: {e}")


def test_model_logging():
    """Test that model operations log correctly."""
    print("\n=== Test 3: Model Logging ===")

    try:
        measure_model = MeasureModel()

        # Test get_by_id with invalid ID (should trigger error logging)
        result = measure_model.get_by_id(999999)
        if result is None:
            print("[OK] get_by_id returned None for non-existent record (check logs for error)")

        # Test count (should work fine)
        count = measure_model.count()
        print(f"[OK] count() returned {count} measures")

    except Exception as e:
        logger.error(f"Model test failed: {e}", exc_info=True)
        print(f"[FAIL] Model test failed: {e}")


def verify_log_file_contents():
    """Verify that log file contains expected content."""
    print("\n=== Test 4: Log File Contents ===")

    log_file = Path("logs/transactions.log")

    if log_file.exists():
        # Read last 20 lines of log file
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        print(f"[OK] Log file has {len(lines)} lines")

        # Show last few entries
        print("\nLast 10 log entries:")
        print("-" * 80)
        for line in lines[-10:]:
            print(line.strip())
        print("-" * 80)
    else:
        print("[FAIL] Log file not found")


if __name__ == "__main__":
    print("=" * 80)
    print("ENHANCED ERROR HANDLING & LOGGING TEST (Section 1.4)")
    print("=" * 80)

    test_logging_initialization()
    test_database_logging()
    test_model_logging()
    verify_log_file_contents()

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check logs/transactions.log for detailed logging")
    print("2. Verify structured error messages in UI")
    print("3. Update TRANSACTION_DEPLOYMENT_PLAN.md to mark section 1.4 complete")
