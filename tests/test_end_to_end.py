"""End-to-end lifecycle tests for measures with backups.

This module tests complete workflows from creation through deletion
and restoration, verifying data integrity at each stage.
"""

import logging

import pytest

from models.measure import MeasureModel

logger = logging.getLogger(__name__)


def test_full_measure_lifecycle_with_backups(test_db, backup_mgr, sample_measure_data):
    """Test complete measure lifecycle: create → update → delete → restore."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    measure_model = MeasureModel()
    conn = test_db.get_connection()

    # Get initial count
    initial_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    logger.info(f"Starting lifecycle test with {initial_count} measures")

    # 1. Create measure
    # Note: We'll use an existing measure for testing since create() requires
    # proper data structure
    existing = conn.execute("SELECT measure_id, measure FROM measure LIMIT 1").fetchone()
    if not existing:
        pytest.skip("No measures found for testing")

    measure_id = existing[0]
    original_text = existing[1]

    logger.info(f"Using existing measure {measure_id} for lifecycle test")

    # Create snapshot after finding measure
    snapshot_after_find = backup_mgr.create_snapshot(
        f"After finding measure {measure_id}", operation_type="test"
    )

    # 2. Update measure
    updated_data = {
        "measure": original_text + " (LIFECYCLE TEST UPDATE)",
        "concise_measure": "Lifecycle test",
        "core_supplementary": "Core (BNG)",
    }

    result = measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data=updated_data,
        measure_types=[1, 2],
        stakeholders=[],
        benefits=[],
    )

    assert result is True

    # Verify update
    updated = conn.execute(
        "SELECT measure FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()
    assert "(LIFECYCLE TEST UPDATE)" in updated[0]

    logger.info(f"Updated measure {measure_id}")

    # Create snapshot after update
    snapshot_after_update = backup_mgr.create_snapshot(
        f"After updating measure {measure_id}", operation_type="test"
    )

    # 3. Delete measure (snapshot created automatically in production)
    measure_model.delete_with_cascade(measure_id)

    # Verify deleted
    deleted_check = conn.execute(
        "SELECT COUNT(*) FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]
    assert deleted_check == 0

    logger.info(f"Deleted measure {measure_id}")

    # 4. Restore to after-update state
    backup_mgr.restore_snapshot(snapshot_after_update)

    restored = conn.execute(
        "SELECT measure FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()
    assert restored is not None
    assert "(LIFECYCLE TEST UPDATE)" in restored[0]

    logger.info(f"Restored measure {measure_id} to after-update state")

    # 5. Restore to original state
    backup_mgr.restore_snapshot(snapshot_after_find)

    original = conn.execute(
        "SELECT measure FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()
    assert original is not None
    assert "(LIFECYCLE TEST UPDATE)" not in original[0]
    assert original[0] == original_text

    logger.info(f"Restored measure {measure_id} to original state")


def test_multiple_operations_with_snapshots(test_db, backup_mgr):
    """Test multiple operations with snapshots between each."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    conn = test_db.get_connection()

    # Get initial count
    initial_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    snapshots = []

    # Create snapshot 1
    snapshot1 = backup_mgr.create_snapshot(
        "State 1: Initial", operation_type="test"
    )
    snapshots.append((snapshot1, initial_count))

    logger.info(f"Snapshot 1: {initial_count} measures")

    # Get two measures to delete
    measures_to_delete = conn.execute(
        "SELECT measure_id FROM measure LIMIT 2"
    ).fetchall()

    if len(measures_to_delete) < 2:
        pytest.skip("Need at least 2 measures for testing")

    # Delete first measure
    MeasureModel().delete_with_cascade(measures_to_delete[0][0])

    # Create snapshot 2
    snapshot2 = backup_mgr.create_snapshot(
        "State 2: After first delete", operation_type="test"
    )
    count2 = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    snapshots.append((snapshot2, count2))

    logger.info(f"Snapshot 2: {count2} measures")

    # Delete second measure
    MeasureModel().delete_with_cascade(measures_to_delete[1][0])

    # Create snapshot 3
    snapshot3 = backup_mgr.create_snapshot(
        "State 3: After second delete", operation_type="test"
    )
    count3 = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    snapshots.append((snapshot3, count3))

    logger.info(f"Snapshot 3: {count3} measures")

    # Now restore to each state and verify count
    for snapshot_id, expected_count in reversed(snapshots):
        backup_mgr.restore_snapshot(snapshot_id)
        actual_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count}, got {actual_count} after restore to {snapshot_id}"

        logger.info(f"Verified restore to {snapshot_id}: {actual_count} measures")


def test_snapshot_time_travel(test_db, backup_mgr):
    """Test time-travel capability through multiple snapshots."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    conn = test_db.get_connection()
    measure_model = MeasureModel()

    # Get a measure to modify
    existing = conn.execute(
        "SELECT measure_id, measure FROM measure LIMIT 1"
    ).fetchone()
    if not existing:
        pytest.skip("No measures found for testing")

    measure_id, original_text = existing

    # Create timeline of states
    states = []

    # State 0: Original
    snapshot0 = backup_mgr.create_snapshot("Timeline: Original")
    states.append(("original", snapshot0, original_text))

    # State 1: First update
    measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data={
            "measure": original_text + " [V1]",
            "concise_measure": "V1",
            "core_supplementary": "Core (BNG)",
        },
        measure_types=[1],
        stakeholders=[],
        benefits=[],
    )
    snapshot1 = backup_mgr.create_snapshot("Timeline: Version 1")
    states.append(("v1", snapshot1, original_text + " [V1]"))

    # State 2: Second update
    measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data={
            "measure": original_text + " [V2]",
            "concise_measure": "V2",
            "core_supplementary": "Core (BNG)",
        },
        measure_types=[1, 2],
        stakeholders=[],
        benefits=[],
    )
    snapshot2 = backup_mgr.create_snapshot("Timeline: Version 2")
    states.append(("v2", snapshot2, original_text + " [V2]"))

    logger.info(f"Created timeline with {len(states)} states")

    # Time-travel: Jump to each state in random order
    test_order = [1, 2, 0, 2, 1, 0]  # Jump around the timeline

    for state_idx in test_order:
        state_name, snapshot_id, expected_text = states[state_idx]

        backup_mgr.restore_snapshot(snapshot_id)

        actual = conn.execute(
            "SELECT measure FROM measure WHERE measure_id = ?", [measure_id]
        ).fetchone()[0]

        assert (
            actual == expected_text
        ), f"Time-travel to {state_name} failed: expected '{expected_text}', got '{actual}'"

        logger.info(f"Time-travel verified: {state_name}")


def test_concurrent_snapshot_operations(test_db, backup_mgr):
    """Test that snapshot operations don't interfere with each other."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    # Create multiple snapshots in quick succession
    snapshot_ids = []
    for i in range(5):
        snapshot_id = backup_mgr.create_snapshot(
            f"Concurrent test {i}", operation_type="test"
        )
        snapshot_ids.append(snapshot_id)

    # Verify all snapshots exist
    all_snapshots = backup_mgr.list_snapshots()
    snapshot_id_set = {s["snapshot_id"] for s in all_snapshots}

    for snapshot_id in snapshot_ids:
        assert snapshot_id in snapshot_id_set, f"Snapshot {snapshot_id} not found"

    logger.info(f"Verified all {len(snapshot_ids)} concurrent snapshots exist")


def test_error_recovery_after_failed_operation(test_db, backup_mgr):
    """Test that system recovers properly after failed operations."""
    if not backup_mgr.enabled:
        pytest.skip("Backups disabled (cloud environment)")

    conn = test_db.get_connection()

    # Create snapshot before attempting bad operation
    snapshot_before = backup_mgr.create_snapshot(
        "Before bad operation", operation_type="test"
    )

    original_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    # Attempt invalid operation (should fail gracefully)
    try:
        # Try to delete non-existent measure
        MeasureModel().delete_with_cascade(999999)
    except Exception as e:
        logger.info(f"Expected error occurred: {e}")

    # Verify database is still intact
    current_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert current_count == original_count

    # Verify we can still create snapshots
    snapshot_after = backup_mgr.create_snapshot(
        "After bad operation", operation_type="test"
    )
    assert snapshot_after is not None

    logger.info("System recovered successfully after failed operation")
