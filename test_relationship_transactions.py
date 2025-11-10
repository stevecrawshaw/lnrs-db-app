"""Test relationship operations with transactions."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import db
from config.logging_config import setup_logging
from models.relationship import RelationshipModel

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def test_create_and_delete_map_link():
    """Test creating and deleting a MAP link."""
    print("\n" + "=" * 80)
    print("TEST 1: Create and Delete MAP Link (Transactional)")
    print("=" * 80 + "\n")

    model = RelationshipModel()
    conn = db.get_connection()

    # Find a measure, area, and priority that don't have a link yet
    query = """
        SELECT m.measure_id, a.area_id, p.priority_id
        FROM measure m
        CROSS JOIN area a
        CROSS JOIN priority p
        WHERE NOT EXISTS (
            SELECT 1 FROM measure_area_priority map
            WHERE map.measure_id = m.measure_id
            AND map.area_id = a.area_id
            AND map.priority_id = p.priority_id
        )
        LIMIT 1
    """

    result = conn.execute(query).fetchone()
    if not result:
        print("⚠️  No available combinations for testing - all links exist")
        return True

    measure_id, area_id, priority_id = result
    print(f"Test data: M{measure_id}-A{area_id}-P{priority_id}\n")

    # Step 1: Create the link
    print("Step 1: Creating MAP link...")
    try:
        model.create_measure_area_priority_link(measure_id, area_id, priority_id)
        print(f"✓ Created MAP link: M{measure_id}-A{area_id}-P{priority_id}")
    except Exception as e:
        print(f"❌ Failed to create link: {e}")
        return False

    # Verify link exists
    exists = model.link_exists_measure_area_priority(measure_id, area_id, priority_id)
    assert exists, "Link should exist after creation"
    print(f"✓ Verified link exists\n")

    # Step 2: Delete the link (transactional - 2 DELETEs)
    print("Step 2: Deleting MAP link (transactional)...")
    try:
        model.delete_measure_area_priority_link(measure_id, area_id, priority_id)
        print(f"✓ Deleted MAP link: M{measure_id}-A{area_id}-P{priority_id}")
    except Exception as e:
        print(f"❌ Failed to delete link: {e}")
        return False

    # Verify link doesn't exist
    exists = model.link_exists_measure_area_priority(measure_id, area_id, priority_id)
    assert not exists, "Link should not exist after deletion"
    print(f"✓ Verified link deleted\n")

    print("✓ TEST 1 PASSED\n")
    return True


def test_bulk_create_map_links():
    """Test bulk creating MAP links with transaction."""
    print("=" * 80)
    print("TEST 2: Bulk Create MAP Links (Atomic Transaction)")
    print("=" * 80 + "\n")

    model = RelationshipModel()
    conn = db.get_connection()

    # Find 2 measures, 2 areas, 2 priorities that don't have links
    query = """
        WITH available_combos AS (
            SELECT m.measure_id, a.area_id, p.priority_id
            FROM measure m
            CROSS JOIN area a
            CROSS JOIN priority p
            WHERE NOT EXISTS (
                SELECT 1 FROM measure_area_priority map
                WHERE map.measure_id = m.measure_id
                AND map.area_id = a.area_id
                AND map.priority_id = p.priority_id
            )
            LIMIT 10
        )
        SELECT measure_id, area_id, priority_id
        FROM available_combos
    """

    results = conn.execute(query).fetchall()
    if len(results) < 4:
        print(f"⚠️  Only {len(results)} available combinations (need 4 for test)")
        if len(results) == 0:
            return True

    # Take first 2 of each to create 2x2x2 = 8 combinations
    measure_ids = list(set([r[0] for r in results[:4]]))[:2]
    area_ids = list(set([r[1] for r in results[:4]]))[:2]
    priority_ids = list(set([r[2] for r in results[:4]]))[:2]

    print(f"Creating bulk links:")
    print(f"  Measures: {measure_ids}")
    print(f"  Areas: {area_ids}")
    print(f"  Priorities: {priority_ids}")
    print(f"  Expected combinations: {len(measure_ids) * len(area_ids) * len(priority_ids)}\n")

    # Count before
    before_count = conn.execute("SELECT COUNT(*) FROM measure_area_priority").fetchone()[0]

    # Bulk create
    print("Executing bulk create (atomic transaction)...")
    try:
        created, skipped = model.bulk_create_measure_area_priority_links(
            measure_ids, area_ids, priority_ids
        )
        print(f"✓ Transaction completed: {created} created, {len(skipped)} skipped")
    except Exception as e:
        print(f"❌ Bulk create failed: {e}")
        return False

    # Count after
    after_count = conn.execute("SELECT COUNT(*) FROM measure_area_priority").fetchone()[0]
    actual_created = after_count - before_count

    print(f"\nVerification:")
    print(f"  Before: {before_count} links")
    print(f"  After: {after_count} links")
    print(f"  Created: {actual_created}")

    assert actual_created == created, f"Count mismatch: {actual_created} != {created}"
    print(f"✓ Count verified\n")

    # Cleanup - delete what we created
    print("Cleanup: Deleting created links...")
    deleted = 0
    for m in measure_ids:
        for a in area_ids:
            for p in priority_ids:
                if model.link_exists_measure_area_priority(m, a, p):
                    model.delete_measure_area_priority_link(m, a, p)
                    deleted += 1

    print(f"✓ Cleaned up {deleted} links\n")

    print("✓ TEST 2 PASSED\n")
    return True


def test_map_link_with_grant():
    """Test MAP link deletion cascades to grants."""
    print("=" * 80)
    print("TEST 3: MAP Link Deletion Cascades to Grants (Transactional)")
    print("=" * 80 + "\n")

    model = RelationshipModel()
    conn = db.get_connection()

    # Find a MAP link that has grants
    query = """
        SELECT map.measure_id, map.area_id, map.priority_id,
               COUNT(mapg.grant_id) as grant_count
        FROM measure_area_priority map
        JOIN measure_area_priority_grant mapg
            ON map.measure_id = mapg.measure_id
            AND map.area_id = mapg.area_id
            AND map.priority_id = mapg.priority_id
        GROUP BY map.measure_id, map.area_id, map.priority_id
        HAVING COUNT(mapg.grant_id) > 0
        ORDER BY COUNT(mapg.grant_id) DESC
        LIMIT 1
    """

    result = conn.execute(query).fetchone()
    if not result:
        print("⚠️  No MAP links with grants found for testing")
        return True

    measure_id, area_id, priority_id, grant_count = result
    print(f"Test data: M{measure_id}-A{area_id}-P{priority_id}")
    print(f"  Grants linked: {grant_count}\n")

    # Verify grants exist
    grants_before = conn.execute(
        """SELECT COUNT(*) FROM measure_area_priority_grant
           WHERE measure_id = ? AND area_id = ? AND priority_id = ?""",
        [measure_id, area_id, priority_id],
    ).fetchone()[0]

    print(f"Step 1: Verify {grants_before} grants exist")
    assert grants_before == grant_count
    print(f"✓ Verified\n")

    # Delete MAP link (should cascade to grants in transaction)
    print(f"Step 2: Delete MAP link (should cascade {grants_before} grants atomically)...")
    try:
        model.delete_measure_area_priority_link(measure_id, area_id, priority_id)
        print(f"✓ MAP link deleted")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    # Verify grants are deleted
    grants_after = conn.execute(
        """SELECT COUNT(*) FROM measure_area_priority_grant
           WHERE measure_id = ? AND area_id = ? AND priority_id = ?""",
        [measure_id, area_id, priority_id],
    ).fetchone()[0]

    print(f"\nStep 3: Verify grants were deleted")
    print(f"  Grants before: {grants_before}")
    print(f"  Grants after: {grants_after}")

    assert grants_after == 0, f"Grants should be deleted, but {grants_after} remain"
    print(f"✓ All {grants_before} grants cascaded correctly\n")

    print("✓ TEST 3 PASSED\n")
    return True


def main():
    """Run all relationship operation tests."""
    print("\n" + "=" * 80)
    print("RELATIONSHIP OPERATIONS - TRANSACTION TESTS")
    print("Testing atomic operations on bridge/junction tables")
    print("=" * 80)

    tests = [
        test_create_and_delete_map_link,
        test_bulk_create_map_links,
        test_map_link_with_grant,
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
        print("\n✓ ALL RELATIONSHIP TRANSACTION TESTS PASSED")
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
