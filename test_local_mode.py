#%%
"""
Phase 5.1: Local Mode Testing Script

This script validates that the application works correctly in LOCAL mode.
Run this script with: uv run python test_local_mode.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Verify we're in LOCAL mode
print("=" * 60)
print("Phase 5.1: LOCAL MODE TESTING")
print("=" * 60)

# Import after loading environment
from config.database import db
from models.measure import MeasureModel

#%%
# Test 1: Connection Mode
print("\n[Test 1] Verifying LOCAL mode configuration...")
# Force connection to be established
db.test_connection()

conn_info = db.get_connection_info()
mode = conn_info.get("mode", "unknown")
database = conn_info.get("database", "unknown")
connected = conn_info.get("connected", False)

assert mode == "local", f"Expected 'local' mode, got '{mode}'"
assert connected, "Database should be connected"
print(f"[OK] Mode: {mode}")
print(f"[OK] Database: {database}")
print(f"[OK] Connected: {connected}")

#%%
# Test 2: Database Connection
print("\n[Test 2] Testing database connection...")
assert db.test_connection(), "Database connection test failed"
print("[OK] Database connection successful")

#%%
# Test 3: Read Operations - Table Counts
print("\n[Test 3] Testing read operations (table counts)...")
expected_counts = {
    "measure": (150, 200),  # Expected range
    "area": (60, 80),
    "priority": (30, 40),
    "species": (40, 60),
    "grant_table": (150, 200),
}

for table, (min_count, max_count) in expected_counts.items():
    count = db.get_table_count(table)
    assert min_count <= count <= max_count, f"{table} count {count} outside expected range [{min_count}, {max_count}]"
    print(f"[OK] {table}: {count} rows")

#%%
# Test 4: Read Operations - View Data
print("\n[Test 4] Testing view queries...")

# Test measure view
measure_model = MeasureModel()
all_measures = measure_model.get_all()
assert len(all_measures) > 0, "Should have measures in database"
print(f"[OK] Retrieved {len(all_measures)} measures via MeasureModel.get_all()")

# Test getting a specific measure
first_measure_id = int(all_measures[0, "measure_id"])  # Extract from polars DataFrame
single_measure = measure_model.get_by_id(first_measure_id)
assert single_measure is not None, f"Should retrieve measure {first_measure_id}"
print(f"[OK] Retrieved measure {first_measure_id}: {single_measure.get('measure', 'N/A')[:50]}...")

#%%
# Test 5: Macro Functionality
print("\n[Test 5] Testing macro functionality...")
result = db.execute_query("SELECT max_meas() AS next_id")
next_id = result.fetchone()[0]
assert next_id > 0, "max_meas() should return a positive number"
print(f"[OK] max_meas() macro works: next measure ID = {next_id}")

#%%
# Test 6-8: Write Operations (Manual SQL - verifying database supports writes)
print("\n[Test 6-8] Testing WRITE operations (manual SQL)...")
try:
    # Get next ID
    result = db.execute_query("SELECT max_meas() AS next_id")
    test_id = result.fetchone()[0]

    # Create test measure
    create_sql = """
    INSERT INTO measure (measure_id, measure, concise_measure)
    VALUES (?, ?, ?)
    """
    db.execute_query(create_sql, (test_id, "TEST MEASURE - Phase 5.1", "Test"))
    print(f"[OK] Created test measure with ID: {test_id}")

    # Verify creation
    verify_sql = "SELECT measure FROM measure WHERE measure_id = ?"
    result = db.execute_query(verify_sql, (test_id,))
    created_measure = result.fetchone()
    assert created_measure is not None, "Should retrieve created measure"
    print(f"[OK] Verified creation: {created_measure[0][:50]}...")

    # Update
    update_sql = "UPDATE measure SET measure = ? WHERE measure_id = ?"
    db.execute_query(update_sql, ("TEST MEASURE - UPDATED", test_id))
    result = db.execute_query(verify_sql, (test_id,))
    updated_measure = result.fetchone()[0]
    assert "UPDATED" in updated_measure, "Measure should be updated"
    print(f"[OK] Updated and verified: {updated_measure[:50]}...")

    # Delete
    delete_sql = "DELETE FROM measure WHERE measure_id = ?"
    db.execute_query(delete_sql, (test_id,))
    result = db.execute_query(verify_sql, (test_id,))
    deleted_measure = result.fetchone()
    assert deleted_measure is None, "Deleted measure should not exist"
    print(f"[OK] Deleted and verified deletion of measure ID {test_id}")

except Exception as e:
    print(f"[FAIL] Write operations test failed: {e}")
    raise

#%%
# Test 9: Views
print("\n[Test 9] Testing database views...")
view_tests = [
    ("source_table_recreated_vw", 6500, 7000),
    ("apmg_slim_vw", 6000, 7000),
]

for view_name, min_count, max_count in view_tests:
    try:
        result = db.execute_query(f"SELECT COUNT(*) as count FROM {view_name}")
        count = result.fetchone()[0]
        assert min_count <= count <= max_count, f"{view_name} count {count} outside expected range"
        print(f"[OK] {view_name}: {count} rows")
    except Exception as e:
        print(f"[FAIL] {view_name} test failed: {e}")
        raise

#%%
# Test 10: Database File Exists
print("\n[Test 10] Verifying local database file...")
db_path = Path(__file__).parent / "data" / "lnrs_3nf_o1.duckdb"
assert db_path.exists(), f"Database file should exist at {db_path}"
size_mb = db_path.stat().st_size / (1024 * 1024)
print(f"[OK] Database file exists: {db_path.name} ({size_mb:.2f} MB)")

#%%
# Summary
print("\n" + "=" * 60)
print("PHASE 5.1 LOCAL MODE TESTING: ALL TESTS PASSED")
print("=" * 60)
print("\n[SUMMARY]")
print(f"[OK] Database Mode: {mode}")
print(f"[OK] Connection: Working")
print(f"[OK] Read Operations: Working")
print(f"[OK] Write Operations (Create/Update/Delete): Working")
print(f"[OK] Macros: Working")
print(f"[OK] Views: Working")
print(f"[OK] Database File: {size_mb:.2f} MB")
print("\nAll Phase 5.1 tests passed successfully!")
print("Ready to proceed to Phase 5.2 (MotherDuck mode testing)")
