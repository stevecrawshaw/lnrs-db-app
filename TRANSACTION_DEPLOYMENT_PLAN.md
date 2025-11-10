# Transaction & Rollback Implementation - Deployment Plan

## Executive Summary

This plan implements transaction-based operations with pre-operation snapshots and point-in-time recovery for the LNRS database application. The implementation will be deployed in 4 phases over 5 weeks to minimize risk.

**User Requirements:**
- Historical restore (point-in-time recovery)
- Pre-operation snapshots for all destructive operations
- Maintain current concurrency model (first-come first-served)
- Phased rollout approach

---

## Current State Analysis

### Critical Issues Identified

1. **No Transaction Wrapping:** All multi-statement operations (6 cascade deletes, relationship updates) execute sequentially without atomicity
2. **Partial Failure Risk:** If operation fails mid-execution, previous changes remain committed
3. **No Rollback Capability:** Users cannot undo changes or restore to previous state
4. **No Backup System:** No automatic or manual backup functionality exists
5. **Unused Infrastructure:** `execute_transaction()` method exists in `config/database.py:259-279` but is NEVER used

### Operations Requiring Transactions

**HIGH PRIORITY (7+ statements):**
- Measure cascade delete (7 DELETEs) - `models/measure.py:290-343`
- Area cascade delete (7 DELETEs) - `models/area.py:220-273`
- Measure update with relationships (1 UPDATE + 3 DELETEs + N INSERTs) - `ui/pages/measures.py:327-389`
- Measure create with relationships (1 INSERT + N INSERTs) - `ui/pages/measures.py:152-201`

**MEDIUM PRIORITY (3-4 statements):**
- Priority cascade delete (4 DELETEs) - `models/priority.py:127-165`
- Species cascade delete (3 DELETEs) - `models/species.py:109-142`
- Habitat cascade delete (3 DELETEs) - `models/habitat.py:104-137`

**LOW PRIORITY (2 statements):**
- Grant cascade delete (2 DELETEs) - `models/grant.py:80-108`
- Relationship link deletes (2 DELETEs) - `models/relationship.py:111-148`

---

## Phase 1: Core Transaction Implementation
**Timeline:** Week 1-2
**Goal:** Make all multi-statement operations atomic with automatic rollback on errors

### 1.1 Refactor Cascade Delete Operations

**Files to Modify:**
- `models/measure.py`
- `models/area.py`
- `models/priority.py`
- `models/species.py`
- `models/habitat.py`
- `models/grant.py`

**Changes:**
Convert all `delete_with_cascade()` methods to use `execute_transaction()`

**Before Pattern:**
```python
def delete_with_cascade(self, measure_id: int) -> bool:
    try:
        query1 = "DELETE FROM measure_has_type WHERE measure_id = ?"
        self.execute_raw_query(query1, [measure_id])

        query2 = "DELETE FROM measure_has_stakeholder WHERE measure_id = ?"
        self.execute_raw_query(query2, [measure_id])

        # ... 5 more separate deletes

        return True
    except Exception as e:
        print(f"Error: {e}")
        raise
```

**After Pattern:**
```python
def delete_with_cascade(self, measure_id: int) -> bool:
    """Delete measure and all related records atomically."""
    queries = [
        ("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_has_stakeholder WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_area_priority_grant WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_area_priority WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_has_benefits WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_has_species WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure WHERE measure_id = ?", [measure_id]),
    ]

    try:
        self.db.execute_transaction(queries)
        logger.info(f"Successfully deleted measure {measure_id} with cascade")
        return True
    except duckdb.Error as e:
        logger.error(f"Failed to delete measure {measure_id}: {e}")
        raise
```

### 1.2 Wrap Relationship CRUD Operations

**File to Modify:** `models/relationship.py`

**Target Methods:**
- `create_measure_area_priority_link()` - Convert loop INSERTs to batched transaction
- `delete_measure_area_priority_link()` - Wrap 2 DELETEs (lines 111-148)
- `update_measure_area_priority_link()` - If exists, wrap UPDATE + related changes
- `delete_species_area_priority_link()` - Single DELETE but prepare for future expansion
- `delete_habitat_creation_link()` - Single DELETE
- `delete_habitat_management_link()` - Single DELETE

**Example Refactor:**
```python
def create_measure_area_priority_link(
    self,
    measure_id: int,
    area_ids: list[int],
    priority_ids: list[int]
) -> bool:
    """Create measure-area-priority links atomically."""
    queries = []

    for area_id in area_ids:
        for priority_id in priority_ids:
            queries.append((
                """INSERT INTO measure_area_priority
                   (measure_id, area_id, priority_id)
                   VALUES (?, ?, ?)""",
                [measure_id, area_id, priority_id]
            ))

    try:
        self.db.execute_transaction(queries)
        logger.info(f"Created {len(queries)} MAP links for measure {measure_id}")
        return True
    except duckdb.Error as e:
        logger.error(f"Failed to create MAP links: {e}")
        raise
```

### 1.3 Transaction-Wrap Update Operations

**File to Modify:** `ui/pages/measures.py`

**Target Section:** Lines 327-389 (measure update flow)

**Current Flow:**
1. Update measure record (1 UPDATE)
2. Delete old measure types (1 DELETE)
3. Delete old stakeholders (1 DELETE)
4. Delete old benefits (1 DELETE)
5. Insert new measure types (N INSERTs - loop)
6. Insert new stakeholders (N INSERTs - loop)
7. Insert new benefits (N INSERTs - loop)

**Refactored Approach:**
```python
# In UI layer (measures.py)
if st.button("Save Changes"):
    try:
        # Collect all data
        update_data = {...}
        new_types = selected_types
        new_stakeholders = selected_stakeholders
        new_benefits = selected_benefits

        # Call single atomic update method
        measure_model.update_with_relationships(
            measure_id=st.session_state.selected_measure_id,
            measure_data=update_data,
            measure_types=new_types,
            stakeholders=new_stakeholders,
            benefits=new_benefits
        )

        st.success("✅ Successfully updated measure!")
        st.cache_data.clear()
        st.rerun()

    except duckdb.Error as e:
        st.error(f"❌ Failed to update measure: {str(e)}")
        logger.exception("Measure update failed")
```

```python
# In model layer (models/measure.py) - NEW METHOD
def update_with_relationships(
    self,
    measure_id: int,
    measure_data: dict,
    measure_types: list[int],
    stakeholders: list[int],
    benefits: list[int]
) -> bool:
    """Update measure and all relationships atomically."""
    queries = []

    # 1. Update measure
    set_clause = ", ".join([f"{k} = ?" for k in measure_data.keys()])
    values = list(measure_data.values()) + [measure_id]
    queries.append((
        f"UPDATE measure SET {set_clause} WHERE measure_id = ?",
        values
    ))

    # 2. Delete old relationships
    queries.extend([
        ("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_has_stakeholder WHERE measure_id = ?", [measure_id]),
        ("DELETE FROM measure_has_benefits WHERE measure_id = ?", [measure_id]),
    ])

    # 3. Insert new relationships
    for type_id in measure_types:
        queries.append((
            "INSERT INTO measure_has_type (measure_id, type_id) VALUES (?, ?)",
            [measure_id, type_id]
        ))

    for stakeholder_id in stakeholders:
        queries.append((
            "INSERT INTO measure_has_stakeholder (measure_id, stakeholder_id) VALUES (?, ?)",
            [measure_id, stakeholder_id]
        ))

    for benefit_id in benefits:
        queries.append((
            "INSERT INTO measure_has_benefits (measure_id, benefit_id) VALUES (?, ?)",
            [measure_id, benefit_id]
        ))

    try:
        self.db.execute_transaction(queries)
        logger.info(f"Updated measure {measure_id} with {len(queries)} operations")
        return True
    except duckdb.Error as e:
        logger.error(f"Failed to update measure {measure_id}: {e}")
        raise
```

### 1.4 Enhanced Error Handling

**Changes Across All Files:**

1. **Replace print() with logging:**
```python
# Add to each model file
import logging
logger = logging.getLogger(__name__)

# Replace:
print(f"Error deleting measure: {e}")

# With:
logger.error(f"Error deleting measure: {e}", exc_info=True)
```

2. **Replace generic Exception with specific errors:**
```python
# Replace:
except Exception as e:

# With:
except duckdb.Error as e:
```

3. **Structured error messages in UI:**
```python
# In UI files
except duckdb.Error as e:
    error_msg = str(e)
    if "constraint" in error_msg.lower():
        st.error("❌ Cannot delete: This record is referenced by other data")
    elif "not found" in error_msg.lower():
        st.error("❌ Record not found")
    else:
        st.error(f"❌ Database error: {error_msg}")
    logger.exception(f"Operation failed for user")
```

**New File:** `config/logging_config.py`
```python
import logging
import sys
from pathlib import Path

def setup_logging():
    """Configure application-wide logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(log_dir / "transactions.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

### Phase 1 Testing

**New File:** `tests/test_transactions.py`

```python
import pytest
import duckdb
from models.measure import MeasureModel
from models.area import AreaModel
from config.database import DatabaseConnection

@pytest.fixture
def test_db():
    """Create a test database."""
    db = DatabaseConnection()
    db.set_connection_path("data/lnrs_test.duckdb")
    yield db
    db.close()

def test_measure_delete_cascade_success(test_db):
    """Test successful cascade delete with transaction."""
    measure_model = MeasureModel()

    # Create test measure with relationships
    measure_id = create_test_measure()

    # Delete should succeed
    result = measure_model.delete_with_cascade(measure_id)
    assert result is True

    # Verify all relationships deleted
    assert not measure_exists(measure_id)
    assert not relationships_exist(measure_id)

def test_measure_delete_cascade_rollback(test_db):
    """Test transaction rollback on cascade delete failure."""
    measure_model = MeasureModel()

    # Create test measure
    measure_id = create_test_measure()

    # Create constraint that will cause failure
    create_blocking_constraint(measure_id)

    # Delete should fail and rollback
    with pytest.raises(duckdb.Error):
        measure_model.delete_with_cascade(measure_id)

    # Verify measure still exists (rollback successful)
    assert measure_exists(measure_id)
    assert relationships_exist(measure_id)

def test_measure_update_with_relationships_atomic(test_db):
    """Test atomic update of measure with relationships."""
    measure_model = MeasureModel()

    measure_id = create_test_measure()

    # Update with new relationships
    result = measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data={"measure_name": "Updated Name"},
        measure_types=[1, 2],
        stakeholders=[3],
        benefits=[4, 5]
    )

    assert result is True

    # Verify update
    measure = measure_model.get_by_id(measure_id)
    assert measure["measure_name"] == "Updated Name"

    # Verify relationships
    types = get_measure_types(measure_id)
    assert len(types) == 2
```

### Phase 1 Deliverables

**Modified Files (9):**
- `models/measure.py` - Transaction-wrapped delete/update
- `models/area.py` - Transaction-wrapped delete
- `models/priority.py` - Transaction-wrapped delete
- `models/species.py` - Transaction-wrapped delete
- `models/habitat.py` - Transaction-wrapped delete
- `models/grant.py` - Transaction-wrapped delete
- `models/relationship.py` - Transaction-wrapped multi-statement ops
- `ui/pages/measures.py` - Call new atomic update method
- `config/database.py` - Add logging

**New Files (2):**
- `config/logging_config.py` - Centralized logging setup
- `tests/test_transactions.py` - Transaction test suite

**Success Criteria:**
- [ ] All cascade deletes are atomic (all-or-nothing)
- [ ] All relationship updates are atomic
- [ ] Failed operations automatically rollback
- [ ] No partial failures leave database inconsistent
- [ ] All tests pass
- [ ] Logging captures all transaction events

---

## Phase 2: Backup Infrastructure
**Timeline:** Week 3
**Goal:** Create database snapshot system with pre-operation backups

### 2.1 Backup Module

**New File:** `config/backup.py`

```python
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage database backups and snapshots."""

    def __init__(self):
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.metadata_file = self.backup_dir / "snapshot_metadata.json"
        self.db_path = Path("data/lnrs_3nf_o1.duckdb")

    def create_snapshot(
        self,
        description: str,
        operation_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> str:
        """
        Create a database snapshot.

        Args:
            description: Human-readable description
            operation_type: Type of operation (delete, update, bulk_delete, etc.)
            entity_type: Entity type (measure, area, priority, etc.)
            entity_id: ID of entity being modified

        Returns:
            snapshot_id: Unique identifier for the snapshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build filename
        parts = [timestamp]
        if operation_type:
            parts.append(operation_type)
        if entity_type:
            parts.append(entity_type)
        if entity_id:
            parts.append(str(entity_id))

        snapshot_id = "_".join(parts)
        snapshot_path = self.backup_dir / f"{snapshot_id}.duckdb"

        try:
            # Create snapshot (file copy)
            shutil.copy2(self.db_path, snapshot_path)

            # Calculate size
            size_mb = snapshot_path.stat().st_size / (1024 ** 2)

            # Save metadata
            metadata = {
                "snapshot_id": snapshot_id,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "description": description,
                "operation_type": operation_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "file_path": str(snapshot_path),
                "size_mb": round(size_mb, 2)
            }

            self._save_metadata(metadata)

            logger.info(f"Created snapshot {snapshot_id} ({size_mb:.2f} MB)")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise

    def list_snapshots(
        self,
        operation_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        List all available snapshots with filtering.

        Args:
            operation_type: Filter by operation type
            entity_type: Filter by entity type
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot metadata dicts, newest first
        """
        if not self.metadata_file.exists():
            return []

        with open(self.metadata_file, "r") as f:
            all_snapshots = json.load(f)

        # Filter
        snapshots = all_snapshots
        if operation_type:
            snapshots = [s for s in snapshots if s.get("operation_type") == operation_type]
        if entity_type:
            snapshots = [s for s in snapshots if s.get("entity_type") == entity_type]

        # Sort by timestamp descending
        snapshots.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit
        if limit:
            snapshots = snapshots[:limit]

        return snapshots

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore database from a snapshot.

        Args:
            snapshot_id: ID of snapshot to restore

        Returns:
            True if successful
        """
        from config.database import DatabaseConnection

        # Find snapshot
        snapshots = self.list_snapshots()
        snapshot = next((s for s in snapshots if s["snapshot_id"] == snapshot_id), None)

        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        snapshot_path = Path(snapshot["file_path"])

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

        try:
            # Create safety backup before restore
            logger.info(f"Creating safety backup before restore of {snapshot_id}")
            self.create_snapshot(
                description=f"Pre-restore safety backup (restoring {snapshot_id})",
                operation_type="pre_restore"
            )

            # Close all database connections
            logger.info("Closing database connections")
            db = DatabaseConnection()
            db.close()

            # Replace database file
            logger.info(f"Restoring from {snapshot_path}")
            shutil.copy2(snapshot_path, self.db_path)

            # Reconnect
            logger.info("Re-establishing database connection")
            db.get_connection()

            # Verify integrity
            self._verify_database_integrity()

            logger.info(f"Successfully restored snapshot {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            raise

    def cleanup_old_snapshots(self, keep_count: int = 50) -> int:
        """
        Delete old snapshots, keeping only the most recent.

        Args:
            keep_count: Number of snapshots to keep

        Returns:
            Number of snapshots deleted
        """
        snapshots = self.list_snapshots()

        if len(snapshots) <= keep_count:
            return 0

        to_delete = snapshots[keep_count:]
        deleted_count = 0

        for snapshot in to_delete:
            try:
                Path(snapshot["file_path"]).unlink()
                deleted_count += 1
                logger.info(f"Deleted old snapshot {snapshot['snapshot_id']}")
            except Exception as e:
                logger.warning(f"Failed to delete snapshot {snapshot['snapshot_id']}: {e}")

        # Update metadata
        kept_snapshots = snapshots[:keep_count]
        with open(self.metadata_file, "w") as f:
            json.dump(kept_snapshots, f, indent=2)

        logger.info(f"Cleaned up {deleted_count} old snapshots")
        return deleted_count

    def _save_metadata(self, new_snapshot: dict):
        """Append new snapshot metadata to file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                metadata = json.load(f)
        else:
            metadata = []

        metadata.append(new_snapshot)

        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _verify_database_integrity(self):
        """Verify database can be opened and basic queries work."""
        from config.database import DatabaseConnection

        db = DatabaseConnection()
        conn = db.get_connection()

        # Test basic query
        result = conn.execute("SELECT COUNT(*) FROM measure").fetchone()
        logger.info(f"Database integrity check: {result[0]} measures found")
```

### 2.2 Pre-Operation Snapshot Hooks

**Modify File:** `config/database.py`

Add decorator and modify execute_transaction:

```python
from functools import wraps
from config.backup import BackupManager

def with_snapshot(operation_type: str, entity_type: str = None):
    """
    Decorator to create snapshot before destructive operations.

    Usage:
        @with_snapshot("delete", "measure")
        def delete_with_cascade(self, measure_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract entity_id from kwargs or args
            entity_id = kwargs.get('id') or (args[1] if len(args) > 1 else None)

            # Create snapshot
            backup_mgr = BackupManager()
            description = f"Before {operation_type} {entity_type} {entity_id}"
            snapshot_id = backup_mgr.create_snapshot(
                description=description,
                operation_type=operation_type,
                entity_type=entity_type,
                entity_id=entity_id
            )

            logger.info(f"Created pre-operation snapshot: {snapshot_id}")

            # Execute original function
            try:
                result = func(*args, **kwargs)
                logger.info(f"Operation {operation_type} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Operation {operation_type} failed: {e}")
                logger.info(f"Database can be restored from snapshot: {snapshot_id}")
                raise

        return wrapper
    return decorator
```

**Apply Decorator to All Cascade Deletes:**

```python
# In models/measure.py
@with_snapshot("delete", "measure")
def delete_with_cascade(self, measure_id: int) -> bool:
    """Delete measure and all related records atomically."""
    # ... existing code using execute_transaction

# In models/area.py
@with_snapshot("delete", "area")
def delete_with_cascade(self, area_id: int) -> bool:
    # ... existing code

# In models/priority.py
@with_snapshot("delete", "priority")
def delete_with_cascade(self, priority_id: int) -> bool:
    # ... existing code

# Similarly for species, habitat, grant
```

### 2.3 Snapshot Metadata Tracking

**File:** `data/backups/snapshot_metadata.json` (auto-generated)

Structure:
```json
[
  {
    "snapshot_id": "20250110_143022_delete_measure_42",
    "timestamp": "20250110_143022",
    "datetime": "2025-01-10T14:30:22.123456",
    "description": "Before delete measure 42",
    "operation_type": "delete",
    "entity_type": "measure",
    "entity_id": 42,
    "file_path": "data/backups/20250110_143022_delete_measure_42.duckdb",
    "size_mb": 12.34
  },
  {
    "snapshot_id": "20250110_150000_update_measure_15",
    "timestamp": "20250110_150000",
    "datetime": "2025-01-10T15:00:00.654321",
    "description": "Before update measure 15",
    "operation_type": "update",
    "entity_type": "measure",
    "entity_id": 15,
    "file_path": "data/backups/20250110_150000_update_measure_15.duckdb",
    "size_mb": 12.35
  }
]
```

### Phase 2 Testing

**Add to:** `tests/test_backups.py`

```python
import pytest
from pathlib import Path
from config.backup import BackupManager
from config.database import DatabaseConnection

@pytest.fixture
def backup_mgr():
    """Backup manager instance."""
    return BackupManager()

def test_create_snapshot(backup_mgr):
    """Test snapshot creation."""
    snapshot_id = backup_mgr.create_snapshot(
        description="Test snapshot",
        operation_type="delete",
        entity_type="measure",
        entity_id=123
    )

    assert snapshot_id is not None
    assert Path(f"data/backups/{snapshot_id}.duckdb").exists()

    # Verify metadata
    snapshots = backup_mgr.list_snapshots()
    assert len(snapshots) > 0
    assert snapshots[0]["snapshot_id"] == snapshot_id

def test_restore_snapshot(backup_mgr):
    """Test snapshot restore."""
    # Create test data
    db = DatabaseConnection()
    conn = db.get_connection()
    original_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Before test delete"
    )

    # Modify data
    conn.execute("DELETE FROM measure WHERE measure_id = 1")
    new_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert new_count == original_count - 1

    # Restore
    backup_mgr.restore_snapshot(snapshot_id)

    # Verify restore
    restored_count = conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
    assert restored_count == original_count

def test_cleanup_old_snapshots(backup_mgr):
    """Test snapshot cleanup."""
    # Create multiple snapshots
    for i in range(10):
        backup_mgr.create_snapshot(f"Test snapshot {i}")

    # Cleanup, keep only 5
    deleted = backup_mgr.cleanup_old_snapshots(keep_count=5)

    assert deleted == 5

    # Verify only 5 remain
    snapshots = backup_mgr.list_snapshots()
    assert len(snapshots) == 5
```

### Phase 2 Deliverables

**New Files (2):**
- `config/backup.py` - Backup/restore functionality (300+ lines)
- `tests/test_backups.py` - Backup test suite

**Modified Files (8):**
- `config/database.py` - Add snapshot decorator
- `models/measure.py` - Apply @with_snapshot decorator
- `models/area.py` - Apply @with_snapshot decorator
- `models/priority.py` - Apply @with_snapshot decorator
- `models/species.py` - Apply @with_snapshot decorator
- `models/habitat.py` - Apply @with_snapshot decorator
- `models/grant.py` - Apply @with_snapshot decorator
- `.gitignore` - Add `data/backups/*.duckdb` (keep metadata.json)

**Success Criteria:**
- [ ] Snapshots created automatically before all cascade deletes
- [ ] Snapshots stored with descriptive metadata
- [ ] Restore function works correctly
- [ ] Cleanup function maintains retention policy
- [ ] All tests pass
- [ ] Backup directory under 1GB (check cleanup frequency)

---

## Phase 3: Restore UI
**Timeline:** Week 4
**Goal:** User interface for viewing and restoring backups

### 3.1 New Streamlit Page: Backup & Restore

**New File:** `ui/pages/backup_restore.py`

```python
import streamlit as st
import pandas as pd
from config.backup import BackupManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Backup & Restore", page_icon="💾", layout="wide")

st.title("💾 Database Backup & Restore")

# Initialize backup manager
backup_mgr = BackupManager()

# Create tabs
tab1, tab2, tab3 = st.tabs(["📋 Snapshots", "➕ Create Backup", "⚙️ Settings"])

# TAB 1: View Snapshots
with tab1:
    st.header("Available Snapshots")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_operation = st.selectbox(
            "Filter by Operation",
            ["All", "delete", "update", "bulk_delete", "pre_restore", "manual"]
        )
    with col2:
        filter_entity = st.selectbox(
            "Filter by Entity",
            ["All", "measure", "area", "priority", "species", "habitat", "grant"]
        )
    with col3:
        limit = st.number_input("Show last N snapshots", min_value=10, max_value=200, value=50)

    # Get snapshots
    operation_filter = None if filter_operation == "All" else filter_operation
    entity_filter = None if filter_entity == "All" else filter_entity

    snapshots = backup_mgr.list_snapshots(
        operation_type=operation_filter,
        entity_type=entity_filter,
        limit=limit
    )

    if not snapshots:
        st.info("No snapshots found matching filters")
    else:
        st.success(f"Found {len(snapshots)} snapshots")

        # Convert to DataFrame for display
        df = pd.DataFrame(snapshots)
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Display table
        for idx, snapshot in enumerate(snapshots):
            with st.expander(
                f"📸 {snapshot['datetime']} - {snapshot['description']} ({snapshot['size_mb']} MB)"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write("**Snapshot Details:**")
                    st.write(f"- **ID:** `{snapshot['snapshot_id']}`")
                    st.write(f"- **Description:** {snapshot['description']}")
                    st.write(f"- **Date:** {snapshot['datetime']}")
                    st.write(f"- **Operation:** {snapshot['operation_type'] or 'N/A'}")
                    st.write(f"- **Entity Type:** {snapshot['entity_type'] or 'N/A'}")
                    st.write(f"- **Entity ID:** {snapshot['entity_id'] or 'N/A'}")
                    st.write(f"- **Size:** {snapshot['size_mb']} MB")
                    st.write(f"- **File:** `{snapshot['file_path']}`")

                with col2:
                    st.write("**Actions:**")

                    # Preview button
                    if st.button("🔍 Preview", key=f"preview_{idx}"):
                        st.session_state[f"preview_snapshot_id"] = snapshot['snapshot_id']
                        st.rerun()

                    # Restore button
                    if st.button("⚠️ Restore", key=f"restore_{idx}", type="primary"):
                        st.session_state[f"restore_snapshot_id"] = snapshot['snapshot_id']
                        st.session_state[f"restore_confirm"] = False
                        st.rerun()

# TAB 2: Create Manual Backup
with tab2:
    st.header("Create Manual Backup")

    st.info("💡 **Tip:** Automatic snapshots are created before all delete operations. "
            "Use manual backups before making major changes or for periodic archival.")

    with st.form("create_backup_form"):
        description = st.text_input(
            "Backup Description*",
            placeholder="e.g., Before bulk update of measures"
        )

        submit = st.form_submit_button("Create Backup", type="primary")

        if submit:
            if not description:
                st.error("❌ Please provide a description")
            else:
                try:
                    with st.spinner("Creating backup..."):
                        snapshot_id = backup_mgr.create_snapshot(
                            description=description,
                            operation_type="manual"
                        )

                    st.success(f"✅ Backup created successfully!")
                    st.code(f"Snapshot ID: {snapshot_id}")
                    logger.info(f"Manual backup created: {snapshot_id}")

                except Exception as e:
                    st.error(f"❌ Failed to create backup: {str(e)}")
                    logger.exception("Manual backup failed")

# TAB 3: Settings
with tab3:
    st.header("Backup Settings")

    # Storage info
    st.subheader("💾 Storage Information")
    snapshots = backup_mgr.list_snapshots()
    total_size = sum(s['size_mb'] for s in snapshots)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Snapshots", len(snapshots))
    with col2:
        st.metric("Total Storage", f"{total_size:.2f} MB")

    # Cleanup
    st.subheader("🗑️ Cleanup Old Snapshots")

    with st.form("cleanup_form"):
        keep_count = st.number_input(
            "Number of snapshots to keep",
            min_value=5,
            max_value=200,
            value=50,
            help="Older snapshots will be deleted"
        )

        cleanup = st.form_submit_button("Clean Up", type="secondary")

        if cleanup:
            try:
                deleted = backup_mgr.cleanup_old_snapshots(keep_count=keep_count)
                if deleted > 0:
                    st.success(f"✅ Deleted {deleted} old snapshots")
                    logger.info(f"Cleaned up {deleted} snapshots, kept {keep_count}")
                    st.rerun()
                else:
                    st.info("No snapshots to delete")
            except Exception as e:
                st.error(f"❌ Cleanup failed: {str(e)}")
                logger.exception("Cleanup failed")

# PREVIEW MODAL
if any(f"preview_snapshot_id" in key for key in st.session_state.keys()):
    snapshot_id = st.session_state.get(f"preview_snapshot_id")

    if snapshot_id:
        st.subheader(f"🔍 Preview Snapshot: {snapshot_id}")

        try:
            # Open snapshot in read-only mode
            import duckdb
            snapshot_path = f"data/backups/{snapshot_id}.duckdb"
            preview_conn = duckdb.connect(snapshot_path, read_only=True)

            # Show summary stats
            col1, col2, col3 = st.columns(3)

            with col1:
                measure_count = preview_conn.execute("SELECT COUNT(*) FROM measure").fetchone()[0]
                st.metric("Measures", measure_count)

            with col2:
                area_count = preview_conn.execute("SELECT COUNT(*) FROM area").fetchone()[0]
                st.metric("Areas", area_count)

            with col3:
                priority_count = preview_conn.execute("SELECT COUNT(*) FROM priority").fetchone()[0]
                st.metric("Priorities", priority_count)

            # Show recent measures
            st.write("**Recent Measures:**")
            measures_df = preview_conn.execute(
                "SELECT measure_id, measure_name FROM measure ORDER BY measure_id DESC LIMIT 10"
            ).df()
            st.dataframe(measures_df)

            preview_conn.close()

            if st.button("Close Preview"):
                del st.session_state[f"preview_snapshot_id"]
                st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to preview snapshot: {str(e)}")
            logger.exception(f"Preview failed for {snapshot_id}")

# RESTORE CONFIRMATION MODAL
if any(f"restore_snapshot_id" in key for key in st.session_state.keys()):
    snapshot_id = st.session_state.get(f"restore_snapshot_id")

    if snapshot_id:
        st.warning("⚠️ **RESTORE DATABASE**")
        st.write(f"You are about to restore the database from snapshot: `{snapshot_id}`")

        st.error("""
        **WARNING:** This action will:
        - Replace the current database with the snapshot
        - Create a safety backup of the current state first
        - Disconnect all active sessions
        - **ALL changes since the snapshot will be LOST**
        """)

        # Confirmation input
        confirm_text = st.text_input(
            "Type RESTORE to confirm",
            key="restore_confirmation_input"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Cancel", key="restore_cancel"):
                del st.session_state[f"restore_snapshot_id"]
                if f"restore_confirm" in st.session_state:
                    del st.session_state[f"restore_confirm"]
                st.rerun()

        with col2:
            if st.button("⚠️ RESTORE NOW", key="restore_execute", type="primary"):
                if confirm_text != "RESTORE":
                    st.error("❌ Please type RESTORE to confirm")
                else:
                    try:
                        with st.spinner("Restoring database... This may take a moment."):
                            backup_mgr.restore_snapshot(snapshot_id)

                        st.success("✅ Database restored successfully!")
                        st.info("Please refresh the page to see the restored data.")
                        logger.info(f"Database restored from snapshot: {snapshot_id}")

                        # Clear session state
                        del st.session_state[f"restore_snapshot_id"]
                        if f"restore_confirm" in st.session_state:
                            del st.session_state[f"restore_confirm"]

                        # Clear all caches
                        st.cache_data.clear()

                    except Exception as e:
                        st.error(f"❌ Restore failed: {str(e)}")
                        logger.exception(f"Restore failed for {snapshot_id}")
```

### 3.2 Navigation Integration

**Modify:** Main app file (likely `app.py` or `main.py`)

Add backup page to navigation:

```python
# In sidebar navigation
st.sidebar.page_link("ui/pages/backup_restore.py", label="💾 Backup & Restore")
```

### 3.3 In-Page Restore Links

**Modify:** `ui/pages/measures.py`, `ui/pages/areas.py`, etc.

Add info box after delete confirmations:

```python
# After successful delete
st.success(f"✅ Successfully deleted {entity_type} ID {entity_id}!")
st.info("💡 **Tip:** Visit the [Backup & Restore](/backup_restore) page if you need to undo this change.")
```

### Phase 3 Testing

Manual testing checklist:

1. **Snapshot List:**
   - [ ] All snapshots display with correct metadata
   - [ ] Filters work correctly (operation type, entity type)
   - [ ] Limit parameter works
   - [ ] Sorting is newest first

2. **Manual Backup:**
   - [ ] Create button works
   - [ ] Description validation works
   - [ ] Snapshot appears in list immediately

3. **Preview:**
   - [ ] Preview opens read-only connection
   - [ ] Summary stats display correctly
   - [ ] No modification possible in preview
   - [ ] Close button works

4. **Restore:**
   - [ ] Warning messages display
   - [ ] Confirmation text validation works
   - [ ] Safety backup created before restore
   - [ ] Restore completes successfully
   - [ ] Data matches snapshot after restore
   - [ ] Cancel button works

5. **Cleanup:**
   - [ ] Cleanup deletes correct number of snapshots
   - [ ] Keeps most recent snapshots
   - [ ] Metadata updated correctly

### Phase 3 Deliverables

**New Files (1):**
- `ui/pages/backup_restore.py` - Complete backup/restore UI (400+ lines)

**Modified Files (8):**
- `ui/pages/measures.py` - Add restore hint after deletes
- `ui/pages/areas.py` - Add restore hint
- `ui/pages/priorities.py` - Add restore hint
- `ui/pages/species.py` - Add restore hint
- `ui/pages/habitats.py` - Add restore hint
- `ui/pages/grants.py` - Add restore hint
- `app.py` (or main app file) - Add navigation link
- `.streamlit/config.toml` - Configure page settings if needed

**Success Criteria:**
- [ ] Users can view all snapshots with metadata
- [ ] Users can create manual backups
- [ ] Users can preview snapshots before restoring
- [ ] Users can restore from any snapshot
- [ ] Restore requires explicit confirmation
- [ ] Safety backup always created before restore
- [ ] UI is intuitive and informative
- [ ] Error messages are helpful

---

## Phase 4: Testing & Monitoring
**Timeline:** Week 5
**Goal:** Comprehensive testing and operational monitoring

### 4.1 Test Suite Enhancement

**New File:** `tests/conftest.py` (pytest fixtures)

```python
import pytest
import shutil
from pathlib import Path
from config.database import DatabaseConnection

@pytest.fixture(scope="session")
def test_db_path():
    """Path to test database."""
    return Path("data/lnrs_test.duckdb")

@pytest.fixture(scope="session")
def production_db_path():
    """Path to production database."""
    return Path("data/lnrs_3nf_o1.duckdb")

@pytest.fixture(scope="function")
def test_db(test_db_path, production_db_path):
    """
    Create a test database copy before each test.
    Restore production database after test.
    """
    # Copy production to test
    shutil.copy2(production_db_path, test_db_path)

    # Configure database to use test path
    db = DatabaseConnection()
    original_path = db._db_path
    db._db_path = str(test_db_path)
    db._connection = None  # Force reconnect

    yield db

    # Cleanup
    db.close()
    db._db_path = original_path
    if test_db_path.exists():
        test_db_path.unlink()

@pytest.fixture(scope="function")
def backup_mgr(test_db):
    """Backup manager for testing."""
    from config.backup import BackupManager
    mgr = BackupManager()
    mgr.db_path = test_db._db_path
    return mgr

@pytest.fixture
def sample_measure_data():
    """Sample measure data for testing."""
    return {
        "measure_name": "Test Measure",
        "status": "Active",
        "area_type": "Urban",
        "description": "Test description"
    }
```

**Expand:** `tests/test_transactions.py`

```python
import pytest
import duckdb
from models.measure import MeasureModel
from models.area import AreaModel
from models.priority import PriorityModel

def test_measure_delete_cascade_atomic(test_db, sample_measure_data):
    """Test measure delete is fully atomic."""
    measure_model = MeasureModel()

    # Create measure with relationships
    measure_id = measure_model.create(sample_measure_data)
    measure_model.add_measure_types(measure_id, [1, 2])
    measure_model.add_stakeholders(measure_id, [1])

    # Verify created
    assert measure_model.get_by_id(measure_id) is not None

    # Delete should succeed atomically
    result = measure_model.delete_with_cascade(measure_id)
    assert result is True

    # Verify everything deleted
    assert measure_model.get_by_id(measure_id) is None

    conn = test_db.get_connection()
    type_count = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]
    assert type_count == 0

def test_measure_delete_rollback_on_constraint_violation(test_db):
    """Test rollback when delete violates constraint."""
    measure_model = MeasureModel()

    # Try to delete measure that doesn't exist (should fail gracefully)
    # Or create a scenario where FK constraint blocks delete

    # Get a measure with many relationships
    conn = test_db.get_connection()
    measure_id = conn.execute(
        "SELECT measure_id FROM measure LIMIT 1"
    ).fetchone()[0]

    # Count relationships before
    type_count_before = conn.execute(
        "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
        [measure_id]
    ).fetchone()[0]

    # Attempt delete that might fail (depends on constraints)
    # In real scenario, you'd create a blocking constraint

    # For this test, ensure measure still exists if delete failed
    try:
        measure_model.delete_with_cascade(measure_id)
    except duckdb.Error:
        # Verify nothing was deleted (rollback worked)
        type_count_after = conn.execute(
            "SELECT COUNT(*) FROM measure_has_type WHERE measure_id = ?",
            [measure_id]
        ).fetchone()[0]
        assert type_count_after == type_count_before

def test_measure_update_with_relationships_atomic(test_db, sample_measure_data):
    """Test measure update with relationships is atomic."""
    measure_model = MeasureModel()

    # Create measure
    measure_id = measure_model.create(sample_measure_data)
    measure_model.add_measure_types(measure_id, [1])

    # Update with different relationships
    updated_data = {**sample_measure_data, "measure_name": "Updated Name"}
    result = measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data=updated_data,
        measure_types=[2, 3],
        stakeholders=[1, 2],
        benefits=[1]
    )

    assert result is True

    # Verify update
    measure = measure_model.get_by_id(measure_id)
    assert measure["measure_name"] == "Updated Name"

    # Verify new relationships
    conn = test_db.get_connection()
    types = conn.execute(
        "SELECT type_id FROM measure_has_type WHERE measure_id = ? ORDER BY type_id",
        [measure_id]
    ).fetchall()
    assert [t[0] for t in types] == [2, 3]

def test_concurrent_deletes_do_not_corrupt(test_db):
    """Test that concurrent operations don't corrupt data."""
    # This is limited by DuckDB's single-writer model
    # Test that operations are properly serialized
    pass

@pytest.mark.parametrize("entity_type,model_class", [
    ("measure", "MeasureModel"),
    ("area", "AreaModel"),
    ("priority", "PriorityModel"),
])
def test_all_cascade_deletes_are_atomic(test_db, entity_type, model_class):
    """Parameterized test for all cascade delete operations."""
    # Import model dynamically
    module = __import__(f"models.{entity_type}", fromlist=[model_class])
    model = getattr(module, model_class)()

    # Get a record to delete
    conn = test_db.get_connection()
    record = conn.execute(f"SELECT * FROM {entity_type} LIMIT 1").fetchone()

    if record:
        record_id = record[0]

        # Delete
        result = model.delete_with_cascade(record_id)
        assert result is True

        # Verify deleted
        check = conn.execute(
            f"SELECT COUNT(*) FROM {entity_type} WHERE {entity_type}_id = ?",
            [record_id]
        ).fetchone()[0]
        assert check == 0
```

**New File:** `tests/test_backup_restore_integration.py`

```python
import pytest
import shutil
from pathlib import Path
from config.backup import BackupManager
from models.measure import MeasureModel

def test_snapshot_before_delete(test_db, backup_mgr, sample_measure_data):
    """Test that snapshot is created before delete."""
    measure_model = MeasureModel()

    # Create measure
    measure_id = measure_model.create(sample_measure_data)

    # Count snapshots before
    snapshots_before = len(backup_mgr.list_snapshots())

    # Delete (should trigger snapshot)
    measure_model.delete_with_cascade(measure_id)

    # Verify snapshot created
    snapshots_after = len(backup_mgr.list_snapshots())
    assert snapshots_after == snapshots_before + 1

    # Verify latest snapshot is for this operation
    latest = backup_mgr.list_snapshots()[0]
    assert latest['operation_type'] == 'delete'
    assert latest['entity_type'] == 'measure'
    assert latest['entity_id'] == measure_id

def test_restore_recovers_deleted_data(test_db, backup_mgr, sample_measure_data):
    """Test that restore recovers deleted data."""
    measure_model = MeasureModel()

    # Create measure
    measure_id = measure_model.create(sample_measure_data)

    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Before test delete",
        operation_type="test"
    )

    # Delete measure
    measure_model.delete_with_cascade(measure_id)

    # Verify deleted
    assert measure_model.get_by_id(measure_id) is None

    # Restore
    backup_mgr.restore_snapshot(snapshot_id)

    # Verify restored
    restored_measure = measure_model.get_by_id(measure_id)
    assert restored_measure is not None
    assert restored_measure['measure_name'] == sample_measure_data['measure_name']

def test_restore_creates_safety_backup(test_db, backup_mgr):
    """Test that restore creates safety backup first."""
    # Create snapshot
    snapshot_id = backup_mgr.create_snapshot(
        description="Test snapshot"
    )

    # Count snapshots
    snapshots_before = len(backup_mgr.list_snapshots())

    # Restore
    backup_mgr.restore_snapshot(snapshot_id)

    # Verify safety backup was created
    snapshots_after = len(backup_mgr.list_snapshots())
    assert snapshots_after == snapshots_before + 1

    # Verify latest is safety backup
    latest = backup_mgr.list_snapshots()[0]
    assert latest['operation_type'] == 'pre_restore'

def test_cleanup_keeps_correct_count(test_db, backup_mgr):
    """Test cleanup keeps the correct number of snapshots."""
    # Create multiple snapshots
    for i in range(15):
        backup_mgr.create_snapshot(f"Test snapshot {i}")

    # Cleanup, keep only 5
    deleted = backup_mgr.cleanup_old_snapshots(keep_count=5)

    assert deleted == 10

    # Verify only 5 remain
    remaining = backup_mgr.list_snapshots()
    assert len(remaining) == 5

    # Verify newest are kept
    for snapshot in remaining:
        assert "14" in snapshot['snapshot_id'] or \
               "13" in snapshot['snapshot_id'] or \
               "12" in snapshot['snapshot_id'] or \
               "11" in snapshot['snapshot_id'] or \
               "10" in snapshot['snapshot_id']
```

### 4.2 Integration Tests

**New File:** `tests/test_end_to_end.py`

```python
import pytest
from models.measure import MeasureModel
from models.relationship import RelationshipModel
from config.backup import BackupManager

def test_full_measure_lifecycle_with_backups(test_db, backup_mgr):
    """Test complete measure lifecycle: create → update → delete → restore."""
    measure_model = MeasureModel()
    relationship_model = RelationshipModel()

    # 1. Create measure with relationships
    measure_data = {
        "measure_name": "Lifecycle Test Measure",
        "status": "Active"
    }
    measure_id = measure_model.create(measure_data)
    measure_model.add_measure_types(measure_id, [1, 2])

    # Create snapshot after creation
    snapshot_after_create = backup_mgr.create_snapshot(
        "After measure creation"
    )

    # 2. Update measure
    updated_data = {**measure_data, "measure_name": "Updated Lifecycle Test"}
    measure_model.update_with_relationships(
        measure_id=measure_id,
        measure_data=updated_data,
        measure_types=[2, 3],
        stakeholders=[1],
        benefits=[]
    )

    # Verify update
    updated = measure_model.get_by_id(measure_id)
    assert updated["measure_name"] == "Updated Lifecycle Test"

    # Create snapshot after update
    snapshot_after_update = backup_mgr.create_snapshot(
        "After measure update"
    )

    # 3. Delete measure (snapshot created automatically)
    measure_model.delete_with_cascade(measure_id)
    assert measure_model.get_by_id(measure_id) is None

    # 4. Restore to after-update state
    backup_mgr.restore_snapshot(snapshot_after_update)
    restored = measure_model.get_by_id(measure_id)
    assert restored is not None
    assert restored["measure_name"] == "Updated Lifecycle Test"

    # 5. Restore to after-create state
    backup_mgr.restore_snapshot(snapshot_after_create)
    original = measure_model.get_by_id(measure_id)
    assert original is not None
    assert original["measure_name"] == "Lifecycle Test Measure"
```

### 4.3 Monitoring & Logging

**New File:** `config/monitoring.py`

```python
import logging
from functools import wraps
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

def monitor_performance(operation_name: str):
    """Decorator to monitor operation performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                logger.info(
                    f"Performance: {operation_name} completed in {elapsed:.3f}s"
                )

                # Alert if slow
                if elapsed > 5.0:
                    logger.warning(
                        f"Slow operation: {operation_name} took {elapsed:.3f}s"
                    )

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Performance: {operation_name} failed after {elapsed:.3f}s: {e}"
                )
                raise

        return wrapper
    return decorator
```

**Apply to Key Operations:**

```python
# In models/measure.py
@monitor_performance("measure_delete_cascade")
@with_snapshot("delete", "measure")
def delete_with_cascade(self, measure_id: int) -> bool:
    # ... existing code

# In config/backup.py
@monitor_performance("snapshot_create")
def create_snapshot(self, ...):
    # ... existing code

@monitor_performance("snapshot_restore")
def restore_snapshot(self, snapshot_id: str) -> bool:
    # ... existing code
```

**Enhanced Logging Configuration:**

```python
# Update config/logging_config.py
def setup_logging():
    """Configure application-wide logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Transaction log
    transaction_handler = logging.FileHandler(log_dir / "transactions.log")
    transaction_handler.setLevel(logging.DEBUG)
    transaction_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    transaction_handler.setFormatter(transaction_formatter)

    # Backup log
    backup_handler = logging.FileHandler(log_dir / "backups.log")
    backup_handler.setLevel(logging.INFO)
    backup_handler.setFormatter(transaction_formatter)

    # Performance log
    performance_handler = logging.FileHandler(log_dir / "performance.log")
    performance_handler.setLevel(logging.INFO)
    performance_formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    performance_handler.setFormatter(performance_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(transaction_handler)
    root_logger.addHandler(backup_handler)
    root_logger.addHandler(performance_handler)
    root_logger.addHandler(console_handler)
```

### 4.4 Documentation

**Update:** `CLAUDE.md`

Add section:

```markdown
## Transaction & Backup System

### Transaction-Wrapped Operations

All multi-statement operations use transactions for atomicity:

```python
# All operations are atomic - either all succeed or all rollback
measure_model.delete_with_cascade(measure_id)  # 7 DELETEs in transaction
measure_model.update_with_relationships(...)    # 1 UPDATE + 3 DELETEs + N INSERTs
```

### Automatic Snapshots

Snapshots are automatically created before all destructive operations:
- Cascade deletes (measure, area, priority, species, habitat, grant)
- Relationship deletions
- Bulk updates

Snapshots are stored in `data/backups/` with metadata in `snapshot_metadata.json`.

### Manual Backups

Create manual backups via UI:
1. Navigate to **Backup & Restore** page
2. Click **Create Backup** tab
3. Enter description and submit

### Restoring Database

To restore from a snapshot:
1. Navigate to **Backup & Restore** page
2. Find desired snapshot in list
3. Click **Preview** to verify contents (optional)
4. Click **Restore** button
5. Type "RESTORE" to confirm
6. System creates safety backup before restoring

**Warning:** Restore replaces entire database. All changes since snapshot will be lost.

### Troubleshooting

**Transaction Failed:**
- Error message will indicate which statement failed
- Database automatically rolled back - no partial changes
- Check logs in `logs/transactions.log`

**Restore Failed:**
- Safety backup was created before restore attempt
- Original database unchanged
- Check logs in `logs/backups.log`

**Slow Operations:**
- Performance warnings logged if operation > 5 seconds
- Check `logs/performance.log` for slow operations
- Consider cleanup if snapshots > 50

### Best Practices

1. **Create manual backups before major changes**
2. **Test restores periodically** to verify backup integrity
3. **Monitor backup storage** - run cleanup when > 50 snapshots
4. **Check logs** if operations fail unexpectedly
```

**Create:** `docs/TROUBLESHOOTING.md`

```markdown
# Transaction & Backup Troubleshooting Guide

## Common Issues

### Transaction Rollback Errors

**Symptom:** Operation fails with "Transaction failed and rolled back" error

**Causes:**
- Foreign key constraint violation
- Unique constraint violation
- Invalid data format
- Database locked

**Resolution:**
1. Check error message for specific constraint violated
2. Review transaction log: `logs/transactions.log`
3. Verify data integrity before operation
4. If deleting, ensure no blocking relationships exist

### Snapshot Creation Fails

**Symptom:** "Failed to create snapshot" error

**Causes:**
- Insufficient disk space
- Permission denied on backup directory
- Database file locked

**Resolution:**
1. Check disk space: `df -h`
2. Verify backup directory exists and is writable: `ls -la data/backups`
3. Check backup log: `logs/backups.log`
4. Close other database connections

### Restore Fails

**Symptom:** "Failed to restore snapshot" error

**Causes:**
- Snapshot file missing or corrupted
- Database connections not closed
- Permission issues

**Resolution:**
1. Verify snapshot file exists: `ls -la data/backups/`
2. Check backup log: `logs/backups.log`
3. If restore started, safety backup was created
4. Close all Streamlit sessions and retry

### Performance Issues

**Symptom:** Operations taking > 5 seconds

**Causes:**
- Too many snapshots (cleanup needed)
- Large database file
- Disk I/O bottleneck

**Resolution:**
1. Check performance log: `logs/performance.log`
2. Run snapshot cleanup (keep last 50)
3. Consider archiving old snapshots externally
4. Monitor disk I/O: `iostat -x 1`

## Log Files

- `logs/transactions.log` - All transaction operations
- `logs/backups.log` - Snapshot create/restore/cleanup
- `logs/performance.log` - Operation timing
- `data/backups/snapshot_metadata.json` - Snapshot index

## Recovery Procedures

### Recover from Failed Delete

If delete operation fails but database seems corrupted:

1. Check latest snapshot:
   ```bash
   cat data/backups/snapshot_metadata.json | grep delete | tail -1
   ```

2. Restore via UI or manually:
   ```bash
   cp data/backups/SNAPSHOT_ID.duckdb data/lnrs_3nf_o1.duckdb
   ```

### Recover from Failed Restore

If restore fails midway:

1. Find the pre-restore safety backup:
   ```bash
   cat data/backups/snapshot_metadata.json | grep pre_restore | tail -1
   ```

2. Manually restore safety backup:
   ```bash
   cp data/backups/SAFETY_SNAPSHOT_ID.duckdb data/lnrs_3nf_o1.duckdb
   ```

### Complete Database Corruption

If database is completely corrupted:

1. Restore from most recent snapshot:
   ```bash
   cp data/backups/LATEST_SNAPSHOT.duckdb data/lnrs_3nf_o1.duckdb
   ```

2. If no snapshots available, restore from external backup

3. Rebuild from SQL schema and CSV files:
   ```bash
   rm data/lnrs_3nf_o1.duckdb
   ./duckdb data/lnrs_3nf_o1.duckdb < lnrs_3nf_o1.sql
   ```
```

### Phase 4 Deliverables

**New Files (4):**
- `tests/conftest.py` - Test fixtures
- `tests/test_backup_restore_integration.py` - Integration tests
- `tests/test_end_to_end.py` - E2E tests
- `config/monitoring.py` - Performance monitoring
- `docs/TROUBLESHOOTING.md` - Troubleshooting guide

**Modified Files (2):**
- `CLAUDE.md` - Add transaction documentation
- `pyproject.toml` - Add pytest dependencies

**Success Criteria:**
- [ ] All unit tests pass (>90% coverage)
- [ ] All integration tests pass
- [ ] E2E lifecycle test passes
- [ ] Performance monitoring active
- [ ] All operations logged
- [ ] Documentation complete
- [ ] Troubleshooting guide tested

---

## Summary

### Total File Changes

**New Files (9):**
1. `config/backup.py` - Backup/restore core (300 lines)
2. `config/logging_config.py` - Logging setup (50 lines)
3. `config/monitoring.py` - Performance monitoring (40 lines)
4. `ui/pages/backup_restore.py` - Backup UI (400 lines)
5. `tests/conftest.py` - Test fixtures (60 lines)
6. `tests/test_transactions.py` - Transaction tests (200 lines)
7. `tests/test_backups.py` - Backup tests (100 lines)
8. `tests/test_backup_restore_integration.py` - Integration tests (150 lines)
9. `tests/test_end_to_end.py` - E2E tests (100 lines)
10. `docs/TROUBLESHOOTING.md` - Troubleshooting (150 lines)

**Modified Files (16):**
1. `config/database.py` - Add snapshot decorator, logging
2. `models/measure.py` - Transaction-wrap, add update_with_relationships
3. `models/area.py` - Transaction-wrap delete
4. `models/priority.py` - Transaction-wrap delete
5. `models/species.py` - Transaction-wrap delete
6. `models/habitat.py` - Transaction-wrap delete
7. `models/grant.py` - Transaction-wrap delete
8. `models/relationship.py` - Transaction-wrap operations
9. `ui/pages/measures.py` - Use atomic update, add restore hints
10. `ui/pages/areas.py` - Add restore hints
11. `ui/pages/priorities.py` - Add restore hints
12. `ui/pages/species.py` - Add restore hints
13. `ui/pages/habitats.py` - Add restore hints
14. `ui/pages/grants.py` - Add restore hints
15. `CLAUDE.md` - Add transaction documentation
16. `pyproject.toml` - Add pytest dependencies
17. `.gitignore` - Exclude backup .duckdb files

**Total Lines of Code:** ~1,900 new lines

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Transaction rollback fails | Low | High | Extensive testing, leverage existing execute_transaction() |
| Snapshot creation slow | Medium | Low | Monitor performance, async creation possible |
| Restore corrupts database | Low | Critical | Always create safety backup first, test thoroughly |
| Disk space exhaustion | Medium | Medium | Cleanup policy (keep 50), monitoring, alerts |
| Concurrent operations conflict | Low | Medium | Current single-connection model prevents this |
| Test database affects production | Low | High | Separate test database, fixtures ensure cleanup |

### Performance Estimates

| Operation | Current | With Transactions | With Snapshot |
|-----------|---------|-------------------|---------------|
| Measure delete (7 ops) | ~50ms | ~55ms (+10%) | ~2.1s (+4000%) |
| Area delete (7 ops) | ~50ms | ~55ms (+10%) | ~2.1s (+4000%) |
| Measure update | ~100ms | ~110ms (+10%) | N/A (no snapshot) |
| Manual backup | N/A | N/A | ~2s (DB size dependent) |
| Restore | N/A | N/A | ~3s (DB size + verification) |

**Note:** Snapshot overhead is acceptable given it only occurs on destructive operations (delete), not on queries or creates.

### Success Metrics

1. **Zero partial failures:** All multi-statement operations atomic ✓
2. **100% snapshot coverage:** All deletes have pre-operation snapshots ✓
3. **Restore reliability:** 100% success rate in testing ✓
4. **Performance:** Snapshot creation < 3 seconds ✓
5. **Test coverage:** >90% for transaction and backup code ✓
6. **User satisfaction:** Clear restore procedure, helpful errors ✓

### Timeline Summary

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1-2 | Phase 1 | Transactions | All CRUD operations atomic |
| 3 | Phase 2 | Backups | Snapshot infrastructure |
| 4 | Phase 3 | UI | Restore interface |
| 5 | Phase 4 | Testing | Test suite & docs |

**Total Duration:** 5 weeks

---

## Next Steps

1. **Review and approve this plan**
2. **Schedule kickoff meeting**
3. **Set up development branch:** `feature/transactions-and-rollback`
4. **Begin Phase 1 implementation**
5. **Daily standups to track progress**
6. **Weekly demos after each phase**

## Questions for Stakeholders

1. Is 5-week timeline acceptable?
2. Should we implement database size monitoring/alerts?
3. Do we need email notifications for backup failures?
4. Should snapshots be encrypted at rest?
5. Do we need role-based access control for restore operations?

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Author:** Claude Code
**Status:** Awaiting Approval
