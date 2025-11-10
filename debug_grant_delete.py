"""Debug script to investigate grant delete issue."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logging

setup_logging(log_level="DEBUG")

from config.database import db
from models.grant import GrantModel

# The grant that's failing to delete
GRANT_ID = "WWEF"

print("=" * 70)
print(f"INVESTIGATING GRANT DELETE ISSUE FOR: {GRANT_ID}")
print("=" * 70)

# 1. Check if grant exists
print("\n1. Checking if grant exists...")
grant_model = GrantModel()
grant = grant_model.get_by_id(GRANT_ID)
if grant:
    print(f"   ✓ Grant found: {grant['grant_name']}")
    print(f"     Scheme: {grant['grant_scheme']}")
else:
    print(f"   ✗ Grant {GRANT_ID} not found!")
    sys.exit(1)

# 2. Check measure_area_priority_grant references
print("\n2. Checking measure_area_priority_grant references...")
conn = db.get_connection()
result = conn.execute(
    "SELECT COUNT(*) FROM measure_area_priority_grant WHERE grant_id = ?", [GRANT_ID]
).fetchone()
ref_count = result[0]
print(f"   Found {ref_count} references in measure_area_priority_grant")

if ref_count > 0:
    # Show some examples
    refs = conn.execute(
        """SELECT measure_id, area_id, priority_id
           FROM measure_area_priority_grant
           WHERE grant_id = ?
           LIMIT 5""",
        [GRANT_ID],
    ).fetchall()
    print(f"   Example references:")
    for r in refs:
        print(f"     - measure_id={r[0]}, area_id={r[1]}, priority_id={r[2]}")

# 3. Check foreign key constraints on grant_table
print("\n3. Checking foreign key constraints...")
try:
    fk_info = conn.execute(
        """
        SELECT
            table_name,
            constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
          AND table_name = 'grant_table'
    """
    ).fetchall()

    if fk_info:
        print(f"   Foreign keys ON grant_table:")
        for fk in fk_info:
            print(f"     - {fk[0]}: {fk[1]}")
    else:
        print("   No FK constraints found on grant_table")

    # Check FKs that reference grant_table
    fk_refs = conn.execute(
        """
        SELECT
            table_name,
            constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
    """
    ).fetchall()

    print(f"\n   All foreign key constraints in database:")
    referencing_grant = []
    for fk in fk_refs:
        print(f"     - Table: {fk[0]}, Constraint: {fk[1]}")
        # Check if this FK references grant_table
        # Note: DuckDB's information_schema might not have detailed FK info

except Exception as e:
    print(f"   Could not retrieve FK info: {e}")

# 4. Check table schema for grant_table
print("\n4. Checking grant_table schema...")
schema = conn.execute("DESCRIBE grant_table").fetchall()
print("   Columns:")
for col in schema:
    print(f"     - {col[0]}: {col[1]}")

# 5. Test manual delete sequence
print("\n5. Testing manual delete sequence...")
print("   (This will NOT be committed - using a transaction we'll rollback)")

try:
    conn.begin()

    # Step 1: Delete from child table
    print("   Step 1: Deleting from measure_area_priority_grant...")
    result = conn.execute(
        "DELETE FROM measure_area_priority_grant WHERE grant_id = ?", [GRANT_ID]
    )
    print(f"   ✓ Deleted {result.fetchone() if hasattr(result, 'fetchone') else 'N/A'}")

    # Check if any remain
    remaining = conn.execute(
        "SELECT COUNT(*) FROM measure_area_priority_grant WHERE grant_id = ?",
        [GRANT_ID],
    ).fetchone()[0]
    print(f"   Remaining references: {remaining}")

    # Step 2: Try to delete from grant_table
    print("   Step 2: Attempting to delete from grant_table...")
    result = conn.execute("DELETE FROM grant_table WHERE grant_id = ?", [GRANT_ID])
    print(f"   ✓ Delete succeeded!")

    conn.rollback()
    print("   ✓ Transaction rolled back (no changes made)")

except Exception as e:
    conn.rollback()
    print(f"   ✗ Error during manual delete: {e}")
    print("   ✓ Transaction rolled back (no changes made)")

# 6. Check for any other tables that might reference grants
print("\n6. Searching for other potential grant references...")
tables = conn.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
).fetchall()

print(f"   Checking {len(tables)} tables for grant_id columns...")
tables_with_grant_id = []

for table in tables:
    table_name = table[0]
    try:
        columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
        for col in columns:
            if "grant" in col[0].lower():
                tables_with_grant_id.append((table_name, col[0]))
    except:
        pass

if tables_with_grant_id:
    print(f"   Found grant-related columns:")
    for table, column in tables_with_grant_id:
        print(f"     - {table}.{column}")
else:
    print("   No other tables with grant-related columns found")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
