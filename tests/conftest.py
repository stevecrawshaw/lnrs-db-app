"""Pytest configuration and shared fixtures for testing.

This module provides fixtures for testing with isolated test databases
and backup managers.
"""

import logging
import shutil
from pathlib import Path

import pytest

from config.database import DatabaseConnection

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_db_path():
    """Path to test database.

    Returns:
        Path: Path object for test database file
    """
    return Path("data/lnrs_test.duckdb")


@pytest.fixture(scope="session")
def production_db_path():
    """Path to production database.

    Returns:
        Path: Path object for production database file
    """
    return Path("data/lnrs_3nf_o1.duckdb")


@pytest.fixture(scope="function")
def test_db(test_db_path, production_db_path, monkeypatch):
    """Create a test database copy before each test.

    This fixture:
    1. Copies production database to test location
    2. Uses monkeypatch to redirect DatabaseConnection to test database
    3. Yields the configured database connection
    4. Cleans up test database after test completes

    Args:
        test_db_path: Path to test database (from fixture)
        production_db_path: Path to production database (from fixture)
        monkeypatch: pytest fixture for modifying environment/attributes

    Yields:
        DatabaseConnection: Configured database connection for testing
    """
    # Copy production to test
    if production_db_path.exists():
        shutil.copy2(production_db_path, test_db_path)
        logger.info(f"Copied production database to test location: {test_db_path}")
    else:
        logger.warning(f"Production database not found at {production_db_path}")

    # Close any existing connection
    db = DatabaseConnection()
    if db._connection is not None:
        db.close()

    # Monkeypatch the _create_local_connection method to use test database
    def _test_create_local_connection(self):
        """Test version that connects to test database."""
        import duckdb

        if not test_db_path.exists():
            raise FileNotFoundError(f"Test database file not found: {test_db_path}")

        try:
            connection = duckdb.connect(str(test_db_path))
            print(f"[TEST] Connected to test database: {test_db_path}")
            return connection
        except duckdb.Error as e:
            raise duckdb.Error(f"Failed to connect to test database: {e}") from e

    # Apply the monkeypatch
    monkeypatch.setattr(
        DatabaseConnection, "_create_local_connection", _test_create_local_connection
    )

    # Reset connection to pick up new implementation
    db.reset_connection()

    # Force local mode for tests
    db._mode = "local"

    logger.info(f"Configured DatabaseConnection for testing: {test_db_path}")

    yield db

    # Cleanup
    db.reset_connection()
    if test_db_path.exists():
        test_db_path.unlink()
        logger.info(f"Cleaned up test database: {test_db_path}")


@pytest.fixture(scope="function")
def backup_mgr(test_db, test_db_path):
    """Backup manager for testing.

    Creates a BackupManager instance configured to work with the test database.

    Args:
        test_db: Test database connection (from fixture)
        test_db_path: Path to test database (from fixture)

    Returns:
        BackupManager: Configured backup manager for testing
    """
    from config.backup import BackupManager

    mgr = BackupManager()
    mgr.db_path = test_db_path
    logger.info(f"Configured BackupManager for testing: {mgr.db_path}")
    return mgr


@pytest.fixture
def sample_measure_data():
    """Sample measure data for testing.

    Returns:
        dict: Sample measure data with required fields
    """
    return {
        "measure": "Test biodiversity measure for automated testing",
        "concise_measure": "Test measure",
        "core_supplementary": "Core (BNG)",
        "mapped_unmapped": "Mapped",
    }


@pytest.fixture
def sample_area_data():
    """Sample area data for testing.

    Returns:
        dict: Sample area data with required fields
    """
    return {
        "area_name": "Test Priority Area",
        "area_description": "Test area for automated testing",
        "area_link": "https://example.com/test-area",
    }


@pytest.fixture
def sample_priority_data():
    """Sample priority data for testing.

    Returns:
        dict: Sample priority data with required fields
    """
    return {
        "priority": "Test Priority",
        "theme": "Test Theme",
        "theme_definition": "Test theme definition",
        "priority_definition": "Test priority definition for automated testing",
    }


@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Set up logging for tests.

    This fixture automatically runs for all tests and configures
    logging to capture at DEBUG level.

    Args:
        caplog: Pytest fixture for capturing logs
    """
    caplog.set_level(logging.DEBUG)
