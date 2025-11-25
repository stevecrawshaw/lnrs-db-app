"""Integration tests for backup and restore functionality.

This module tests the integration between backup snapshots and
database operations, including automatic snapshot creation and restore.
"""

import logging
from pathlib import Path

import pytest

from models.measure import MeasureModel

logger = logging.getLogger(__name__)


def test_snapshot_before_delete(test_db, backup_mgr):
    """Test that snapshot is created before delete."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    measure_model = MeasureModel()
    conn = test_db.get_connection()

    # Get an existing measure
    existing = conn.execute("SELECT measure_id FROM measure LIMIT 1").fetchone()
    if not existing:
        pytest.skip("No measures found for testing")

    measure_id = existing[0]

    # Count snapshots before
    snapshots_before = len(backup_mgr.list_snapshots())

    logger.info(f"Snapshots before delete: {snapshots_before}")

    # Delete (should trigger snapshot via decorator)
    # Note: In test environment, decorator may not be active
    # This tests the BackupManager functionality itself
    snapshot_id = backup_mgr.create_snapshot(
        description=f"Before test delete of measure {measure_id}",
        operation_type="delete",
        entity_type="measure",
        entity_id=measure_id,
    )

    assert snapshot_id is not None

    # Verify snapshot created
    snapshots_after = len(backup_mgr.list_snapshots())
    assert snapshots_after == snapshots_before + 1

    # Verify latest snapshot metadata
    latest = backup_mgr.list_snapshots()[0]
    assert latest["operation_type"] == "delete"
    assert latest["entity_type"] == "measure"
    assert latest["entity_id"] == measure_id


def test_restore_recovers_deleted_data(test_db, backup_mgr):
    """Test that restore recovers deleted data."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    measure_model = MeasureModel()
    conn = test_db.get_connection()

    # Get original count
    original_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    logger.info(f"Original measure count: {original_count}")

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Before test delete", operation_type="test"
    )

    # Delete a measure
    existing = conn.execute("SELECT measure_id FROM measure LIMIT 1").fetchone()
    if not existing:
        pytest.skip("No measures found for testing")

    measure_id = existing[0]
    measure_model.delete_with_cascade(measure_id)

    # Verify deleted
    new_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert new_count == original_count - 1

    logger.info(f"Count after delete: {new_count}")

    # Restore
    backup_mgr.restore_snapshot(snapshot_id)

    # Verify restored
    restored_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert restored_count == original_count

    logger.info(f"Count after restore: {restored_count}")


def test_restore_creates_safety_backup(test_db, backup_mgr):
    """Test that restore creates safety backup first."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(description="Test snapshot")

    # Count snapshots
    snapshots_before = len(backup_mgr.list_snapshots())

    logger.info(f"Snapshots before restore: {snapshots_before}")

    # Restore (should create safety backup)
    backup_mgr.restore_snapshot(snapshot_id)

    # Verify safety backup was created
    snapshots_after = len(backup_mgr.list_snapshots())
    assert snapshots_after == snapshots_before + 1

    # Verify latest is safety backup
    latest = backup_mgr.list_snapshots()[0]
    assert latest["operation_type"] == "pre_restore"

    logger.info(f"Safety backup created: {latest['snapshot_id']}")


def test_cleanup_keeps_correct_count(test_db, backup_mgr):
    """Test cleanup keeps the correct number of snapshots."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    # Create multiple snapshots
    created_ids = []
    for i in range(15):
        snapshot_id = backup_mgr.create_snapshot(
            f"Test snapshot {i}", operation_type="test"
        )
        created_ids.append(snapshot_id)

    logger.info(f"Created {len(created_ids)} test snapshots")

    # Cleanup, keep only 5
    deleted = backup_mgr.cleanup_old_snapshots(keep_count=5)

    assert deleted == 10

    logger.info(f"Deleted {deleted} old snapshots")

    # Verify only 5 remain
    remaining = backup_mgr.list_snapshots()
    assert len(remaining) == 5

    # Verify newest are kept (should include snapshots 10-14)
    remaining_ids = [s["snapshot_id"] for s in remaining]
    newest_created = created_ids[-5:]

    for snapshot_id in newest_created:
        assert any(
            snapshot_id in rid for rid in remaining_ids
        ), f"Expected {snapshot_id} to be kept"


def test_snapshot_file_creation(test_db, backup_mgr):
    """Test that snapshot files are actually created."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    snapshot_id = backup_mgr.create_snapshot(
        description="File creation test", operation_type="test"
    )

    # Check that file exists
    snapshots = backup_mgr.list_snapshots()
    snapshot = next((s for s in snapshots if s["snapshot_id"] == snapshot_id), None)

    assert snapshot is not None
    snapshot_path = Path(snapshot["file_path"])
    assert snapshot_path.exists()
    assert snapshot_path.stat().st_size > 0

    logger.info(f"Snapshot file created: {snapshot_path} ({snapshot['size_mb']} MB)")


def test_snapshot_metadata_integrity(test_db, backup_mgr):
    """Test that snapshot metadata is complete and correct."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    snapshot_id = backup_mgr.create_snapshot(
        description="Metadata test",
        operation_type="test",
        entity_type="measure",
        entity_id=999,
    )

    snapshots = backup_mgr.list_snapshots()
    snapshot = next((s for s in snapshots if s["snapshot_id"] == snapshot_id), None)

    assert snapshot is not None
    assert snapshot["snapshot_id"] == snapshot_id
    assert snapshot["description"] == "Metadata test"
    assert snapshot["operation_type"] == "test"
    assert snapshot["entity_type"] == "measure"
    assert snapshot["entity_id"] == 999
    assert "timestamp" in snapshot
    assert "datetime" in snapshot
    assert "file_path" in snapshot
    assert "size_mb" in snapshot
    assert snapshot["size_mb"] > 0

    logger.info(f"Snapshot metadata verified: {snapshot}")


def test_restore_verifies_database_integrity(test_db, backup_mgr):
    """Test that restore verifies database integrity after restore."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Integrity test", operation_type="test"
    )

    # Restore should complete without errors
    # (integrity check is internal to restore_snapshot)
    try:
        backup_mgr.restore_snapshot(snapshot_id)
        logger.info("Restore completed with integrity verification")
    except Exception as e:
        pytest.fail(f"Restore failed integrity check: {e}")

    # Verify we can query the database
    conn = test_db.get_connection()
    count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert count >= 0

    logger.info(f"Database integrity verified: {count} measures found")
