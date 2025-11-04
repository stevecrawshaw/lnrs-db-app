# Streamlit Deployment with MotherDuck - Implementation Plan

## Executive Summary

This document outlines the complete plan for migrating the LNRS Database CRUD application from a local DuckDB file to MotherDuck cloud database, enabling successful deployment to Streamlit Community Cloud or Hugging Face Spaces.

**Key Facts:**
- **Current database**: 21MB local DuckDB file (`data/lnrs_3nf_o1.duckdb`)
- **Target database**: MotherDuck cloud database (`lnrs_weca`)
- **Database already created**: Yes, via `lnrs_to_motherduck.sql`
- **MotherDuck token**: Available in `.env` file
- **Estimated implementation time**: 4-5 hours
- **Risk level**: Low (minimal code changes required)

---

## Problem Analysis

### Current Architecture Challenges

#### 1. Local File Dependency
The application currently uses a hardcoded path to a local DuckDB file:

```python
# config/database.py line 41
db_path = Path(__file__).parent.parent / "data" / "lnrs_3nf_o1.duckdb"
```

#### 2. Deployment Platform Constraints

**Streamlit Community Cloud:**
- Ephemeral filesystem (changes lost on restart)
- Read-only or temporary storage for app files
- No way to persist database writes between deployments

**Hugging Face Spaces:**
- Similar ephemeral storage constraints
- Database changes would be lost on restart

#### 3. Current Database Operations
All CRUD operations go through:
- Singleton `DatabaseConnection` class
- Single persistent connection
- Custom macros loaded on connection (`max_meas()`)
- All models inherit from `BaseModel` which uses `db.get_connection()`

### Why MotherDuck is the Solution

| Requirement | MotherDuck Solution |
|------------|---------------------|
| Persistent storage | Database lives in cloud, not on app server |
| Free hosting | 10GB storage (need <0.3%), 5 users, 10 CU hours/month |
| Same syntax | DuckDB API unchanged, minimal code modifications |
| Easy integration | Connection string change only |
| Data safety | Automated backups, high availability |

---

## Architecture Overview

### Connection Flow Comparison

**Current (Local):**
```
Streamlit App → DatabaseConnection → Local DuckDB File
                                    (data/lnrs_3nf_o1.duckdb)
```

**Target (MotherDuck):**
```
Streamlit App → DatabaseConnection → MotherDuck Cloud
                                    (md:lnrs_weca?token=...)
```

### Environment Detection Strategy

```
┌─────────────────────────────────────────────────────┐
│ Application Startup                                  │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│ Check DATABASE_MODE environment variable             │
│ - "local"      → Use local DuckDB file              │
│ - "motherduck" → Use MotherDuck connection          │
│ - Not set      → Auto-detect based on environment   │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│ Load Configuration                                   │
│ - Local: Read from .env file                        │
│ - Cloud: Read from st.secrets                       │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│ Create Connection                                    │
│ - Local: duckdb.connect("data/lnrs_3nf_o1.duckdb") │
│ - Cloud: duckdb.connect("md:lnrs_weca?token=...")  │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Plan

## Phase 1: Environment & Configuration Setup ✅ COMPLETED

**Duration**: 30 minutes (Actual: 25 minutes)
**Risk Level**: Low
**Status**: ✅ Complete

### 1.1 Update Project Dependencies

**Use `uv add` to change the project dependencies. Do not edit the pyproject.toml file**

**File**: `pyproject.toml`

**Changes needed**:
```toml
dependencies = [
    "duckdb>=1.4.1",
    "ipykernel>=7.1.0",
    "polars>=1.34.0",
    "pyarrow>=21.0.0",
    "sqlfluff>=3.5.0",
    "streamlit>=1.50.0",
    "python-dotenv>=1.0.0",  # NEW: For loading .env files
]
```

### 1.2 Create Streamlit Secrets Directory and Template

**New Directory**: `.streamlit/`

**New File**: `.streamlit/secrets.toml.template`

**Contents**:
```toml
# Streamlit Secrets Configuration Template
# Copy this file to .streamlit/secrets.toml and fill in your values
# DO NOT commit secrets.toml to git!

# Database configuration
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"

# MotherDuck authentication token
# Get your token from: https://app.motherduck.com/
motherduck_token = "your_motherduck_token_here"
```

**New File**: `.streamlit/secrets.toml` (for local MotherDuck testing)

**Contents**:
```toml
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "YOUR_MOTHERDUCK_TOKEN_HERE"
```

**Note**: Replace `YOUR_MOTHERDUCK_TOKEN_HERE` with your actual token from `.env` file.

### 1.3 Update .env File for Local Development

**File**: `.env`

**Current**:
```bash
motherduck_token="..."
```

**Updated**:
```bash
# Local development mode
DATABASE_MODE="local"

# MotherDuck configuration (used when DATABASE_MODE="motherduck")
motherduck_token="YOUR_MOTHERDUCK_TOKEN_HERE"
database_name="lnrs_weca"
```

**Note**: This file is excluded from git via `.gitignore`.

### 1.4 Update .gitignore

**File**: `.gitignore`

**Add these lines**:
```gitignore
# Environment files
.env
.env.*

# Streamlit secrets
.streamlit/secrets.toml

# Local database files
data/*.duckdb
data/*.duckdb.wal

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Virtual environments
venv/
env/
ENV/
```

### 1.5 Create requirements.txt for Deployment ✅

**New File**: `requirements.txt`

**Contents**:
```txt
duckdb>=1.4.1
streamlit>=1.50.0
polars>=1.34.0
pyarrow>=21.0.0
python-dotenv>=1.2.1
```

**Status**: ✅ Created

---

### Phase 1 Summary

**Completed Tasks**:
- ✅ Added `python-dotenv>=1.2.1` dependency via `uv add`
- ✅ Created `.streamlit/` directory
- ✅ Created `.streamlit/secrets.toml.template` (template for deployment)
- ✅ Created `.streamlit/secrets.toml` (for local MotherDuck testing)
- ✅ Updated `.env` with `DATABASE_MODE="local"` and organized configuration
- ✅ Updated `.gitignore` to exclude:
  - `.env` and `.env.*`
  - `.streamlit/secrets.toml`
  - `*.duckdb` and `*.duckdb.wal`
- ✅ Created `requirements.txt` for Streamlit Cloud deployment

**Files Created**:
1. `.streamlit/secrets.toml.template` - Template for secrets configuration
2. `.streamlit/secrets.toml` - Local secrets (with MotherDuck token)
3. `requirements.txt` - Deployment dependencies

**Files Modified**:
1. `pyproject.toml` - Added python-dotenv dependency
2. `.env` - Added DATABASE_MODE and organized configuration
3. `.gitignore` - Added security exclusions

**Next Steps**: Proceed to Phase 2 - Database Connection Refactoring

---

## Phase 2: Database Connection Refactoring ✅ COMPLETED

**Duration**: 1-2 hours (Actual: 45 minutes)
**Risk Level**: Medium (core functionality changes)
**Status**: ✅ Complete

### 2.1 Refactor config/database.py

This is the main file that needs modification. Below is the complete refactored version with detailed comments:

**File**: `config/database.py`

**Key Changes**:
1. Add configuration loading helper
2. Add connection factory method
3. Update `get_connection()` to use factory
4. Add connection status methods
5. Ensure macros work in both environments

**Implementation Notes**:
- Import `os`, `streamlit as st`, and `dotenv`
- Add `_get_config()` method to load environment variables
- Add `_create_local_connection()` method
- Add `_create_motherduck_connection()` method
- Modify `get_connection()` to call appropriate factory method
- Add `get_connection_info()` method for debugging
- Keep all existing CRUD methods unchanged

### 2.2 Connection Configuration Priority

The configuration loading should follow this priority:

1. **Streamlit Secrets** (highest priority - for deployed apps)
   - Check `st.secrets` first

2. **Environment Variables** (for CI/CD or containers)
   - Check `os.environ`

3. **.env File** (for local development)
   - Load via `python-dotenv`

4. **Auto-detect** (fallback)
   - If `STREAMLIT_SHARING_MODE` exists → use MotherDuck
   - Otherwise → use local

### 2.3 Database Mode Logic

```python
def _get_database_mode() -> str:
    """Determine which database mode to use.

    Returns:
        str: "local" or "motherduck"
    """
    # Priority 1: Explicit setting in Streamlit secrets
    try:
        return st.secrets["DATABASE_MODE"]
    except (KeyError, FileNotFoundError):
        pass

    # Priority 2: Environment variable
    mode = os.getenv("DATABASE_MODE")
    if mode:
        return mode.lower()

    # Priority 3: Auto-detect based on Streamlit Cloud
    if os.getenv("STREAMLIT_SHARING_MODE"):
        return "motherduck"

    # Priority 4: Default to local
    return "local"
```

### 2.4 MotherDuck Connection String Format

```python
# Format: md:database_name?motherduck_token=TOKEN
connection_string = f"md:{database_name}?motherduck_token={token}"

# Example:
# md:lnrs_weca?motherduck_token=eyJhbGc...
```

### 2.5 Macro Loading Strategy

Macros may not persist in MotherDuck, so they should be recreated on every connection:

```python
def _load_macros(self) -> None:
    """Load custom macros into the database.

    Creates the max_meas() macro for generating new measure IDs.
    Macros are recreated each time to ensure they exist in both
    local and MotherDuck environments.
    """
    try:
        # Drop if exists to ensure clean state
        self._connection.execute("DROP MACRO IF EXISTS max_meas")

        # Create max_meas() macro
        self._connection.execute(
            "CREATE MACRO max_meas() AS "
            "(SELECT COALESCE(MAX(measure_id), 0) + 1 FROM measure)"
        )
        print("✓ Macros loaded successfully")
    except duckdb.Error as e:
        print(f"Warning: Failed to load macros: {e}")
```

---

### Phase 2 Summary

**Completed Tasks**:
- ✅ Refactored `config/database.py` with dual-mode support (local/MotherDuck)
- ✅ Added environment detection logic with proper priority:
  1. `.env` file (DATABASE_MODE variable)
  2. Streamlit secrets
  3. Auto-detect Streamlit Cloud
  4. Default to local
- ✅ Created `_create_local_connection()` method
- ✅ Created `_create_motherduck_connection()` method
- ✅ Added `get_connection_info()` for debugging
- ✅ Updated macro loading to work in both environments
- ✅ Fixed character encoding issues (replaced ✓ with [OK])
- ✅ All existing CRUD methods remain unchanged

**Key Features Implemented**:
1. **Connection Factory Pattern**: Separate methods for local vs MotherDuck
2. **Configuration Priority**: `.env` takes precedence for local development
3. **Error Handling**: Clear error messages for missing configuration
4. **Backward Compatibility**: All existing code continues to work unchanged
5. **Debugging Support**: `get_connection_info()` shows current mode and database

**Files Modified**:
1. `config/database.py` - Complete refactoring with 390 lines
   - Added `import os` and `from dotenv import load_dotenv`
   - Added Streamlit import with fallback
   - Added `_get_database_mode()` method
   - Added `_get_config()` method
   - Added `_create_local_connection()` method
   - Added `_create_motherduck_connection()` method
   - Added `get_connection_info()` method
   - Updated `get_connection()` to use factory methods
   - Updated `_load_macros()` to drop before creating

**Testing Results**:
- ✅ Mode detection works correctly (respects DATABASE_MODE="local")
- ✅ Configuration loading works (reads from .env file)
- ✅ Error messages are clear and helpful
- ⚠️ Full testing requires closing any open database connections

**Next Steps**: Proceed to Phase 3 - Schema & Data Validation

---

## Phase 3: Schema & Data Validation

**Duration**: 30 minutes
**Risk Level**: Low

### 3.1 Create Validation Script

**New File**: `validate_motherduck_schema.py`

**Purpose**: Verify that MotherDuck database matches local structure

**Validation Checks**:
1. All tables exist in MotherDuck
2. Table row counts match
3. Column names and types match
4. Views exist and work
5. Foreign key constraints exist
6. Macros can be created

**Expected Output**:
```
LNRS Database Schema Validation
================================

Connection Status:
✓ Local connection successful
✓ MotherDuck connection successful

Table Validation:
✓ measure: 780 rows (local) = 780 rows (motherduck)
✓ area: 68 rows (local) = 68 rows (motherduck)
✓ priority: 33 rows (local) = 33 rows (motherduck)
...

View Validation:
✓ source_table_recreated_vw exists
✓ apmg_slim_vw exists

Macro Validation:
✓ max_meas() macro works

Foreign Key Validation:
✓ All foreign key constraints present

Overall Status: ✓ PASSED
```

### 3.2 Run Verification Queries

Use the queries from `lnrs_to_motherduck.sql` lines 437-456:

```sql
-- Verify row counts match
SELECT 'measure' AS table_name, COUNT(*) AS count FROM measure
UNION ALL
SELECT 'area', COUNT(*) FROM area
UNION ALL
SELECT 'priority', COUNT(*) FROM priority
UNION ALL
SELECT 'species', COUNT(*) FROM species
UNION ALL
SELECT 'grant_table', COUNT(*) FROM grant_table
UNION ALL
SELECT 'measure_area_priority', COUNT(*) FROM measure_area_priority
UNION ALL
SELECT 'measure_area_priority_grant', COUNT(*) FROM measure_area_priority_grant;

-- Verify views work
SELECT COUNT(*) AS view_count FROM apmg_slim_vw;
```

---

## Phase 4: Application Code Updates

**Duration**: 15 minutes
**Risk Level**: Very Low

### 4.1 No Changes Required to Models

**Files that DO NOT need changes**:
- `models/base.py` - Uses `db.get_connection()` abstraction
- `models/measure.py` - Inherits from BaseModel
- `models/area.py` - Inherits from BaseModel
- `models/priority.py` - Inherits from BaseModel
- `models/species.py` - Inherits from BaseModel
- `models/grant.py` - Inherits from BaseModel
- `models/habitat.py` - Inherits from BaseModel
- `models/relationship.py` - Uses `db.execute_query()`

**Why no changes needed**: All models use the `db` singleton which abstracts the connection type.

### 4.2 No Changes Required to UI Pages

**Files that DO NOT need changes**:
- `ui/pages/home.py`
- `ui/pages/measures.py`
- `ui/pages/areas.py`
- `ui/pages/priorities.py`
- `ui/pages/species.py`
- `ui/pages/grants.py`
- `ui/pages/habitats.py`
- `ui/pages/relationships.py`
- `ui/pages/data_export.py`
- `app.py`

### 4.3 Optional: Add Connection Status to Dashboard

**File**: `ui/pages/home.py`

**Optional enhancement** - Add connection info to the dashboard:

```python
# Add to the dashboard page
import streamlit as st
from config.database import db

# Show connection status
st.sidebar.divider()
st.sidebar.subheader("Database Status")

conn_info = db.get_connection_info()
st.sidebar.write(f"**Mode**: {conn_info['mode'].title()}")
st.sidebar.write(f"**Status**: {'🟢 Connected' if conn_info['connected'] else '🔴 Disconnected'}")

if conn_info['mode'] == 'motherduck':
    st.sidebar.write(f"**Database**: {conn_info['database']}")
```

---

## Phase 5: Testing & Validation

**Duration**: 1 hour
**Risk Level**: Low

### 5.1 Local Mode Testing

**Setup**:
```bash
# Set environment to local mode
echo 'DATABASE_MODE="local"' > .env
```

**Test Checklist**:
- [ ] App starts without errors
- [ ] Dashboard loads and shows correct counts
- [ ] Can view all entity tables (measures, areas, etc.)
- [ ] Can create new records
- [ ] Can update existing records
- [ ] Can delete records (with proper cascading)
- [ ] Can create relationships between entities
- [ ] Data export functionality works
- [ ] Macros work (max_meas() returns correct value)

**Test Script**: `test_local_mode.py`

### 5.2 MotherDuck Mode Testing (Local)

**Setup**:
```bash
# Method 1: Via .env
echo 'DATABASE_MODE="motherduck"' > .env

# Method 2: Via Streamlit secrets
# Edit .streamlit/secrets.toml and set DATABASE_MODE = "motherduck"
```

**Test Checklist**:
- [ ] App starts and connects to MotherDuck
- [ ] Dashboard loads and shows correct counts
- [ ] Can view all entity tables
- [ ] Can create new records
- [ ] Can update existing records
- [ ] Can delete records
- [ ] Restart app and verify data persists
- [ ] Check MotherDuck web UI to confirm writes
- [ ] Verify macros work
- [ ] Test concurrent operations (if possible)

**Test Script**: `test_motherduck_mode.py`

### 5.3 Performance Testing

**Metrics to collect**:
- Page load time (local vs MotherDuck)
- Query execution time for common operations
- Large dataset operations (viewing 1000+ records)
- Complex joins (relationship queries)

**Expected Results**:
- Local: < 100ms for most queries
- MotherDuck: < 500ms for most queries (acceptable)

**If performance is slow**:
- Check MotherDuck connection quality
- Consider adding indexes
- Optimize complex queries
- Use pagination for large result sets

### 5.4 Macro Behavior Testing

**Test**: Verify `max_meas()` macro

**Local Test**:
```python
result = db.execute_query("SELECT max_meas() as next_id")
print(f"Next measure ID: {result.fetchone()[0]}")
```

**MotherDuck Test**:
```python
# Same test, but in MotherDuck mode
result = db.execute_query("SELECT max_meas() as next_id")
print(f"Next measure ID: {result.fetchone()[0]}")
```

**Expected**: Both should return the same value (next available measure_id)

### 5.5 Error Handling Testing

**Test Scenarios**:
1. Invalid MotherDuck token → Should show clear error message
2. Network failure → Should handle gracefully
3. Database not found → Should show helpful error
4. Table doesn't exist → Should show appropriate error

**Test Script**: `test_error_handling.py`

---

## Phase 6: Deployment Preparation

**Duration**: 30 minutes
**Risk Level**: Low

### 6.1 Verify requirements.txt

**File**: `requirements.txt`

**Contents**:
```txt
duckdb>=1.4.1
streamlit>=1.50.0
polars>=1.34.0
pyarrow>=21.0.0
python-dotenv>=1.0.0
```

**Note**: Streamlit Cloud uses `requirements.txt`, not `pyproject.toml`

### 6.2 Create Deployment Documentation

**New File**: `DEPLOYMENT.md`

**Contents**:

```markdown
# Deployment Guide - LNRS Database Application

## Prerequisites

1. MotherDuck account with `lnrs_weca` database created
2. MotherDuck API token
3. GitHub repository with application code
4. Streamlit Community Cloud account (free)

## Deployment Steps

### 1. Prepare GitHub Repository

Ensure these files are committed:
- `app.py`
- `requirements.txt`
- `config/database.py` (updated version)
- All `ui/` and `models/` files
- `.gitignore` (ensure `.env` and `secrets.toml` are excluded)

### 2. Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repository
4. Set main file path: `app.py`
5. Click "Advanced settings"

### 3. Configure Secrets

In the Streamlit Cloud app settings, add these secrets:

```toml
DATABASE_MODE = "motherduck"
database_name = "lnrs_weca"
motherduck_token = "YOUR_MOTHERDUCK_TOKEN_HERE"
```

### 4. Deploy

Click "Deploy" and wait for the app to start.

### 5. Verify Deployment

- Check that the app loads without errors
- Verify data is visible in the dashboard
- Test a CRUD operation (create, read, update, or delete)
- Verify changes persist after app restart

## Troubleshooting

### App won't start
- Check Streamlit Cloud logs for errors
- Verify all secrets are set correctly
- Ensure `requirements.txt` is in repository root

### Can't connect to MotherDuck
- Verify MotherDuck token is valid
- Check database name is correct (`lnrs_weca`)
- Ensure token has write permissions

### Data not persisting
- Verify `DATABASE_MODE = "motherduck"` in secrets
- Check MotherDuck web UI to confirm writes are happening
- Review app logs for connection errors

## Monitoring

### MotherDuck Usage Dashboard
- URL: https://app.motherduck.com/
- Check compute usage (10 CU hours/month limit on free tier)
- Monitor storage usage (should be ~21MB)

### Streamlit Cloud Logs
- Available in app settings
- Check for errors or warnings
- Monitor performance metrics
```

### 6.3 Create Secrets Template Documentation

**New File**: `SECRETS_TEMPLATE.md`

**Contents**:

```markdown
# Streamlit Secrets Configuration

When deploying to Streamlit Community Cloud, you need to configure secrets in the app settings.

## How to Add Secrets

1. Go to your app in Streamlit Cloud
2. Click the menu (⋮) and select "Settings"
3. Click "Secrets" in the left sidebar
4. Paste the configuration below (with your actual values)

## Secrets Configuration

```toml
# Database mode - use "motherduck" for production
DATABASE_MODE = "motherduck"

# Database name in MotherDuck
database_name = "lnrs_weca"

# MotherDuck authentication token
# Get this from: https://app.motherduck.com/ → Settings → Tokens
motherduck_token = "YOUR_TOKEN_HERE"
```

## Getting Your MotherDuck Token

1. Go to https://app.motherduck.com/
2. Sign in to your account
3. Click your profile icon → Settings
4. Go to "Access Tokens"
5. Copy your token
6. Paste it in the `motherduck_token` field above

## Security Notes

- **NEVER** commit secrets to git
- **NEVER** share your token publicly
- Keep your `.env` file in `.gitignore`
- Keep `.streamlit/secrets.toml` in `.gitignore`
```

### 6.4 Final Pre-deployment Checklist

- [ ] All code committed to GitHub
- [ ] `.env` is in `.gitignore`
- [ ] `.streamlit/secrets.toml` is in `.gitignore`
- [ ] `requirements.txt` exists and is correct
- [ ] MotherDuck database `lnrs_weca` exists and has data
- [ ] MotherDuck token is valid and has write permissions
- [ ] Local testing passed (both modes)
- [ ] Documentation is complete
- [ ] Deployment guide is ready

---

## Phase 7: Deployment & Monitoring

**Duration**: 30 minutes
**Risk Level**: Low

### 7.1 Deploy to Streamlit Community Cloud

**Steps**:

1. **Create Streamlit Cloud Account**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub

2. **Connect Repository**
   - Click "New app"
   - Select your GitHub repository
   - Set main file: `app.py`
   - Set Python version: 3.13 (or your version)

3. **Configure Secrets**
   - Click "Advanced settings" before deploying
   - Add secrets from `SECRETS_TEMPLATE.md`
   - Ensure `DATABASE_MODE = "motherduck"`

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (2-5 minutes)
   - Monitor logs for errors

### 7.2 Initial Deployment Verification

**Checklist**:
- [ ] App URL is accessible
- [ ] Dashboard loads without errors
- [ ] Record counts are correct
- [ ] All navigation pages work
- [ ] Can perform CRUD operations
- [ ] Changes persist after manual app restart

**Test Operations**:
1. Create a new measure
2. Refresh the page
3. Verify the measure still exists
4. Update the measure
5. Delete the measure
6. Verify deletion persisted

### 7.3 Monitor MotherDuck Usage

**MotherDuck Dashboard**: https://app.motherduck.com/

**Metrics to monitor**:
- **Compute usage**: Track against 10 CU hours/month limit
- **Storage**: Should be ~21MB
- **Query performance**: Check slow queries
- **Connection status**: Ensure stable connections

**Set up alerts** (if available):
- 80% of compute quota used
- Unusual query patterns
- Connection failures

### 7.4 Monitor Streamlit Cloud Logs

**Access logs**:
1. Go to your app in Streamlit Cloud
2. Click menu (⋮) → "Logs"
3. Monitor for errors or warnings

**Common issues to watch for**:
- Connection timeout errors
- Token expiration warnings
- Memory usage warnings
- Slow query warnings

### 7.5 Performance Monitoring

**Metrics to track**:
- Page load time
- Query execution time
- User session duration
- Error rates

**Expected performance**:
- Initial load: < 5 seconds
- Page transitions: < 2 seconds
- Simple queries: < 500ms
- Complex queries: < 2 seconds

**If performance degrades**:
1. Check MotherDuck connection quality
2. Review query execution plans
3. Consider adding indexes
4. Optimize complex joins
5. Implement pagination for large datasets

---

## Testing Strategy

### Test Suite Structure

```
tests/
├── test_local_mode.py           # Local database connection tests
├── test_motherduck_mode.py      # MotherDuck connection tests
├── test_crud_operations.py      # CRUD operation tests
├── test_relationships.py        # Relationship management tests
├── test_error_handling.py       # Error handling tests
├── test_macros.py              # Macro functionality tests
└── validate_schema.py          # Schema validation script
```

### Test 1: Local Mode Connection

**File**: `test_local_mode.py`

**Purpose**: Verify application works in local mode

**Tests**:
```python
def test_local_connection():
    """Test connection to local database."""
    assert db.get_connection_info()['mode'] == 'local'
    assert db.test_connection() == True

def test_local_read_operations():
    """Test read operations in local mode."""
    # Test table access
    measures = db.get_table_count('measure')
    assert measures > 0

def test_local_write_operations():
    """Test write operations in local mode."""
    # Create a test record
    # Update the record
    # Delete the record
    # Verify all operations succeeded
```

### Test 2: MotherDuck Mode Connection

**File**: `test_motherduck_mode.py`

**Purpose**: Verify application works in MotherDuck mode

**Tests**:
```python
def test_motherduck_connection():
    """Test connection to MotherDuck."""
    assert db.get_connection_info()['mode'] == 'motherduck'
    assert db.test_connection() == True

def test_motherduck_read_operations():
    """Test read operations in MotherDuck mode."""
    measures = db.get_table_count('measure')
    assert measures > 0

def test_motherduck_write_operations():
    """Test write operations persist."""
    # Create a test record
    # Restart connection
    # Verify record still exists
```

### Test 3: CRUD Operations

**File**: `test_crud_operations.py`

**Purpose**: Verify all CRUD operations work correctly

**Test Cases**:
1. Create new measure
2. Read measure by ID
3. Update measure
4. Delete measure
5. Verify cascading deletes
6. Test bulk operations
7. Test transaction rollback

### Test 4: Schema Validation

**File**: `validate_schema.py`

**Purpose**: Ensure MotherDuck schema matches local

**Checks**:
```python
def validate_table_structure():
    """Verify all tables exist with correct columns."""
    expected_tables = [
        'measure', 'area', 'priority', 'species', 'grant_table',
        'measure_type', 'stakeholder', 'benefits', 'habitat',
        'measure_has_type', 'measure_has_stakeholder',
        'measure_area_priority', 'species_area_priority',
        'area_funding_schemes', 'measure_has_benefits',
        'measure_has_species', 'habitat_creation_area',
        'habitat_management_area', 'area_geom',
        'measure_area_priority_grant', 'source_table'
    ]
    # Verify each table exists

def validate_row_counts():
    """Verify row counts match between local and MotherDuck."""
    # Compare counts for each table

def validate_foreign_keys():
    """Verify all foreign key constraints exist."""
    # Query information_schema

def validate_views():
    """Verify all views exist and work."""
    # Test source_table_recreated_vw
    # Test apmg_slim_vw
```

### Test 5: Error Handling

**File**: `test_error_handling.py`

**Purpose**: Verify graceful error handling

**Test Cases**:
1. Invalid MotherDuck token
2. Network connection failure
3. Database not found
4. Table doesn't exist
5. Invalid SQL query
6. Constraint violation
7. Concurrent write conflicts

---

## Rollback Plan

If deployment fails or critical issues arise, follow this rollback procedure:

### Immediate Rollback Steps

1. **In Streamlit Cloud**:
   - Go to app settings
   - Change `DATABASE_MODE = "local"` in secrets
   - Note: This will only work if local database file is in repository (not recommended)

2. **Better Option - Maintenance Mode**:
   - Show maintenance page in app
   - Investigate issue offline
   - Fix and redeploy

### Rollback to Local Development

1. Set `.env` to local mode:
   ```bash
   echo 'DATABASE_MODE="local"' > .env
   ```

2. Verify local database is up to date

3. Test locally before redeploying

### Data Recovery

If MotherDuck data is corrupted or lost:

1. **Restore from local database**:
   ```bash
   duckdb
   ATTACH 'data/lnrs_3nf_o1.duckdb' AS lnrs;
   ATTACH 'md:' AS motherduck;
   .read lnrs_to_motherduck.sql
   ```

2. **Verify data integrity**:
   ```bash
   python validate_schema.py
   ```

---

## Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MotherDuck token exposed | Low | High | Store in secrets only, never commit |
| Token expires | Low | Medium | Monitor expiration, rotate tokens |
| Network connection issues | Medium | Medium | Implement retry logic, show user-friendly errors |
| Macros don't persist | Medium | Low | Recreate on each connection |
| Slower performance than local | High | Low | Optimize queries, add pagination |
| Free tier limits exceeded | Low | Medium | Monitor usage, plan upgrade path |
| Database corruption | Very Low | High | Regular backups, test restore procedures |
| Concurrent write conflicts | Low | Low | Use transactions, implement optimistic locking |
| Schema drift | Low | Medium | Version control, schema validation scripts |
| Deployment failure | Low | Medium | Test locally first, have rollback plan |

---

## Success Criteria

### Functional Requirements

- ✅ Application connects to MotherDuck successfully
- ✅ All CRUD operations work correctly
- ✅ Data persists across app restarts
- ✅ All UI pages function without errors
- ✅ Relationships can be created and managed
- ✅ Data export functionality works
- ✅ Macros function correctly

### Non-Functional Requirements

- ✅ Page load time < 5 seconds
- ✅ Query response time < 2 seconds for most operations
- ✅ No errors in Streamlit Cloud logs
- ✅ MotherDuck compute usage < 50% of free tier
- ✅ Application available 99%+ of the time
- ✅ Clear error messages for users
- ✅ Documentation complete and accurate

### Security Requirements

- ✅ MotherDuck token not exposed in code or logs
- ✅ Secrets properly configured in Streamlit Cloud
- ✅ No sensitive data in git repository
- ✅ Connection uses secure protocol
- ✅ Token has appropriate permissions (read/write)

---

## Post-Deployment Tasks

### Week 1

- [ ] Monitor MotherDuck usage daily
- [ ] Check Streamlit Cloud logs for errors
- [ ] Test all major user workflows
- [ ] Gather user feedback
- [ ] Document any issues encountered

### Week 2-4

- [ ] Analyze performance metrics
- [ ] Optimize slow queries if needed
- [ ] Review MotherDuck compute usage trends
- [ ] Plan for scaling if needed
- [ ] Update documentation based on learnings

### Ongoing

- [ ] Monthly review of MotherDuck usage
- [ ] Monitor for MotherDuck token expiration
- [ ] Keep dependencies updated
- [ ] Backup strategy review
- [ ] Performance optimization as needed

---

## Appendix A: Key File Changes Summary

### Files to Modify

1. **config/database.py** - Main refactoring
   - Add environment detection
   - Add connection factory
   - Support both local and MotherDuck

2. **pyproject.toml** - Add dependency
   - Add `python-dotenv>=1.0.0`

3. **.env** - Update configuration
   - Add `DATABASE_MODE="local"`

4. **.gitignore** - Security
   - Add `.env`, `.streamlit/secrets.toml`

### Files to Create

1. **requirements.txt** - For Streamlit Cloud
2. **.streamlit/secrets.toml.template** - Secrets template
3. **.streamlit/secrets.toml** - Local secrets (not committed)
4. **DEPLOYMENT.md** - Deployment guide
5. **SECRETS_TEMPLATE.md** - Secrets documentation
6. **validate_schema.py** - Schema validation script
7. **test_local_mode.py** - Local mode tests
8. **test_motherduck_mode.py** - MotherDuck tests
9. **test_crud_operations.py** - CRUD tests
10. **test_error_handling.py** - Error handling tests

### Files That Need NO Changes

- All files in `models/` - Use abstracted connection
- All files in `ui/pages/` - Use abstracted connection
- `app.py` - No changes needed

---

## Appendix B: MotherDuck Connection String Examples

### Basic Connection
```python
conn = duckdb.connect("md:")
# Connects to default database using stored token
```

### Specific Database
```python
conn = duckdb.connect("md:lnrs_weca")
# Connects to lnrs_weca database
```

### With Token
```python
conn = duckdb.connect("md:lnrs_weca?motherduck_token=YOUR_TOKEN")
# Explicit token in connection string
```

### Read-Only Connection
```python
conn = duckdb.connect("md:lnrs_weca?motherduck_token=YOUR_TOKEN&access_mode=read_only")
# Read-only access
```

---

## Appendix C: Troubleshooting Guide

### Issue: "Cannot connect to MotherDuck"

**Symptoms**: App fails to start, connection error in logs

**Solutions**:
1. Verify token is correct in secrets
2. Check database name spelling (`lnrs_weca`)
3. Verify token has not expired
4. Check MotherDuck service status
5. Test connection locally first

### Issue: "Macro 'max_meas' does not exist"

**Symptoms**: Error when creating new measures

**Solutions**:
1. Verify `_load_macros()` is being called
2. Check if macro creation SQL is correct
3. Test macro creation manually in MotherDuck UI
4. Consider creating macro as a regular function if persistence is an issue

### Issue: "Performance is very slow"

**Symptoms**: Queries take > 5 seconds, pages timeout

**Solutions**:
1. Check MotherDuck connection quality
2. Review query execution plans
3. Add indexes to frequently queried columns
4. Implement pagination for large result sets
5. Cache frequently accessed data
6. Consider upgrading MotherDuck tier if needed

### Issue: "Data is not persisting"

**Symptoms**: Changes are lost after restart

**Solutions**:
1. Verify `DATABASE_MODE = "motherduck"` in secrets
2. Check that writes are completing (no errors)
3. Verify not accidentally in local mode
4. Check MotherDuck web UI to see if data is there
5. Review transaction handling

### Issue: "Out of compute credits"

**Symptoms**: Queries fail with quota exceeded error

**Solutions**:
1. Review compute usage in MotherDuck dashboard
2. Optimize expensive queries
3. Reduce query frequency
4. Consider upgrading to paid tier
5. Implement caching strategy

---

## Appendix D: Environment Variables Reference

### Local Development (.env file)

```bash
# Database mode: "local" or "motherduck"
DATABASE_MODE="local"

# MotherDuck configuration (used when DATABASE_MODE="motherduck")
motherduck_token="YOUR_MOTHERDUCK_TOKEN"
database_name="lnrs_weca"
```

### Streamlit Cloud (secrets.toml)

```toml
# Database mode
DATABASE_MODE = "motherduck"

# Database name
database_name = "lnrs_weca"

# MotherDuck token
motherduck_token = "YOUR_MOTHERDUCK_TOKEN"
```

### Auto-detected Environment Variables

- `STREAMLIT_SHARING_MODE` - Set by Streamlit Cloud, triggers auto-detection

---

## Contact & Support

### MotherDuck Support
- Documentation: https://motherduck.com/docs
- Support: https://motherduck.com/support
- Status: https://status.motherduck.com

### Streamlit Support
- Documentation: https://docs.streamlit.io
- Community Forum: https://discuss.streamlit.io
- Status: https://status.streamlit.io

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-04 | Initial | Initial implementation plan |

---

*End of Implementation Plan*
