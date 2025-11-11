"""Test suite for backup and restore functionality.

Tests the BackupManager class and snapshot operations including:
- Snapshot creation
- Snapshot restoration
- Cleanup policies
- Cloud environment detection
"""

import os
import shutil
from pathlib import Path

import pytest

from config.backup import BackupManager
from config.database import DatabaseConnection


@pytest.fixture
def backup_mgr():
    """Create a BackupManager instance for testing.

    Note: This will only work in local development mode.
    If running on Streamlit Cloud, BackupManager will be disabled.
    """
    mgr = BackupManager()
    yield mgr

    # Cleanup: Remove test snapshots after each test
    if mgr.enabled and mgr.backup_dir:
        for snapshot_file in mgr.backup_dir.glob("*.duckdb"):
            # Only delete test snapshots (contain "test" in name)
            if "test" in snapshot_file.name.lower():
                snapshot_file.unlink()

        # Clean metadata
        if mgr.metadata_file.exists():
            import json
            with open(mgr.metadata_file, "r") as f:
                snapshots = json.load(f)

            # Keep only non-test snapshots
            snapshots = [s for s in snapshots if "test" not in s["snapshot_id"].lower()]

            with open(mgr.metadata_file, "w") as f:
                json.dump(snapshots, f, indent=2)


@pytest.fixture
def test_db():
    """Get database connection for testing."""
    db = DatabaseConnection()
    return db


def test_backup_manager_initialization(backup_mgr):
    """Test BackupManager initializes correctly."""
    assert backup_mgr is not None

    # Should be enabled in local dev, disabled on cloud
    if backup_mgr.enabled:
        assert backup_mgr.backup_dir is not None
        assert backup_mgr.metadata_file is not None
        assert backup_mgr.db_path is not None
        assert backup_mgr.backup_dir.exists()
    else:
        # Running on cloud - should be disabled gracefully
        assert backup_mgr.backup_dir is None
        assert backup_mgr.metadata_file is None
        assert backup_mgr.db_path is None


def test_create_snapshot(backup_mgr):
    """Test snapshot creation."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    snapshot_id = backup_mgr.create_snapshot(
        description="Test snapshot",
        operation_type="test",
        entity_type="measure",
        entity_id=999
    )

    assert snapshot_id is not None
    assert "test" in snapshot_id

    # Verify snapshot file exists
    snapshot_path = backup_mgr.backup_dir / f"{snapshot_id}.duckdb"
    assert snapshot_path.exists()

    # Verify metadata was saved
    snapshots = backup_mgr.list_snapshots()
    test_snapshot = next((s for s in snapshots if s["snapshot_id"] == snapshot_id), None)

    assert test_snapshot is not None
    assert test_snapshot["description"] == "Test snapshot"
    assert test_snapshot["operation_type"] == "test"
    assert test_snapshot["entity_type"] == "measure"
    assert test_snapshot["entity_id"] == 999


def test_list_snapshots(backup_mgr):
    """Test listing snapshots with filters."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    # Create test snapshots
    snapshot_1 = backup_mgr.create_snapshot(
        description="Test snapshot 1",
        operation_type="delete",
        entity_type="measure"
    )
    snapshot_2 = backup_mgr.create_snapshot(
        description="Test snapshot 2",
        operation_type="update",
        entity_type="area"
    )

    # List all
    all_snapshots = backup_mgr.list_snapshots()
    assert len(all_snapshots) >= 2

    # Filter by operation type
    delete_snapshots = backup_mgr.list_snapshots(operation_type="delete")
    assert any(s["snapshot_id"] == snapshot_1 for s in delete_snapshots)

    # Filter by entity type
    area_snapshots = backup_mgr.list_snapshots(entity_type="area")
    assert any(s["snapshot_id"] == snapshot_2 for s in area_snapshots)

    # Filter with limit
    limited = backup_mgr.list_snapshots(limit=1)
    assert len(limited) == 1


def test_restore_snapshot(backup_mgr, test_db):
    """Test snapshot restore functionality."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    # Get initial measure count
    conn = test_db.get_connection()
    initial_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Test snapshot for restore"
    )

    # Insert a test measure (simpler than deleting with FK constraints)
    test_measure_id = 9999
    conn.execute("""
        INSERT INTO measure (measure_id, measure, concise_measure, core_supplementary)
        VALUES (?, 'Test measure for restore', 'Test', 'Core')
    """, [test_measure_id])

    # Verify insertion
    new_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert new_count == initial_count + 1

    # Restore snapshot
    result = backup_mgr.restore_snapshot(snapshot_id)
    assert result is True

    # Verify restoration
    conn = test_db.get_connection()  # Reconnect after restore
    restored_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert restored_count == initial_count

    # Verify the test measure is gone
    test_measure_exists = conn.execute(
        "SELECT COUNT(*) FROM measure WHERE measure_id = ?",
        [test_measure_id]
    ).fetchone()[0]
    assert test_measure_exists == 0


def test_cleanup_old_snapshots(backup_mgr):
    """Test snapshot cleanup with retention policy."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    # Count existing snapshots
    existing_count = len(backup_mgr.list_snapshots())

    # Create multiple test snapshots
    snapshot_ids = []
    for i in range(5):
        snapshot_id = backup_mgr.create_snapshot(
            f"Test cleanup snapshot {i}",
            operation_type="test"
        )
        snapshot_ids.append(snapshot_id)

    # Verify all created
    all_snapshots = backup_mgr.list_snapshots()
    assert len(all_snapshots) == existing_count + 5

    # Cleanup, keep only 2 total
    deleted_count = backup_mgr.cleanup_old_snapshots(keep_count=2)

    # Should have deleted at least 3 (5 created + existing - 2 kept)
    assert deleted_count >= 3

    # Verify only 2 remain total
    remaining = backup_mgr.list_snapshots()
    assert len(remaining) == 2


def test_cloud_environment_detection_mock(monkeypatch):
    """Test cloud environment detection with mocked environment."""
    # Mock cloud environment
    monkeypatch.setenv("STREAMLIT_SHARING_MODE", "1")

    # Create new BackupManager with mocked environment
    mgr = BackupManager()

    # Should be detected as cloud and disabled
    assert mgr.is_cloud is True
    assert mgr.enabled is False


def test_snapshot_on_disabled_manager(monkeypatch):
    """Test that snapshot operations fail gracefully when disabled."""
    # Mock cloud environment
    monkeypatch.setenv("STREAMLIT_SHARING_MODE", "1")

    mgr = BackupManager()
    assert mgr.enabled is False

    # create_snapshot should return None without error
    snapshot_id = mgr.create_snapshot("Test snapshot")
    assert snapshot_id is None

    # list_snapshots should return empty list without error
    snapshots = mgr.list_snapshots()
    assert snapshots == []

    # cleanup should return 0 without error
    deleted = mgr.cleanup_old_snapshots(keep_count=10)
    assert deleted == 0


def test_restore_creates_safety_backup(backup_mgr):
    """Test that restore creates a safety backup first."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    # Create initial snapshot
    snapshot_id = backup_mgr.create_snapshot(
        "Test snapshot for safety backup test",
        operation_type="test"
    )

    # Count snapshots before restore
    snapshots_before = len(backup_mgr.list_snapshots())

    # Restore (should create safety backup)
    backup_mgr.restore_snapshot(snapshot_id)

    # Count snapshots after restore
    snapshots_after = len(backup_mgr.list_snapshots())

    # Should have one more snapshot (the safety backup)
    assert snapshots_after == snapshots_before + 1

    # Find the pre_restore snapshot (should be most recent)
    snapshots = backup_mgr.list_snapshots()
    pre_restore_snapshots = [s for s in snapshots if s.get("operation_type") == "pre_restore"]
    assert len(pre_restore_snapshots) >= 1


def test_snapshot_metadata_structure(backup_mgr):
    """Test that snapshot metadata has correct structure."""
    if not backup_mgr.enabled:
        pytest.skip("Backup functionality disabled (running on cloud)")

    snapshot_id = backup_mgr.create_snapshot(
        description="Test metadata structure",
        operation_type="delete",
        entity_type="measure",
        entity_id=123
    )

    snapshots = backup_mgr.list_snapshots()
    test_snapshot = next((s for s in snapshots if s["snapshot_id"] == snapshot_id), None)

    # Verify all expected fields exist
    assert "snapshot_id" in test_snapshot
    assert "timestamp" in test_snapshot
    assert "datetime" in test_snapshot
    assert "description" in test_snapshot
    assert "operation_type" in test_snapshot
    assert "entity_type" in test_snapshot
    assert "entity_id" in test_snapshot
    assert "file_path" in test_snapshot
    assert "size_mb" in test_snapshot

    # Verify data types
    assert isinstance(test_snapshot["snapshot_id"], str)
    assert isinstance(test_snapshot["size_mb"], (int, float))
    assert test_snapshot["entity_id"] == 123


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])
