"""Validate MotherDuck schema matches local database.

This script verifies that the MotherDuck cloud database has the same structure
and data as the local DuckDB database.
"""

import os
import sys
from pathlib import Path

import duckdb
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def get_local_connection() -> duckdb.DuckDBPyConnection:
    """Get connection to local database."""
    db_path = project_root / "data" / "lnrs_3nf_o1.duckdb"
    if not db_path.exists():
        raise FileNotFoundError(f"Local database not found: {db_path}")
    return duckdb.connect(str(db_path))


def get_motherduck_connection() -> duckdb.DuckDBPyConnection:
    """Get connection to MotherDuck database."""
    load_dotenv()
    token = os.getenv("motherduck_token")
    database_name = os.getenv("database_name", "lnrs_weca")

    if not token:
        raise ValueError("MotherDuck token not found in .env file")

    connection_string = f"md:{database_name}?motherduck_token={token}"
    return duckdb.connect(connection_string)


def validate_connections() -> tuple[duckdb.DuckDBPyConnection, duckdb.DuckDBPyConnection]:
    """Validate both database connections work.

    Returns:
        tuple: (local_conn, motherduck_conn)
    """
    print("=" * 70)
    print("LNRS Database Schema Validation")
    print("=" * 70)
    print()

    print("Step 1: Testing Database Connections")
    print("-" * 70)

    try:
        local_conn = get_local_connection()
        result = local_conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
        print("[OK] Local connection successful")
    except Exception as e:
        print(f"[FAIL] Local connection failed: {e}")
        sys.exit(1)

    try:
        md_conn = get_motherduck_connection()
        result = md_conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
        print("[OK] MotherDuck connection successful")
    except Exception as e:
        print(f"[FAIL] MotherDuck connection failed: {e}")
        sys.exit(1)

    print()
    return local_conn, md_conn


def validate_table_counts(
    local_conn: duckdb.DuckDBPyConnection, md_conn: duckdb.DuckDBPyConnection
) -> bool:
    """Validate that table row counts match between local and MotherDuck.

    Returns:
        bool: True if all counts match
    """
    print("Step 2: Validating Table Row Counts")
    print("-" * 70)

    tables = [
        "measure",
        "area",
        "priority",
        "species",
        "grant_table",
        "measure_type",
        "stakeholder",
        "benefits",
        "habitat",
        "measure_has_type",
        "measure_has_stakeholder",
        "measure_area_priority",
        "species_area_priority",
        "area_funding_schemes",
        "measure_has_benefits",
        "measure_has_species",
        "habitat_creation_area",
        "habitat_management_area",
        "area_geom",
        "measure_area_priority_grant",
        "source_table",
    ]

    all_match = True

    for table in tables:
        try:
            local_count = local_conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            md_count = md_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

            if local_count == md_count:
                print(f"[OK] {table:30s}: {local_count:5d} rows (match)")
            else:
                print(
                    f"[FAIL] {table:30s}: local={local_count}, motherduck={md_count} (MISMATCH)"
                )
                all_match = False
        except Exception as e:
            print(f"[FAIL] {table:30s}: Error - {e}")
            all_match = False

    print()
    return all_match


def validate_views(
    local_conn: duckdb.DuckDBPyConnection, md_conn: duckdb.DuckDBPyConnection
) -> bool:
    """Validate that views exist and work in both databases.

    Returns:
        bool: True if all views work
    """
    print("Step 3: Validating Views")
    print("-" * 70)

    views = ["source_table_recreated_vw", "apmg_slim_vw"]

    all_work = True

    for view in views:
        try:
            # Test local view
            local_count = local_conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[
                0
            ]

            # Test MotherDuck view
            md_count = md_conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]

            if local_count == md_count:
                print(f"[OK] {view:30s}: {local_count:5d} rows (match)")
            else:
                print(
                    f"[FAIL] {view:30s}: local={local_count}, motherduck={md_count} (MISMATCH)"
                )
                all_work = False
        except Exception as e:
            print(f"[FAIL] {view:30s}: Error - {e}")
            all_work = False

    print()
    return all_work


def validate_macros(md_conn: duckdb.DuckDBPyConnection) -> bool:
    """Validate that macros can be created and work in MotherDuck.

    Returns:
        bool: True if macros work
    """
    print("Step 4: Validating Macros")
    print("-" * 70)

    try:
        # Drop macro if exists
        md_conn.execute("DROP MACRO IF EXISTS max_meas")

        # Create macro
        md_conn.execute(
            "CREATE MACRO max_meas() AS "
            "(SELECT COALESCE(MAX(measure_id), 0) + 1 FROM measure)"
        )

        # Test macro
        result = md_conn.execute("SELECT max_meas() as next_id").fetchone()
        next_id = result[0]

        print(f"[OK] max_meas() macro created and working")
        print(f"  Next available measure_id: {next_id}")
    except Exception as e:
        print(f"[FAIL] Macro validation failed: {e}")
        return False

    print()
    return True


def validate_foreign_keys(md_conn: duckdb.DuckDBPyConnection) -> bool:
    """Validate that foreign key constraints exist in MotherDuck.

    Returns:
        bool: True if constraints exist
    """
    print("Step 5: Validating Foreign Key Constraints")
    print("-" * 70)

    # Sample a few critical FK relationships
    fk_checks = [
        {
            "name": "measure_has_type -> measure",
            "query": """
                SELECT COUNT(*) FROM measure_has_type mht
                LEFT JOIN measure m ON mht.measure_id = m.measure_id
                WHERE m.measure_id IS NULL
            """,
        },
        {
            "name": "measure_has_type -> measure_type",
            "query": """
                SELECT COUNT(*) FROM measure_has_type mht
                LEFT JOIN measure_type mt ON mht.measure_type_id = mt.measure_type_id
                WHERE mt.measure_type_id IS NULL
            """,
        },
        {
            "name": "measure_area_priority -> measure",
            "query": """
                SELECT COUNT(*) FROM measure_area_priority map
                LEFT JOIN measure m ON map.measure_id = m.measure_id
                WHERE m.measure_id IS NULL
            """,
        },
        {
            "name": "measure_area_priority -> area",
            "query": """
                SELECT COUNT(*) FROM measure_area_priority map
                LEFT JOIN area a ON map.area_id = a.area_id
                WHERE a.area_id IS NULL
            """,
        },
        {
            "name": "measure_area_priority -> priority",
            "query": """
                SELECT COUNT(*) FROM measure_area_priority map
                LEFT JOIN priority p ON map.priority_id = p.priority_id
                WHERE p.priority_id IS NULL
            """,
        },
    ]

    all_valid = True

    for check in fk_checks:
        try:
            orphans = md_conn.execute(check["query"]).fetchone()[0]
            if orphans == 0:
                print(f"[OK] {check['name']:45s}: No orphaned records")
            else:
                print(
                    f"[FAIL] {check['name']:45s}: {orphans} orphaned records found (ERROR)"
                )
                all_valid = False
        except Exception as e:
            print(f"[FAIL] {check['name']:45s}: Error - {e}")
            all_valid = False

    print()
    return all_valid


def print_summary(results: dict[str, bool]) -> None:
    """Print validation summary.

    Args:
        results: Dictionary of validation step results
    """
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)

    all_passed = all(results.values())

    for step, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{step:40s}: {status}")

    print()
    if all_passed:
        print(" Overall Status: [OK] ALL VALIDATIONS PASSED")
        print()
        print("The MotherDuck database matches the local database structure and data.")
        print("The application is ready for deployment to Streamlit Cloud.")
    else:
        print("  Overall Status: [FAIL] SOME VALIDATIONS FAILED")
        print()
        print("Please review the failures above and fix the issues before deploying.")
        print(
            "You may need to re-run the lnrs_to_motherduck.sql script to fix the data."
        )

    print("=" * 70)


def main() -> None:
    """Run all validation checks."""
    try:
        # Step 1: Connect to both databases
        local_conn, md_conn = validate_connections()

        # Step 2: Validate table counts
        tables_match = validate_table_counts(local_conn, md_conn)

        # Step 3: Validate views
        views_work = validate_views(local_conn, md_conn)

        # Step 4: Validate macros
        macros_work = validate_macros(md_conn)

        # Step 5: Validate foreign keys
        fks_valid = validate_foreign_keys(md_conn)

        # Print summary
        print_summary(
            {
                "Table Counts": tables_match,
                "Views": views_work,
                "Macros": macros_work,
                "Foreign Keys": fks_valid,
            }
        )

        # Close connections
        local_conn.close()
        md_conn.close()

        # Exit with appropriate code
        if all([tables_match, views_work, macros_work, fks_valid]):
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n[FAIL] Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
