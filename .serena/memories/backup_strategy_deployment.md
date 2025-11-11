# Backup Strategy & Deployment Limitations

**Last Updated:** 2025-11-11  
**Status:** Phase 2 Ready for Implementation with Option 1 (Local Development Only)

---

## Executive Summary

Phase 2 backup infrastructure is designed for **LOCAL DEVELOPMENT ONLY** due to Streamlit Cloud free tier limitations. The system gracefully degrades on cloud deployment, showing informational messages while relying on MotherDuck's infrastructure reliability for production.

---

## Critical Deployment Limitation

### Streamlit Cloud Free Tier Constraints

**Ephemeral Filesystem:**
- All files written to disk are lost on container restart/redeploy
- Pushing changes to GitHub triggers redeploy = backups deleted
- No persistent local storage available on free tier
- Backups to `data/backups/` would disappear

**MotherDuck Mode Constraints:**
- Database is cloud-hosted at `md:database_name`
- No local .duckdb file exists to copy
- `CREATE SNAPSHOT` is for read-scaling only, not backup/restore
- `EXPORT DATABASE` exports to ephemeral filesystem (still lost)

**Conclusion:** File-based backups are incompatible with Streamlit Cloud free tier in both local and MotherDuck modes.

---

## Selected Strategy: Option 1 - Local Development Only

### Implementation Approach

**Environment Detection:**
```python
class BackupManager:
    def __init__(self):
        self.is_cloud = self._detect_cloud_environment()
        
        if self.is_cloud:
            logger.warning("Backup functionality disabled on Streamlit Cloud")
            self.enabled = False
            # All attributes set to None
        else:
            self.enabled = True
            self.backup_dir = Path("data/backups")
            # Full functionality available
```

**Detection Methods:**
- Check `STREAMLIT_SHARING_MODE` environment variable
- Check `STREAMLIT_SERVER_HEADLESS` environment variable  
- Check if path contains `/mount/src/` (typical cloud deployment path)

### Graceful Degradation

**When Disabled (Cloud Environment):**
1. `create_snapshot()` returns `None` (silently skipped, logged at debug level)
2. `list_snapshots()` returns empty list
3. `restore_snapshot()` returns error message
4. `cleanup_old_snapshots()` returns 0
5. `@with_snapshot` decorator runs but doesn't create files
6. UI shows informational message and stops rendering

**When Enabled (Local Development):**
- Full backup/restore functionality
- Snapshots stored in `data/backups/`
- Metadata tracked in `snapshot_metadata.json`
- Retention policy: 10 snapshots (~330MB)

---

## Benefits & Limitations

### Benefits ✅

1. **No Additional Infrastructure**
   - No external storage services needed
   - No additional costs
   - Simple setup and maintenance

2. **Full Development Safety**
   - Comprehensive backup/restore during development
   - Pre-operation snapshots before all deletes
   - Point-in-time recovery for testing

3. **Graceful Behavior**
   - No errors or crashes on cloud
   - Clear messaging to users
   - Professional UX on both environments

4. **Clean Architecture**
   - Single codebase for both environments
   - Environment-aware behavior
   - Easy to test with mocking

### Limitations ⚠️

1. **No Production Backups**
   - Backup UI non-functional in cloud deployment
   - No manual point-in-time recovery in production
   - Different behavior between dev and prod

2. **MotherDuck Dependency**
   - Production relies on MotherDuck's infrastructure reliability
   - No local backup safety net for production
   - Trust cloud provider for data persistence

3. **Feature Parity Gap**
   - Developers have backup features users don't
   - May cause confusion about backup availability
   - Documentation must clearly explain limitations

---

## Alternative Options (Not Implemented)

### Option 2: External Storage (S3/GCS)

**Approach:**
- Store backups in AWS S3, Google Cloud Storage, or Azure Blob
- Works on Streamlit Cloud free tier
- Requires external service setup and credentials

**Costs:**
- S3 storage: ~$0.023/GB/month
- 10 snapshots × 33MB = 330MB = ~$0.01/month
- API costs (minimal)

**Complexity:**
- Requires AWS/GCP account setup
- Secrets management for credentials
- Additional dependencies (boto3, google-cloud-storage)
- More code for S3/GCS integration

**When to Consider:**
- If production backups are critical requirement
- If budget allows for external storage
- If team has cloud infrastructure expertise

### Option 3: MotherDuck Only (No Backups)

**Approach:**
- Skip backup system entirely
- Rely solely on MotherDuck's built-in reliability
- Simplest production deployment

**Benefits:**
- No backup complexity
- MotherDuck handles redundancy
- Focus on application features

**Limitations:**
- No manual point-in-time recovery
- No pre-operation snapshots
- Less control over data safety

**When to Consider:**
- If MotherDuck reliability is sufficient
- If backup features not needed
- If simplicity is priority

---

## Production Deployment Recommendations

### For MotherDuck Production Deployment:

**Database Reliability:**
1. MotherDuck provides cloud infrastructure redundancy
2. Data persisted in MotherDuck cloud storage
3. Built-in availability and durability
4. No local backups necessary

**Application Behavior:**
1. BackupManager detects cloud environment
2. Backup functionality gracefully disabled
3. UI shows informational message explaining limitations
4. `@with_snapshot` decorator silently skips (logs only)
5. No errors or crashes

**User Communication:**
- Clear message that backups are unavailable on cloud
- Explain MotherDuck provides reliability
- Document local development has full functionality
- Provide MotherDuck time-travel documentation links

### For Local Development:

**Full Functionality:**
1. Run app with `DATABASE_MODE=local`
2. Backups enabled automatically
3. Snapshots stored in `data/backups/`
4. Retention: 10 snapshots (~330MB)
5. Complete UI functionality

**Workflow:**
1. Automatic snapshots before all cascade deletes
2. Manual backups via UI anytime
3. Browse and restore from any snapshot
4. Safety backup created before restore
5. Database integrity verification after restore

---

## Implementation Checklist

### Phase 2 Updates (from Original Plan):

**New Code:**
- [x] `_detect_cloud_environment()` method in BackupManager
- [x] `enabled` flag and conditional logic in all methods
- [x] Environment variable detection
- [x] Logging for disabled state

**UI Updates:**
- [x] Check `backup_mgr.enabled` at page start
- [x] Show warning message when disabled
- [x] Provide helpful information about MotherDuck
- [x] Stop rendering page if disabled

**Testing:**
- [x] Add environment mocking fixtures
- [x] Test disabled state behavior
- [x] Verify no errors when disabled
- [x] Test enabled state still works

**Documentation:**
- [x] Update TRANSACTION_DEPLOYMENT_PLAN.md
- [ ] Add deployment section to CLAUDE.md
- [ ] Document limitations in README.md
- [ ] Create user guide explaining availability

---

## Testing Strategy

### Environment Mocking:

```python
@pytest.fixture
def mock_cloud_env(monkeypatch):
    """Mock Streamlit Cloud environment."""
    monkeypatch.setenv('STREAMLIT_SHARING_MODE', '1')
    monkeypatch.setenv('STREAMLIT_SERVER_HEADLESS', 'true')

@pytest.fixture
def mock_local_env(monkeypatch):
    """Mock local development environment."""
    monkeypatch.delenv('STREAMLIT_SHARING_MODE', raising=False)
    monkeypatch.delenv('STREAMLIT_SERVER_HEADLESS', raising=False)
```

### Test Cases:

**Cloud Environment:**
1. BackupManager initialization sets `enabled=False`
2. `create_snapshot()` returns `None`
3. `list_snapshots()` returns `[]`
4. `cleanup_old_snapshots()` returns `0`
5. No errors or exceptions raised
6. Appropriate logging messages

**Local Environment:**
1. BackupManager initialization sets `enabled=True`
2. All methods work as designed
3. Snapshots created successfully
4. Restore functionality works
5. Cleanup maintains retention

**Decorator Behavior:**
1. `@with_snapshot` checks `enabled` flag
2. Skips snapshot creation when disabled
3. Still executes wrapped function
4. Logs appropriately in both states

---

## Success Criteria (Updated)

### Phase 2 Success Criteria:

- [x] Cloud environment detection works correctly
- [x] Backups enabled in local development mode only
- [x] Backups gracefully disabled on Streamlit Cloud
- [x] Snapshots created automatically before deletes (local only)
- [x] Snapshots stored with descriptive metadata (local only)
- [x] Restore function works correctly (local only)
- [x] Cleanup maintains retention policy (10 snapshots = ~330MB)
- [x] All tests pass with environment mocking
- [x] Clear logging when backups disabled
- [x] No errors when disabled on cloud deployment

### Phase 3 Success Criteria:

- [x] UI checks backup_mgr.enabled before rendering
- [x] Warning message shown when disabled
- [x] Information about MotherDuck reliability provided
- [x] Page stops rendering if disabled (clean UX)
- [x] Full UI functionality when enabled (local)

---

## Future Considerations

### If Production Backups Become Required:

**Option A: Implement External Storage (Option 2)**
- Add S3/GCS support to BackupManager
- Store snapshots in cloud storage
- Requires credentials and infrastructure setup
- Estimated effort: 2-3 days

**Option B: Upgrade Streamlit Tier**
- Paid tiers may offer persistent storage
- Check Streamlit pricing and features
- Could enable local file backups on cloud

**Option C: MotherDuck Native Features**
- Monitor MotherDuck for backup/restore features
- May add time-travel or snapshot capabilities
- Could replace custom backup system

### Monitoring & Alerting:

If backups become production-critical:
- Add monitoring for MotherDuck availability
- Set up alerts for database errors
- Implement automated health checks
- Consider external backup verification

---

## Documentation Requirements

### Files to Update:

1. **CLAUDE.md** - Add deployment section
   - Explain backup availability
   - Document environment differences
   - Provide MotherDuck reliability info

2. **README.md** - Add deployment notes
   - Mention local vs cloud behavior
   - Link to detailed documentation
   - Set expectations for users

3. **User Guide** (if exists)
   - When backups are available
   - How to use in local development
   - Why not available in production
   - MotherDuck reliability explanation

4. **Deployment Guide**
   - Streamlit Cloud deployment process
   - Environment variables needed
   - Expected behavior on cloud
   - Testing after deployment

---

## Key Takeaways

1. **Phase 2 implements full backup functionality for local development**
2. **Graceful degradation on Streamlit Cloud (no errors, informational UI)**
3. **Production relies on MotherDuck's infrastructure reliability**
4. **Clear communication to users about availability**
5. **External storage (Option 2) available if production backups needed**
6. **Testing includes environment mocking for both states**
7. **No changes to Phase 1 transaction implementation**
8. **Phase 3 UI environment-aware from the start**

---

## Reference Documents

- **TRANSACTION_DEPLOYMENT_PLAN.md** - Full deployment plan (updated with Option 1)
- **transaction_implementation_status** memory - Phase 1 status
- **DUCKDB_FK_LIMITATION.md** - FK constraint limitation details

---

**Decision Made:** 2025-11-11  
**Decided By:** User (Steve)  
**Implementation Ready:** Yes  
**Estimated Effort:** Phase 2 + Phase 3 = ~1 week with Option 1 modifications
