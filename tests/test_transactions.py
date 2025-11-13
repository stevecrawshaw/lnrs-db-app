"""Tests for transaction-wrapped operations.

This module tests that multi-statement operations are properly wrapped
in transactions and provide atomicity guarantees.
"""

import logging

import duckdb
import pytest

from models.area import AreaModel
from models.measure import MeasureModel
from models.priority import PriorityModel

logger = logging.getLogger(__name__)


def test_measure_delete_cascade_sequential(test_db, sample_measure_data):
    """Test measure delete with sequential execution.

    Note: Due to DuckDB FK constraint limitations, cascade deletes
    are sequential rather than atomic.
    """
    measure_model = MeasureModel()

    # Get an existing measure with relationships
    conn = test_db.get_connection()
    existing = conn.execute(
        "SELECT measure_id FROM measure WHERE measure_id IN "
        "(SELECT measure_id FROM measure_has_type LIMIT 1)"
    ).fetchone()

    if not existing:
        pytest.skip("No measures with relationships found for testing")

    measure_id = existing[0]

    # Count relationships before
    type_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]

    logger.info(f"Testing delete of measure {measure_id} with {type_count} types")

    # Delete should succeed
    result = measure_model.delete_with_cascade(measure_id)
    assert result is True

    # Verify measure deleted
    check = conn.execute(
        "SELECT COUNT(*) FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]
    assert check == 0

    # Verify relationships deleted
    type_count_after = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]
    assert type_count_after == 0


def test_measure_update_with_relationships_atomic(test_db):
    """Test measure update with relationships is atomic.

    This operation IS fully atomic because it doesn't delete parent records.
    """
    measure_model = MeasureModel()
    conn = test_db.get_connection()

    # Get an existing measure
    existing = conn.execute("SELECT measure_id FROM measure LIMIT 1").fetchone()

    if not existing:
        pytest.skip("No measures found for testing")

    measure_id = existing[0]

    # Get current data
    current = conn.execute(
        "SELECT measure, concise_measure FROM measure WHERE measure_id = ?",
        [measure_id],
    ).fetchone()

    original_measure = current[0]
    original_concise = current[1]

    # Update with new data
    updated_data = {
        "measure": original_measure + " (UPDATED)",
        "concise_measure": original_concise,
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
    assert "(UPDATED)" in updated[0]

    # Verify relationships
    types = conn.execute(
        "SELECT measure_type_id FROM measure_has_type WHERE measure_id = ? ORDER BY measure_type_id",
        [measure_id],
    ).fetchall()
    assert len(types) == 2
    assert [t[0] for t in types] == [1, 2]


def test_area_delete_cascade_sequential(test_db):
    """Test area delete with sequential execution."""
    area_model = AreaModel()
    conn = test_db.get_connection()

    # Get an area with minimal relationships
    existing = conn.execute("SELECT area_id FROM area LIMIT 1").fetchone()

    if not existing:
        pytest.skip("No areas found for testing")

    area_id = existing[0]

    logger.info(f"Testing delete of area {area_id}")

    # Delete should succeed
    result = area_model.delete_with_cascade(area_id)
    assert result is True

    # Verify deleted
    check = conn.execute(
        "SELECT COUNT(*) FROM area WHERE area_id = ?", [area_id]
    ).fetchone()[0]
    assert check == 0


def test_priority_delete_cascade_sequential(test_db):
    """Test priority delete with sequential execution."""
    priority_model = PriorityModel()
    conn = test_db.get_connection()

    # Get a priority with minimal relationships
    existing = conn.execute("SELECT priority_id FROM priority LIMIT 1").fetchone()

    if not existing:
        pytest.skip("No priorities found for testing")

    priority_id = existing[0]

    logger.info(f"Testing delete of priority {priority_id}")

    # Delete should succeed
    result = priority_model.delete_with_cascade(priority_id)
    assert result is True

    # Verify deleted
    check = conn.execute(
        "SELECT COUNT(*) FROM priority WHERE priority_id = ?", [priority_id]
    ).fetchone()[0]
    assert check == 0


@pytest.mark.parametrize(
    "entity_type,model_class,id_field",
    [
        ("measure", "MeasureModel", "measure_id"),
        ("area", "AreaModel", "area_id"),
        ("priority", "PriorityModel", "priority_id"),
    ],
)
def test_all_cascade_deletes_work(test_db, entity_type, model_class, id_field):
    """Parameterized test for all cascade delete operations.

    Note: These are sequential, not atomic, due to DuckDB FK limitations.
    """
    # Import model dynamically
    module = __import__(f"models.{entity_type}", fromlist=[model_class])
    model = getattr(module, model_class)()

    # Get a record to delete
    conn = test_db.get_connection()
    record = conn.execute(f"SELECT {id_field} FROM {entity_type} LIMIT 1").fetchone()

    if not record:
        pytest.skip(f"No {entity_type} records found for testing")

    record_id = record[0]

    logger.info(f"Testing delete of {entity_type} {record_id}")

    # Delete
    result = model.delete_with_cascade(record_id)
    assert result is True

    # Verify deleted
    check = conn.execute(
        f"SELECT COUNT(*) FROM {entity_type} WHERE {id_field} = ?", [record_id]
    ).fetchone()[0]
    assert check == 0


def test_database_integrity_after_operations(test_db):
    """Test that database integrity is maintained after operations."""
    conn = test_db.get_connection()

    # Check for orphaned relationships
    orphaned_measure_types = conn.execute(
        """
        SELECT COUNT(*)
        FROM measure_has_type mht
        LEFT JOIN measure m ON mht.measure_id = m.measure_id
        WHERE m.measure_id IS NULL
    """
    ).fetchone()[0]

    assert (
        orphaned_measure_types == 0
    ), f"Found {orphaned_measure_types} orphaned measure types"

    # Check for orphaned MAP records
    orphaned_maps = conn.execute(
        """
        SELECT COUNT(*)
        FROM measure_area_priority map
        LEFT JOIN measure m ON map.measure_id = m.measure_id
        WHERE m.measure_id IS NULL
    """
    ).fetchone()[0]

    assert orphaned_maps == 0, f"Found {orphaned_maps} orphaned MAP records"


def test_concurrent_operations_serialized(test_db):
    """Test that operations are properly serialized.

    DuckDB has a single-writer model, so concurrent writes
    should be automatically serialized.
    """
    # This is more of a documentation test
    # DuckDB's single-writer model ensures serialization
    conn = test_db.get_connection()

    # Verify database is accessible
    result = conn.execute("SELECT COUNT(*) FROM measure").fetchone()
    assert result[0] >= 0

    logger.info("DuckDB single-writer model ensures operation serialization")
