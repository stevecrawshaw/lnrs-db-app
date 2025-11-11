"""Test measure delete with cascade using sequential approach."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import db
from config.logging_config import setup_logging
from models.measure import MeasureModel

# Setup logging to see detailed output
setup_logging()
logger = logging.getLogger(__name__)


def test_measure_delete():
    """Test measure deletion with detailed verification."""
    print("\n" + "=" * 80)
    print("TESTING MEASURE DELETE WITH CASCADE (SEQUENTIAL APPROACH)")
    print("=" * 80 + "\n")

    model = MeasureModel()
    conn = db.get_connection()

    # Step 1: Find a measure with multiple relationships
    print("Step 1: Finding a measure with relationships...")
    query = """
        SELECT
            m.measure_id,
            m.measure,
            (SELECT COUNT(*) FROM measure_has_type WHERE measure_id = m.measure_id) as type_count,
            (SELECT COUNT(*) FROM measure_has_stakeholder WHERE measure_id = m.measure_id) as stakeholder_count,
            (SELECT COUNT(*) FROM measure_area_priority_grant WHERE measure_id = m.measure_id) as grant_count,
            (SELECT COUNT(*) FROM measure_area_priority WHERE measure_id = m.measure_id) as map_count,
            (SELECT COUNT(*) FROM measure_has_benefits WHERE measure_id = m.measure_id) as benefit_count,
            (SELECT COUNT(*) FROM measure_has_species WHERE measure_id = m.measure_id) as species_count
        FROM measure m
        WHERE EXISTS (SELECT 1 FROM measure_area_priority_grant WHERE measure_id = m.measure_id)
        LIMIT 1
    """
    result = conn.execute(query).fetchone()

    if not result:
        print("❌ No measures found with grant relationships. Creating test data...")
        # If no suitable measure exists, we'll need to create one or skip
        print("⚠️  Skipping test - no suitable test data")
        return

    measure_id = result[0]
    measure_name = result[1]
    type_count = result[2]
    stakeholder_count = result[3]
    grant_count = result[4]
    map_count = result[5]
    benefit_count = result[6]
    species_count = result[7]

    print(f"\n✓ Found measure: ID={measure_id}, Name='{measure_name}'")
    print(f"  Relationships:")
    print(f"    - Types: {type_count}")
    print(f"    - Stakeholders: {stakeholder_count}")
    print(f"    - Grants: {grant_count}")
    print(f"    - Area-Priority links: {map_count}")
    print(f"    - Benefits: {benefit_count}")
    print(f"    - Species: {species_count}")

    total_relationships = (
        type_count + stakeholder_count + grant_count + map_count + benefit_count + species_count
    )
    print(f"  Total relationships: {total_relationships}")

    # Step 2: Verify measure exists
    print(f"\nStep 2: Verifying measure {measure_id} exists...")
    measure_check = conn.execute(
        "SELECT COUNT(*) FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]
    assert measure_check == 1, f"Measure {measure_id} should exist"
    print(f"✓ Measure {measure_id} exists")

    # Step 3: Execute delete
    print(f"\nStep 3: Deleting measure {measure_id} with sequential cascade...")
    print("-" * 80)
    try:
        result = model.delete_with_cascade(measure_id)
        print("-" * 80)
        print(f"✓ Delete completed successfully: {result}")
    except Exception as e:
        print("-" * 80)
        print(f"❌ Delete failed: {e}")
        raise

    # Step 4: Verify measure is deleted
    print(f"\nStep 4: Verifying measure {measure_id} is deleted...")
    measure_check = conn.execute(
        "SELECT COUNT(*) FROM measure WHERE measure_id = ?", [measure_id]
    ).fetchone()[0]
    assert measure_check == 0, f"Measure {measure_id} should be deleted"
    print(f"✓ Measure {measure_id} is deleted")

    # Step 5: Verify all relationships are deleted
    print(f"\nStep 5: Verifying all relationships are deleted...")

    checks = [
        ("measure_has_type", type_count),
        ("measure_has_stakeholder", stakeholder_count),
        ("measure_area_priority_grant", grant_count),
        ("measure_area_priority", map_count),
        ("measure_has_benefits", benefit_count),
        ("measure_has_species", species_count),
    ]

    all_clean = True
    for table, expected_count in checks:
        actual_count = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE measure_id = ?", [measure_id]
        ).fetchone()[0]
        status = "✓" if actual_count == 0 else "❌"
        print(f"  {status} {table}: {actual_count} records (had {expected_count})")
        if actual_count != 0:
            all_clean = False

    if all_clean:
        print(f"\n✓ All {total_relationships} relationships successfully deleted")
    else:
        print("\n❌ Some relationships were not deleted!")
        raise AssertionError("Not all relationships were deleted")

    print("\n" + "=" * 80)
    print("✓ MEASURE DELETE TEST PASSED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        test_measure_delete()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
