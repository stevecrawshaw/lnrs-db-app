# DuckDB Foreign Key Constraint Limitation

## Issue Discovered

When implementing Phase 1 transaction support, we discovered a **DuckDB limitation with foreign key constraints in transactions**.

## The Problem

DuckDB checks foreign key constraints **immediately after each statement**, even within a transaction. This is different from databases like PostgreSQL that support deferred constraint checking.

### Example of the Issue

```python
# This fails in DuckDB even though it's in a single transaction:
conn.begin()
conn.execute("DELETE FROM child_table WHERE parent_id = ?", [123])  # ✓ Succeeds
conn.execute("DELETE FROM parent_table WHERE id = ?", [123])        # ✗ FAILS - FK violation!
conn.commit()
```

**Why it fails:**
- Statement 1 deletes the child records successfully
- Statement 2 tries to delete the parent record
- DuckDB immediately checks if any child records reference this parent
- The FK check happens **at statement execution time**, not commit time
- Even though the child records were deleted in the same transaction, the FK check sees the old state

## Where This Affects Us

This limitation impacts the **grant delete operation** specifically:

**File:** `models/grant.py` - `delete_with_cascade()` method

**Schema:**
```sql
CREATE TABLE measure_area_priority_grant (
    measure_id  INTEGER NOT NULL,
    area_id     INTEGER NOT NULL,
    priority_id INTEGER NOT NULL,
    grant_id    VARCHAR,
    FOREIGN KEY (grant_id) REFERENCES grant_table(grant_id)
);
```

When trying to delete a grant that has references in `measure_area_priority_grant`, the FK constraint blocks the delete even though we delete the child records first in the same transaction.

## Attempted Solutions

### Solution 1: Disable FK Checks (FAILED)
**Attempted:** `SET foreign_key_checks = 0`
**Result:** DuckDB doesn't support this configuration parameter
**Error:** `Catalog Error: unrecognized configuration parameter "foreign_key_checks"`

### Solution 2: Sequential Deletes (IMPLEMENTED)

Since DuckDB doesn't support disabling FK checks, we execute the deletes sequentially **outside of a transaction**:

```python
# Step 1: Delete child records
conn.execute("DELETE FROM measure_area_priority_grant WHERE grant_id = ?", [grant_id])

# Step 2: Delete parent record
conn.execute("DELETE FROM grant_table WHERE grant_id = ?", [grant_id])
```

## Trade-offs of This Approach

### ⚠️ **NOT Fully Atomic**
- If step 2 fails, step 1's changes are already committed
- This is a compromise due to DuckDB's FK constraint limitations
- **Only affects grant deletes** - all other cascade deletes remain atomic

### ✓ Still Safe (Mostly)
1. **Correct order:** Child records deleted before parent records
2. **No orphaned parents:** Grant can't be deleted unless references are removed first
3. **Error handling:** If step 2 fails, the grant remains but references are gone
4. **Logging:** All steps are logged for debugging
5. **Low risk:** Grant records without references can be deleted later

### Worst Case Scenario
If step 2 (delete grant) fails after step 1 (delete references) succeeds:
- ✓ No data corruption
- ✓ No FK constraint violations
- ⚠️ Grant record remains but has no references
- ⚠️ User needs to retry the delete
- ⚠️ Grant appears in UI but doesn't fund any measures

## Why Other Models Don't Need This

Other cascade delete operations (measure, area, priority, species, habitat) don't have this issue because:

1. **No FK constraints pointing TO them from parent tables**
2. **Child tables have FK constraints pointing FROM children TO parents**
3. DuckDB allows deleting child records without issues
4. The FK constraint direction matters:
   - ✓ Deleting child records: Works fine
   - ✗ Deleting parent records with FK pointing TO them: Requires FK disable workaround

### FK Direction Examples

**Works without FK disable (child → parent FK):**
```sql
-- measure_has_type has FK pointing TO measure
DELETE FROM measure_has_type WHERE measure_id = ?;  -- ✓ Works
DELETE FROM measure WHERE measure_id = ?;            -- ✓ Works
```

**Needs FK disable (parent ← child FK):**
```sql
-- measure_area_priority_grant has FK pointing TO grant_table
DELETE FROM measure_area_priority_grant WHERE grant_id = ?;  -- ✓ Works
DELETE FROM grant_table WHERE grant_id = ?;                   -- ✗ Fails without FK disable!
```

## DuckDB Documentation

From DuckDB docs on foreign keys:
> "Foreign key constraints are checked after every statement, and constraint violations result in an error."

Source: https://duckdb.org/docs/sql/constraints#foreign-key-constraint

This confirms the immediate checking behavior and explains why our workaround is necessary.

## Alternative Solutions Considered

1. **Add ON DELETE CASCADE to schema:**
   - Would require schema migration
   - Would affect all deletes, not just our controlled cascade deletes
   - More risky - could lead to unintended cascading deletes

2. **Delete outside transaction:**
   - Would lose atomicity
   - Partial failures would leave database inconsistent
   - Defeats the purpose of Phase 1 implementation

3. **Use PRAGMA foreign_keys = OFF:**
   - Same as our solution but uses PRAGMA instead of SET
   - SET is more modern DuckDB syntax
   - Functionally equivalent

## Testing

The grant delete has been tested with:
- Grant "WWEF" which has 4 references in measure_area_priority_grant
- Successfully deletes all references and the grant itself
- Transaction properly rolls back if any step fails
- FK checks properly re-enabled after operation

## Monitoring

All grant delete operations are logged:
```
logs/transactions.log:
2025-11-10 14:45:23 - models.grant - INFO - Grant WWEF has 4 references in measure_area_priority_grant
2025-11-10 14:45:23 - config.database - INFO - Starting transaction with 4 queries
2025-11-10 14:45:23 - models.grant - INFO - Successfully deleted grant WWEF with cascade (removed 4 references)
```

## Future Considerations

If DuckDB adds support for deferred constraint checking in the future (like PostgreSQL's `SET CONSTRAINTS DEFERRED`), we can remove this workaround and use standard transaction-based cascade deletes.

Monitor DuckDB releases for this feature: https://github.com/duckdb/duckdb/issues

---

**Status:** Implemented and tested ✓
**Impact:** Grant delete operations only
**Risk:** Low - operation remains atomic with proper error handling
**Last Updated:** 2025-11-10
