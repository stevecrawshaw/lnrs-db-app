# Troubleshooting Guide

This guide covers common issues and solutions for the LNRS Database Application's transaction and backup system.

## Table of Contents

1. [Backup & Restore Issues](#backup--restore-issues)
2. [Transaction Failures](#transaction-failures)
3. [Performance Issues](#performance-issues)
4. [Database Integrity](#database-integrity)
5. [Logging & Debugging](#logging--debugging)

---

## Backup & Restore Issues

### Backup Functionality Disabled

**Symptom**: Warning message "Backup functionality disabled" on Backup & Restore page.

**Cause**: Running on Streamlit Cloud or other ephemeral filesystem environment.

**Solution**: Backup functionality is intentionally disabled on cloud platforms because:
- Streamlit Cloud uses ephemeral filesystems
- Backups would be lost on container restart
- MotherDuck provides cloud infrastructure reliability

**Local Development**: Ensure you're running locally for backup functionality:
```bash
# Check if running locally
python -c "from config.backup import BackupManager; print(f'Backups enabled: {BackupManager().enabled}')"
```

### Snapshot Creation Fails

**Symptom**: Error during snapshot creation.

**Common Causes**:
1. **Insufficient disk space**
   ```bash
   # Check available space
   df -h data/backups/

   # Solution: Clean up old snapshots
   python -c "from config.backup import BackupManager; BackupManager().cleanup_old_snapshots(keep_count=5)"
   ```

2. **Database file locked**
   ```
   Error: database is locked
   ```
   **Solution**: Close all other connections to the database
   ```python
   from config.database import DatabaseConnection
   db = DatabaseConnection()
   db.close()  # Close all connections
   ```

3. **Permission issues**
   ```bash
   # Fix permissions
   chmod 755 data/backups/
   chmod 644 data/backups/*.duckdb
   ```

### Restore Operation Fails

**Symptom**: Restore fails with error or database becomes corrupted.

**Recovery Steps**:
1. **Check for safety backup**: Restore creates a safety backup before replacing database
   ```python
   from config.backup import BackupManager
   snapshots = BackupManager().list_snapshots(operation_type="pre_restore")
   print(f"Safety backups: {[s['snapshot_id'] for s in snapshots]}")
   ```

2. **Restore from safety backup** if needed:
   - Navigate to Backup & Restore page
   - Filter by "pre_restore" operation type
   - Restore most recent safety backup

3. **Verify database integrity**:
   ```python
   from config.database import DatabaseConnection
   db = DatabaseConnection()
   conn = db.get_connection()

   # Check measure count
   result = conn.execute("SELECT COUNT(*) FROM measure").fetchone()
   print(f"Measures: {result[0]}")
   ```

### Snapshot File Missing

**Symptom**: Error "Snapshot file not found" during restore.

**Cause**: Snapshot file was manually deleted or moved.

**Solution**:
1. Check snapshot metadata vs actual files:
   ```bash
   # List metadata
   cat data/backups/snapshot_metadata.json | grep snapshot_id

   # List actual files
   ls -lh data/backups/*.duckdb
   ```

2. Remove orphaned metadata entries or restore from another snapshot

---

## Transaction Failures

### Delete Operation Fails

**Symptom**: Error during delete operation, partial data deleted.

**Common Causes**:

1. **Foreign key constraint violation**
   ```
   Constraint Error: Violates foreign key constraint
   ```
   **Solution**: Delete operations should use `delete_with_cascade()` methods, which handle proper cascade order.

2. **Record doesn't exist**
   ```python
   # Verify record exists before delete
   from config.database import DatabaseConnection
   db = DatabaseConnection()
   result = db.get_connection().execute(
       "SELECT COUNT(*) FROM measure WHERE measure_id = ?",
       [measure_id]
   ).fetchone()

   if result[0] == 0:
       print(f"Measure {measure_id} not found")
   ```

3. **Snapshot creation failed**
   - Check logs: `logs/backups.log`
   - Verify disk space
   - If snapshot fails, delete operation is aborted (expected behavior)

### Update Operation Fails

**Symptom**: Update operation fails or partial update occurs.

**Cause**: Updates are atomic, so either all changes apply or none.

**Solution**:
1. Check validation errors in logs: `logs/transactions.log`
2. Verify required fields are provided
3. Check foreign key references exist

**Example**: Updating measure with invalid measure_type_id:
```python
# Check valid measure types
db = DatabaseConnection()
types = db.get_connection().execute("SELECT measure_type_id, measure_type FROM measure_type").fetchall()
print(f"Valid types: {types}")
```

### Cascading Delete Incomplete

**Symptom**: Parent record deleted but child records remain.

**Cause**: DuckDB's `ON DELETE CASCADE` is not reliable; manual cascade is required.

**Solution**: Use model's `delete_with_cascade()` method:
```python
from models.measure import MeasureModel
measure_model = MeasureModel()
result = measure_model.delete_with_cascade(measure_id)
```

**Check for orphaned records**:
```sql
-- Find measures with no types (orphaned)
SELECT m.measure_id, m.measure
FROM measure m
LEFT JOIN measure_has_type mht ON m.measure_id = mht.measure_id
WHERE mht.measure_id IS NULL;
```

---

## Performance Issues

### Slow Delete Operations

**Symptom**: Delete operations take >5 seconds.

**Cause**: Sequential cascade deletes across many relationships.

**Diagnosis**:
1. Check performance log: `logs/performance.log`
   ```bash
   grep "Slow operation" logs/performance.log
   ```

2. Identify bottleneck:
   ```bash
   grep "measure_delete_cascade" logs/performance.log | tail -5
   ```

**Solutions**:
1. **Expected behavior**: Deletes are sequential due to DuckDB FK constraints
2. **Reduce relationships**: If measure has many relationships, delete is slower
3. **Check disk I/O**: Snapshots involve file copies

### Slow Restore Operations

**Symptom**: Restore takes longer than expected.

**Cause**: Large database file (multiple MB or GB).

**Solutions**:
1. **Monitor progress**: Check logs in real-time
   ```bash
   tail -f logs/backups.log
   ```

2. **Database size**:
   ```bash
   ls -lh data/lnrs_3nf_o1.duckdb
   ls -lh data/backups/*.duckdb
   ```

3. **Expected timing**: ~1-2 seconds per MB for file copy + database verification

---

## Database Integrity

### Database Corruption

**Symptom**: Errors accessing database or inconsistent data.

**Recovery**:
1. **Immediate**: Restore from most recent snapshot
   - Navigate to Backup & Restore page
   - Sort by timestamp (newest first)
   - Preview and restore

2. **Verify integrity** after restore:
   ```python
   from config.backup import BackupManager
   backup_mgr = BackupManager()
   backup_mgr._verify_database_integrity()  # Runs COUNT query on measure table
   ```

3. **Check logs** for error cause: `logs/transactions.log`

### Foreign Key Violations

**Symptom**: Error about foreign key constraints.

**Diagnosis**:
```sql
-- Check for orphaned records in bridge tables
SELECT COUNT(*) FROM measure_has_type mht
WHERE NOT EXISTS (SELECT 1 FROM measure m WHERE m.measure_id = mht.measure_id);

SELECT COUNT(*) FROM measure_has_type mht
WHERE NOT EXISTS (SELECT 1 FROM measure_type mt WHERE mt.measure_type_id = mht.measure_type_id);
```

**Solution**: Restore to last known good snapshot or manually clean up orphaned records.

### Inconsistent Record Counts

**Symptom**: Record counts don't match expectations after operations.

**Diagnosis**:
```sql
-- Get counts of all core tables
SELECT 'measure' as table_name, COUNT(*) as count FROM measure
UNION ALL SELECT 'area', COUNT(*) FROM area
UNION ALL SELECT 'priority', COUNT(*) FROM priority
UNION ALL SELECT 'species', COUNT(*) FROM species
UNION ALL SELECT 'habitat', COUNT(*) FROM habitat
UNION ALL SELECT 'grant_table', COUNT(*) FROM grant_table;
```

**Solution**: Compare with snapshot to identify when divergence occurred, then restore.

---

## Logging & Debugging

### Enable Debug Logging

**Temporary (session-based)**:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

**Permanent**: Modify `config/logging_config.py`:
```python
setup_logging(log_level="DEBUG")  # Default is "INFO"
```

### Log File Locations

- **Transactions**: `logs/transactions.log` - All database operations
- **Backups**: `logs/backups.log` - Snapshot creation/restore
- **Performance**: `logs/performance.log` - Operation timing
- **Console**: STDOUT - Warnings and errors only

### Viewing Logs

**Real-time monitoring**:
```bash
# All database operations
tail -f logs/transactions.log

# Backup operations only
tail -f logs/backups.log

# Performance metrics
tail -f logs/performance.log
```

**Search logs**:
```bash
# Find all delete operations
grep "delete_with_cascade" logs/transactions.log

# Find slow operations
grep "Slow operation" logs/performance.log

# Find errors
grep "ERROR" logs/transactions.log
```

### Common Log Patterns

**Successful delete**:
```
INFO - Starting measure_delete_cascade (measure_id=123)
INFO - Creating snapshot: Pre-delete measure 123
INFO - Performance: snapshot_create completed in 0.234s
INFO - Deleted from measure_has_type: 3 rows
INFO - Deleted from measure_has_stakeholder: 2 rows
...
INFO - Successfully deleted measure 123
INFO - Performance: measure_delete_cascade completed in 1.456s
```

**Failed operation**:
```
ERROR - Failed to create snapshot: [Errno 28] No space left on device
ERROR - Snapshot creation failed, aborting delete operation
```

### Debug Mode for Tests

```bash
# Run tests with verbose output
uv run pytest tests/ -v -s

# Run specific test with full logging
uv run pytest tests/test_transactions.py::test_measure_delete_with_cascade -v -s --log-cli-level=DEBUG
```

---

## Common Questions

### Q: Can I restore while the app is running?

**A**: Yes, but it will close all database connections. The app will automatically reconnect. Users may see temporary errors. Best to restore when no users are active.

### Q: How much disk space do backups use?

**A**: Each snapshot is a full copy of the database (~5-50 MB typically). With 10 snapshots retained, expect ~50-500 MB. Adjust retention with:
```python
BackupManager().cleanup_old_snapshots(keep_count=5)  # Keep only 5
```

### Q: Can I manually delete snapshot files?

**A**: Yes, but update metadata:
1. Delete `.duckdb` files from `data/backups/`
2. Remove corresponding entries from `data/backups/snapshot_metadata.json`
3. Or use: `BackupManager().cleanup_old_snapshots()`

### Q: What happens if snapshot creation fails during delete?

**A**: The delete operation is aborted. No data is deleted. This is intentional safety behavior.

### Q: Why are deletes sequential instead of atomic?

**A**: DuckDB enforces foreign key constraints immediately during transactions. Child records must be deleted before parent records, making true atomic deletes impossible. Updates remain atomic.

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs**: Start with `logs/transactions.log`
2. **Run tests**: `uv run pytest tests/ -v` to verify system health
3. **Review documentation**: See `CLAUDE.md` for architecture details
4. **Last resort**: Restore from snapshot and retry operation

**Emergency recovery**: Keep the most recent snapshot always. It's your safety net.
