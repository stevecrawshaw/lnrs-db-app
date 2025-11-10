"""Test measure update operations with transactions."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import db
from config.logging_config import setup_logging
from models.measure import MeasureModel

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def test_update_measure_basic():
    """Test updating measure without relationships."""
    print("\n" + "=" * 80)
    print("TEST 1: Update Measure (Basic - No Relationships)")
    print("=" * 80 + "\n")

    model = MeasureModel()
    conn = db.get_connection()

    # Find a measure to update
    result = conn.execute("SELECT measure_id FROM measure LIMIT 1").fetchone()
    if not result:
        print("⚠️  No measures found for testing")
        return True

    measure_id = result[0]
    print(f"Test data: Measure ID {measure_id}\n")

    # Get original values
    original = model.get_by_id(measure_id)
    original_concise = original.get("concise_measure", "")

    print(f"Original concise_measure: {original_concise[:50] if original_concise else 'N/A'}...")

    # Step 1: Update measure data only
    print("\nStep 1: Updating measure data (atomic transaction)...")
    new_concise = f"[TEST UPDATE] {original_concise}" if original_concise else "[TEST UPDATE]"

    try:
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data={"concise_measure": new_concise},
            measure_types=None,  # Don't touch relationships
            stakeholders=None,
            benefits=None
        )
        print(f"✓ Updated measure {measure_id}")
    except Exception as e:
        print(f"❌ Failed to update: {e}")
        return False

    # Verify update
    updated = model.get_by_id(measure_id)
    assert updated["concise_measure"] == new_concise, "Update verification failed"
    print(f"✓ Verified updated value: {updated['concise_measure'][:50]}...\n")

    # Step 2: Restore original value
    print("Step 2: Restoring original value...")
    try:
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data={"concise_measure": original_concise},
            measure_types=None,
            stakeholders=None,
            benefits=None
        )
        print(f"✓ Restored measure {measure_id}\n")
    except Exception as e:
        print(f"❌ Failed to restore: {e}")
        return False

    print("✓ TEST 1 PASSED\n")
    return True


def test_update_measure_with_relationships():
    """Test updating measure with relationships atomically."""
    print("=" * 80)
    print("TEST 2: Update Measure with Relationships (Atomic Transaction)")
    print("=" * 80 + "\n")

    model = MeasureModel()
    conn = db.get_connection()

    # Find a measure with relationships
    query = """
        SELECT m.measure_id,
               COUNT(DISTINCT mht.measure_type_id) as type_count,
               COUNT(DISTINCT mhs.stakeholder_id) as stakeholder_count,
               COUNT(DISTINCT mhb.benefit_id) as benefit_count
        FROM measure m
        LEFT JOIN measure_has_type mht ON m.measure_id = mht.measure_id
        LEFT JOIN measure_has_stakeholder mhs ON m.measure_id = mhs.measure_id
        LEFT JOIN measure_has_benefits mhb ON m.measure_id = mhb.measure_id
        GROUP BY m.measure_id
        HAVING type_count > 0 OR stakeholder_count > 0 OR benefit_count > 0
        LIMIT 1
    """

    result = conn.execute(query).fetchone()
    if not result:
        print("⚠️  No measures with relationships found for testing")
        return True

    measure_id, original_type_count, original_stakeholder_count, original_benefit_count = result
    print(f"Test data: Measure ID {measure_id}")
    print(f"  Original types: {original_type_count}")
    print(f"  Original stakeholders: {original_stakeholder_count}")
    print(f"  Original benefits: {original_benefit_count}\n")

    # Store original relationships
    original_types = conn.execute(
        "SELECT measure_type_id FROM measure_has_type WHERE measure_id = ? ORDER BY measure_type_id",
        [measure_id]
    ).fetchall()
    original_type_ids = [t[0] for t in original_types]

    original_stakeholders = conn.execute(
        "SELECT stakeholder_id FROM measure_has_stakeholder WHERE measure_id = ? ORDER BY stakeholder_id",
        [measure_id]
    ).fetchall()
    original_stakeholder_ids = [s[0] for s in original_stakeholders]

    original_benefits = conn.execute(
        "SELECT benefit_id FROM measure_has_benefits WHERE measure_id = ? ORDER BY benefit_id",
        [measure_id]
    ).fetchall()
    original_benefit_ids = [b[0] for b in original_benefits]

    # Get available types/stakeholders/benefits for replacement
    available_types = conn.execute("SELECT measure_type_id FROM measure_type LIMIT 3").fetchall()
    new_type_ids = [t[0] for t in available_types if t[0] not in original_type_ids][:2]

    available_stakeholders = conn.execute("SELECT stakeholder_id FROM stakeholder LIMIT 3").fetchall()
    new_stakeholder_ids = [s[0] for s in available_stakeholders if s[0] not in original_stakeholder_ids][:2]

    available_benefits = conn.execute("SELECT benefit_id FROM benefits LIMIT 3").fetchall()
    new_benefit_ids = [b[0] for b in available_benefits if b[0] not in original_benefit_ids][:2]

    print(f"Step 1: Updating measure with NEW relationships (atomic transaction)...")
    print(f"  New types: {new_type_ids}")
    print(f"  New stakeholders: {new_stakeholder_ids}")
    print(f"  New benefits: {new_benefit_ids}\n")

    # Update with new relationships
    try:
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data={"concise_measure": "[TEST] Updated with relationships"},
            measure_types=new_type_ids if new_type_ids else None,
            stakeholders=new_stakeholder_ids if new_stakeholder_ids else None,
            benefits=new_benefit_ids if new_benefit_ids else None
        )
        print(f"✓ Updated measure {measure_id} with new relationships")
    except Exception as e:
        print(f"❌ Failed to update: {e}")
        return False

    # Verify new relationships
    new_type_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    new_stakeholder_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_stakeholder WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    new_benefit_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_benefits WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]

    print(f"\nVerification:")
    print(f"  Type count: {original_type_count} → {new_type_count}")
    print(f"  Stakeholder count: {original_stakeholder_count} → {new_stakeholder_count}")
    print(f"  Benefit count: {original_benefit_count} → {new_benefit_count}")

    expected_types = len(new_type_ids) if new_type_ids else 0
    expected_stakeholders = len(new_stakeholder_ids) if new_stakeholder_ids else 0
    expected_benefits = len(new_benefit_ids) if new_benefit_ids else 0

    assert new_type_count == expected_types, f"Type count mismatch: {new_type_count} != {expected_types}"
    assert new_stakeholder_count == expected_stakeholders, f"Stakeholder count mismatch: {new_stakeholder_count} != {expected_stakeholders}"
    assert new_benefit_count == expected_benefits, f"Benefit count mismatch: {new_benefit_count} != {expected_benefits}"
    print(f"✓ Verified new relationship counts\n")

    # Step 2: Restore original relationships
    print(f"Step 2: Restoring original relationships...")
    print(f"  Original types: {original_type_ids}")
    print(f"  Original stakeholders: {original_stakeholder_ids}")
    print(f"  Original benefits: {original_benefit_ids}\n")

    try:
        original_measure = model.get_by_id(measure_id)
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data={"concise_measure": original_measure.get("concise_measure")},
            measure_types=original_type_ids if original_type_ids else None,
            stakeholders=original_stakeholder_ids if original_stakeholder_ids else None,
            benefits=original_benefit_ids if original_benefit_ids else None
        )
        print(f"✓ Restored measure {measure_id} to original state\n")
    except Exception as e:
        print(f"❌ Failed to restore: {e}")
        return False

    # Verify restoration
    restored_type_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    restored_stakeholder_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_stakeholder WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    restored_benefit_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_benefits WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]

    assert restored_type_count == original_type_count
    assert restored_stakeholder_count == original_stakeholder_count
    assert restored_benefit_count == original_benefit_count
    print(f"✓ Verified restoration complete\n")

    print("✓ TEST 2 PASSED\n")
    return True


def test_update_measure_clear_relationships():
    """Test clearing all relationships atomically."""
    print("=" * 80)
    print("TEST 3: Clear All Relationships (Atomic Transaction)")
    print("=" * 80 + "\n")

    model = MeasureModel()
    conn = db.get_connection()

    # Find a measure with relationships
    query = """
        SELECT m.measure_id,
               COUNT(DISTINCT mht.measure_type_id) as type_count
        FROM measure m
        JOIN measure_has_type mht ON m.measure_id = mht.measure_id
        GROUP BY m.measure_id
        HAVING type_count > 0
        LIMIT 1
    """

    result = conn.execute(query).fetchone()
    if not result:
        print("⚠️  No measures with types found for testing")
        return True

    measure_id, original_count = result
    print(f"Test data: Measure ID {measure_id}")
    print(f"  Original types: {original_count}\n")

    # Store original type IDs
    original_types = conn.execute(
        "SELECT measure_type_id FROM measure_has_type WHERE measure_id = ? ORDER BY measure_type_id",
        [measure_id]
    ).fetchall()
    original_type_ids = [t[0] for t in original_types]

    # Step 1: Clear all type relationships
    print("Step 1: Clearing all type relationships (passing empty list)...")
    try:
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data=None,  # Don't update measure data
            measure_types=[],   # Empty list = clear all
            stakeholders=None,  # None = don't touch
            benefits=None
        )
        print(f"✓ Cleared types for measure {measure_id}")
    except Exception as e:
        print(f"❌ Failed to clear: {e}")
        return False

    # Verify cleared
    cleared_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]

    print(f"\nVerification:")
    print(f"  Type count: {original_count} → {cleared_count}")
    assert cleared_count == 0, f"Types not cleared: {cleared_count} remain"
    print(f"✓ Verified all types cleared\n")

    # Step 2: Restore original types
    print("Step 2: Restoring original types...")
    try:
        model.update_with_relationships(
            measure_id=measure_id,
            measure_data=None,
            measure_types=original_type_ids,
            stakeholders=None,
            benefits=None
        )
        print(f"✓ Restored {len(original_type_ids)} types\n")
    except Exception as e:
        print(f"❌ Failed to restore: {e}")
        return False

    # Verify restoration
    restored_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    assert restored_count == original_count
    print(f"✓ Verified restoration: {restored_count} types restored\n")

    print("✓ TEST 3 PASSED\n")
    return True


def main():
    """Run all measure update tests."""
    print("\n" + "=" * 80)
    print("MEASURE UPDATE OPERATIONS - TRANSACTION TESTS")
    print("Testing atomic update operations with relationships")
    print("=" * 80)

    tests = [
        test_update_measure_basic,
        test_update_measure_with_relationships,
        test_update_measure_clear_relationships,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ TEST FAILED WITH EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\n✓ Passed: {passed}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
        return 1
    else:
        print("\n✓ ALL MEASURE UPDATE TESTS PASSED")
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
