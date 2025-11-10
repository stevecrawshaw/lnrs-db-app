"""Test all entity delete operations to identify which need sequential approach."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import db
from config.logging_config import setup_logging
from models.area import AreaModel
from models.habitat import HabitatModel
from models.priority import PriorityModel
from models.species import SpeciesModel

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def test_entity_delete(entity_name, model_class, id_column, relationship_queries):
    """Test delete operation for a given entity.

    Args:
        entity_name: Name of the entity (e.g., "area", "priority")
        model_class: Model class to test
        id_column: Name of the ID column
        relationship_queries: Dict of {table_name: query} to count relationships

    Returns:
        dict: Test results with status and details
    """
    print(f"\n{'=' * 80}")
    print(f"TESTING {entity_name.upper()} DELETE")
    print(f"{'=' * 80}\n")

    model = model_class()
    conn = db.get_connection()

    # Find an entity with relationships
    print(f"Step 1: Finding {entity_name} with relationships...")

    # Get entity with most relationships - build subqueries
    subqueries = []
    for table in relationship_queries.keys():
        subqueries.append(f"(SELECT COUNT(*) FROM {table} WHERE {id_column} = e.{id_column})")
    count_queries = " + ".join(subqueries)

    find_query = f"""
        SELECT
            e.{id_column},
            {count_queries} as total_rels
        FROM {entity_name} e
        WHERE ({count_queries}) > 0
        ORDER BY total_rels DESC
        LIMIT 1
    """

    try:
        result = conn.execute(find_query).fetchone()
    except Exception as e:
        return {
            "status": "SKIPPED",
            "reason": f"Failed to find test data: {e}",
            "entity_name": entity_name,
        }

    if not result:
        return {
            "status": "SKIPPED",
            "reason": "No entities with relationships found",
            "entity_name": entity_name,
        }

    entity_id = result[0]
    total_rels = result[1]

    print(f"✓ Found {entity_name}: ID={entity_id}, Total relationships={total_rels}")

    # Get detailed relationship counts
    rel_counts = {}
    for table, query in relationship_queries.items():
        # Query already contains full SELECT statement
        count = conn.execute(query, [entity_id]).fetchone()[0]
        rel_counts[table] = count
        print(f"  - {table}: {count}")

    # Verify entity exists before delete
    check_query = f"SELECT COUNT(*) FROM {entity_name} WHERE {id_column} = ?"
    before_count = conn.execute(check_query, [entity_id]).fetchone()[0]
    assert before_count == 1, f"{entity_name} {entity_id} should exist before delete"

    # Attempt delete
    print(f"\nStep 2: Attempting delete of {entity_name} {entity_id}...")
    try:
        result = model.delete_with_cascade(entity_id)
        print(f"✓ Delete completed successfully")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Delete failed: {error_msg}")

        # Check if it's the FK constraint issue
        if "Constraint Error" in error_msg or "FOREIGN KEY" in error_msg:
            return {
                "status": "FAILED_FK_CONSTRAINT",
                "reason": "DuckDB FK constraint prevents transaction-based delete",
                "entity_name": entity_name,
                "entity_id": entity_id,
                "error": error_msg,
                "needs_sequential": True,
            }
        else:
            return {
                "status": "FAILED_OTHER",
                "reason": f"Unexpected error: {error_msg}",
                "entity_name": entity_name,
                "entity_id": entity_id,
                "error": error_msg,
            }

    # Verify entity is deleted
    after_count = conn.execute(check_query, [entity_id]).fetchone()[0]
    if after_count != 0:
        return {
            "status": "FAILED_INCOMPLETE",
            "reason": f"{entity_name} still exists after delete",
            "entity_name": entity_name,
            "entity_id": entity_id,
        }

    # Verify all relationships are deleted
    print(f"\nStep 3: Verifying all relationships are deleted...")
    all_clean = True
    for table, expected_count in rel_counts.items():
        check = f"SELECT COUNT(*) FROM {table} WHERE {id_column} = ?"
        actual = conn.execute(check, [entity_id]).fetchone()[0]
        status = "✓" if actual == 0 else "❌"
        print(f"  {status} {table}: {actual} records (had {expected_count})")
        if actual != 0:
            all_clean = False

    if not all_clean:
        return {
            "status": "FAILED_ORPHANED",
            "reason": "Some relationships not deleted (orphaned records)",
            "entity_name": entity_name,
            "entity_id": entity_id,
        }

    print(f"\n✓ {entity_name.upper()} DELETE TEST PASSED")
    return {
        "status": "PASSED",
        "entity_name": entity_name,
        "entity_id": entity_id,
        "total_relationships": total_rels,
        "needs_sequential": False,
    }


def main():
    """Run all delete tests."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE DELETE OPERATION TESTS")
    print("Testing which operations need sequential vs transactional approach")
    print("=" * 80)

    tests = [
        {
            "entity_name": "area",
            "model_class": AreaModel,
            "id_column": "area_id",
            "relationship_queries": {
                "measure_area_priority_grant": "SELECT COUNT(*) FROM measure_area_priority_grant WHERE area_id = ?",
                "measure_area_priority": "SELECT COUNT(*) FROM measure_area_priority WHERE area_id = ?",
                "species_area_priority": "SELECT COUNT(*) FROM species_area_priority WHERE area_id = ?",
                "area_funding_schemes": "SELECT COUNT(*) FROM area_funding_schemes WHERE area_id = ?",
                "habitat_creation_area": "SELECT COUNT(*) FROM habitat_creation_area WHERE area_id = ?",
                "habitat_management_area": "SELECT COUNT(*) FROM habitat_management_area WHERE area_id = ?",
            },
        },
        {
            "entity_name": "priority",
            "model_class": PriorityModel,
            "id_column": "priority_id",
            "relationship_queries": {
                "measure_area_priority_grant": "SELECT COUNT(*) FROM measure_area_priority_grant WHERE priority_id = ?",
                "measure_area_priority": "SELECT COUNT(*) FROM measure_area_priority WHERE priority_id = ?",
                "species_area_priority": "SELECT COUNT(*) FROM species_area_priority WHERE priority_id = ?",
            },
        },
        {
            "entity_name": "species",
            "model_class": SpeciesModel,
            "id_column": "species_id",
            "relationship_queries": {
                "species_area_priority": "SELECT COUNT(*) FROM species_area_priority WHERE species_id = ?",
                "measure_has_species": "SELECT COUNT(*) FROM measure_has_species WHERE species_id = ?",
            },
        },
        {
            "entity_name": "habitat",
            "model_class": HabitatModel,
            "id_column": "habitat_id",
            "relationship_queries": {
                "habitat_creation_area": "SELECT COUNT(*) FROM habitat_creation_area WHERE habitat_id = ?",
                "habitat_management_area": "SELECT COUNT(*) FROM habitat_management_area WHERE habitat_id = ?",
            },
        },
    ]

    results = []
    for test_config in tests:
        result = test_entity_delete(**test_config)
        results.append(result)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = [r for r in results if r["status"] == "PASSED"]
    failed_fk = [r for r in results if r["status"] == "FAILED_FK_CONSTRAINT"]
    failed_other = [
        r
        for r in results
        if r["status"]
        not in ["PASSED", "FAILED_FK_CONSTRAINT", "SKIPPED"]
    ]
    skipped = [r for r in results if r["status"] == "SKIPPED"]

    print(f"\n✓ PASSED (Transactions work): {len(passed)}")
    for r in passed:
        print(f"  - {r['entity_name']}: Deleted {r['total_relationships']} relationships")

    print(f"\n⚠️  FAILED (FK Constraint - Need Sequential): {len(failed_fk)}")
    for r in failed_fk:
        print(f"  - {r['entity_name']}: {r['reason']}")

    if failed_other:
        print(f"\n❌ FAILED (Other errors): {len(failed_other)}")
        for r in failed_other:
            print(f"  - {r['entity_name']}: {r['reason']}")

    if skipped:
        print(f"\n⊘  SKIPPED: {len(skipped)}")
        for r in skipped:
            print(f"  - {r['entity_name']}: {r['reason']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    need_sequential = [r for r in results if r.get("needs_sequential", False)]
    if need_sequential:
        print("\n⚠️  The following entities MUST be converted to sequential deletes:")
        for r in need_sequential:
            print(f"  - {r['entity_name']}: models/{r['entity_name']}.py")

    if passed:
        print("\n✓ The following entities can keep transaction-based deletes:")
        for r in passed:
            print(f"  - {r['entity_name']}: models/{r['entity_name']}.py")

    print("\n" + "=" * 80)

    # Return exit code
    if failed_other:
        print("❌ TESTS FAILED WITH UNEXPECTED ERRORS")
        return 1
    elif need_sequential:
        print(f"⚠️  {len(need_sequential)} ENTITIES NEED CONVERSION TO SEQUENTIAL")
        return 0
    else:
        print("✓ ALL TESTS PASSED")
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
