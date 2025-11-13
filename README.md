# LNRS Database Management Application 🌿

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.41+-FF4B4B.svg)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/duckdb-1.1+-yellow.svg)](https://duckdb.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive CRUD application for managing Local Nature Recovery Strategy (LNRS) biodiversity data with advanced transaction management, automatic backup capabilities, and dual-mode deployment (local/cloud).

## Table of Contents

- [About LNRS](#about-lnrs)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Application Structure](#application-structure)
- [Database Architecture](#database-architecture)
- [Core Features](#core-features)
- [Transaction & Backup System](#transaction--backup-system)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## About LNRS

The **Local Nature Recovery Strategy (LNRS)** is a system for spatial planning to deliver environmental improvements across England. This application provides a comprehensive data management solution for tracking biodiversity measures, priority areas, species, habitats, and funding opportunities.

### Project Purpose

This application enables the LNRS manager to:
- CREATE, READ, UPDATE, and DELETE (CRUD) biodiversity measures and related entities
- Export data for analysis and reporting
- Maintain data integrity with automatic backups and point-in-time recovery


---

## Key Features

### 🗄️ Data Management
- **Full CRUD Operations** for all entity types (measures, areas, priorities, species, habitats, grants)
- **Complex Relationship Management** with many-to-many relationships between entities
- **Cascade Delete Protection** with automatic snapshot creation before destructive operations
- **Atomic Updates** with transaction support for data integrity

### 💾 Backup & Recovery
- **Automatic Snapshots** created before all delete operations
- **Manual Backup Creation** with descriptive notes
- **Point-in-Time Recovery** with snapshot preview functionality
- **Safety Backups** automatically created before restore operations
- **Retention Policies** with automatic cleanup of old snapshots

### 📊 Data Export
- **CSV Export** for all entity types and relationships
- **Customizable Exports** with filtering and selection options
- **Bulk Export** capabilities for comprehensive data extraction
- **update the [LNRS Toolkit](https://opendata.westofengland-ca.gov.uk/pages/lnrs-application/?headless=true)**

### 🔍 Performance & Monitoring
- **Performance Tracking** with automatic slow operation detection (>5 seconds)
- **Comprehensive Logging** with separate log files for transactions, backups, and performance
- **Operation Audit Trail** with detailed logging of all database operations

### 🌐 Dual-Mode Deployment
- **Local Development Mode** with DuckDB file-based database and full backup functionality
- **Cloud Production Mode** with MotherDuck cloud database (backup UI gracefully disabled)
- **Automatic Environment Detection** and configuration

### 🎨 User Experience
- **Responsive Design** works on all screen sizes
- **Intuitive Navigation** with organized entity and relationship sections
- **Real-time Feedback** with success/error messages and restore hints
- **Dashboard View** with database statistics and recent activity

---

## Technology Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core language | 3.13+ |
| **Streamlit** | Web framework for UI | 1.41+ |
| **DuckDB** | Local database engine | 1.4+ |
| **MotherDuck** | Cloud database (production) | Latest |
| **Polars** | Data manipulation | Latest |
| **uv** | Package manager | Latest |
| **pytest** | Testing framework | 8.4+ |

### Architecture

- **Database**: DuckDB (local) / MotherDuck (cloud) - Columnar, OLAP database with full SQL support
- **ORM Layer**: Custom models with DuckDB's relational Python API
- **UI Framework**: Streamlit multipage application
- **State Management**: Streamlit session state
- **Deployment**: Streamlit Community Cloud (free tier)

---

## Prerequisites

### For Local Development

- **Python 3.13 or higher**
- **uv package manager** (recommended) or pip
- **Git** for version control
- **Database file**: `data/lnrs_3nf_o1.duckdb` (should be included in repository or created from schema)

### For Cloud Deployment

- **MotherDuck Account** (free tier available at https://app.motherduck.com/)
- **Streamlit Community Cloud Account** (free at https://share.streamlit.io/)
- **GitHub Repository** (https://github.com/stevecrawshaw/lnrs-db-app)

---

## Installation & Setup

### Quick Start (Local Development)

```bash
# Clone the repository
git clone <repository-url>
cd lnrs-db-app

# Install dependencies
uv sync

# Create environment file
echo "DATABASE_MODE=local" > .env

# Verify database file exists
ls -lh data/lnrs_3nf_o1.duckdb

# Run the application
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Detailed Setup

#### 1. Clone Repository

```bash
git clone <repository-url>
cd lnrs-db-app
```

#### 2. Install Dependencies

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment

Create a `.env` file in the root directory:

```bash
# For local development
DATABASE_MODE=local
```

**OR** for MotherDuck cloud database:

```bash
DATABASE_MODE=motherduck
database_name=lnrs_weca
motherduck_token=YOUR_MOTHERDUCK_TOKEN_HERE
```

#### 4. Database Setup

**Option A: Use Existing Database**

Ensure the database file exists at `data/lnrs_3nf_o1.duckdb`

**Option B: Create Database from Schema**

```bash
# Create database from SQL schema
duckdb data/lnrs_3nf_o1.duckdb < lnrs_3nf_o1.sql

# Load data from CSV files (if available)
# CSV files should be in data/ directory with semicolon delimiters
```

#### 5. Verify Installation

```bash
# Run application
streamlit run app.py

# Run tests
uv run pytest tests/ -v
```

---

## Running the Application

### Local Development Mode

```bash
# Set environment
echo "DATABASE_MODE=local" > .env

# Run application
streamlit run app.py
```

Features available in local mode:
- ✅ Full CRUD operations
- ✅ Automatic backup creation
- ✅ Manual backup and restore
- ✅ Snapshot preview
- ✅ All functionality enabled

### Cloud/MotherDuck Mode

```bash
# Configure environment
cat > .env << EOF
DATABASE_MODE=motherduck
database_name=lnrs_weca
motherduck_token=YOUR_TOKEN_HERE
EOF

# Run application
streamlit run app.py
```

Features in cloud mode:
- ✅ Full CRUD operations
- ✅ Cloud database persistence
- ✅ Multi-user access
- ⚠️ Backup UI shows informational message (ephemeral filesystem)
- ✅ MotherDuck provides infrastructure reliability

### Command Line Options

```bash
# Run on different port
streamlit run app.py --server.port 8502

# Run with specific config
streamlit run app.py --server.headless true

# View help
streamlit run app.py --help
```

---

## Application Structure

### Navigation

The application is organized into logical sections:

```
📁 LNRS Database Manager
├── 🏠 Main
│   └── Dashboard (Overview, statistics, recent activity)
├── 📋 Entities
│   ├── Measures (Biodiversity measures and actions)
│   ├── Areas (Priority areas for conservation)
│   ├── Priorities (Biodiversity priorities by theme)
│   ├── Species (Species of importance with GBIF data)
│   ├── Grants (Funding opportunities for landowners)
│   └── Habitats (Habitat types for creation/management)
├── 🔗 Relationships
│   └── Manage many-to-many relationships between entities
├── 📊 Export
│   └── Data Export (CSV export for all entities and relationships)
└── 💾 Backup
    └── Backup & Restore (Snapshot management and recovery)
```

### Page Descriptions

| Page | Purpose | Key Features |
|------|---------|--------------|
| **Dashboard** | Overview and statistics | Entity counts, recent activity, system status |
| **Measures** | Biodiversity actions | CRUD operations, relationship links, cascade delete |
| **Areas** | Priority areas | Geographic data, funding schemes, linked measures |
| **Priorities** | Conservation priorities | Theme grouping, area/measure associations |
| **Species** | Important species | GBIF integration, images, habitat preferences |
| **Grants** | Funding opportunities | Grant details, eligibility, linked measures |
| **Habitats** | Habitat management | Creation/management areas, linked measures |
| **Relationships** | Entity linking | Bulk operations, link management |
| **Data Export** | CSV export | Customizable exports, filtering, bulk download |
| **Backup & Restore** | Data recovery | Snapshot list, manual backup, restore with preview |

---

## Database Architecture

### Schema Overview

The database follows a **normalized 3NF (Third Normal Form)** design with 20+ tables:

#### Core Tables (Entities)

| Table | Records | Description |
|-------|---------|-------------|
| **measure** | 780+ | Biodiversity measures and recommendations |
| **area** | 50 | Priority areas (linked to 694 polygons) |
| **priority** | 33 | Biodiversity priorities grouped by themes |
| **species** | 39 | Species of importance with GBIF data |
| **grant_table** | Variable | Financial incentives and grants |
| **habitat** | Variable | Habitat types for creation and management |
| **benefits** | Variable | Benefits delivered by measures |

#### Bridge Tables (Many-to-Many Relationships)

- `measure_has_type` - Measure classification
- `measure_has_stakeholder` - Stakeholder responsibilities
- `measure_area_priority` - Core three-way relationship
- `measure_area_priority_grant` - Grant associations
- `species_area_priority` - Species conservation priorities
- `measure_has_benefits` - Benefit associations
- `measure_has_species` - Species-measure links
- `habitat_creation_area` - Habitat creation locations
- `habitat_management_area` - Habitat management locations

#### Important Views

- **source_table_recreated_vw** - Denormalized view recreating original source data
- **apmg_slim_vw** - Streamlined view for LNRS Toolkit with essential fields

### Data Integrity

- **Foreign Key Constraints** enforced on all relationships
- **Cascade Delete Handling** with sequential deletion pattern (DuckDB limitation)
- **Atomic Updates** using transactions for relationship modifications
- **Unique Constraints** on entity IDs and key fields

---

## Core Features

### CRUD Operations

#### Creating Records

1. Navigate to entity page (e.g., Measures)
2. Click "Create New" button
3. Fill in required fields
4. Optionally add relationships (types, stakeholders, etc.)
5. Click "Create" - operation is validated before execution

#### Reading/Viewing Records

- **List View**: Paginated table with sorting and filtering
- **Detail View**: Full record with all related entities
- **Search**: Full-text search across key fields
- **Statistics**: Aggregate counts and summaries

#### Updating Records

1. Select record from list view
2. Click "Edit" button
3. Modify fields as needed
4. Update relationships (additions/removals are atomic)
5. Click "Update" - changes are transactional

**Atomicity**: Updates with relationships are fully atomic - either all changes succeed or none do.

#### Deleting Records

1. Select record from list view
2. Click "Delete" button
3. Review cascade warning showing affected relationships
4. Confirm deletion
5. Automatic snapshot created before deletion
6. Restore hint displayed with link to Backup page

**Safety**: All deletes create automatic snapshots for recovery.

### Relationship Management

The Relationships page provides tools for managing many-to-many relationships:

- **Bulk Link Creation**: Link multiple entities in one operation
- **Link Deletion**: Remove relationships with cascade handling
- **Relationship Browser**: View all connections between entities
- **Validation**: Prevents duplicate links and orphaned records

### Data Export

Export data to CSV format for analysis and reporting:

1. Navigate to Data Export page
2. Select entity type (measures, areas, priorities, etc.)
3. Choose export options (all records or filtered)
4. Click "Export to CSV"
5. Download file automatically

**Export Options**:
- Individual entity tables
- Relationship bridge tables
- Denormalized views (all data joined)
- Filtered subsets

---

## Transaction & Backup System

### Automatic Snapshots

**All destructive operations automatically create database snapshots:**

```python
# Snapshots created before:
- Delete operations (measures, areas, priorities, species, habitats, grants)
- Bulk delete operations
- Relationship deletions (with cascade)

# NOT created for:
- Read operations
- Update operations (use transactions instead)
- Create operations
```

**Snapshot Naming**: `YYYYMMDD_HHMMSS_operation_entity_id`

**Storage**: `data/backups/*.duckdb` (local mode only)

### Manual Backup

Create manual backups for scheduled archival or before major changes:

1. Navigate to Backup & Restore page
2. Click "Create Backup" tab
3. Enter descriptive note (e.g., "Before bulk measure update")
4. Click "Create Snapshot"
5. Snapshot saved with metadata in `snapshot_metadata.json`

### Restore Process

Restore database to a previous state:

1. Navigate to Backup & Restore page → Snapshots tab
2. Filter snapshots by operation type or entity (optional)
3. Click "Preview" to view snapshot contents (read-only)
4. Click "Restore" button
5. Review warnings (all changes since snapshot will be lost)
6. Type "RESTORE" to confirm
7. System creates safety backup automatically
8. Database restored and verified

**Safety Features**:
- Safety backup created before restore
- Database integrity check after restore
- Confirmation required (type "RESTORE")
- Preview functionality to verify contents

### Snapshot Management

**Automatic Cleanup**:
- Default retention: 10 most recent snapshots
- Configurable via Settings tab
- Oldest snapshots deleted automatically

**Manual Cleanup**:
1. Navigate to Backup & Restore → Settings tab
2. Set retention count (5-200)
3. Click "Clean Up"
4. Old snapshots deleted, keeping most recent

**Disk Space**: Each snapshot is ~32MB (varies with database size)

### DuckDB Transaction Limitations

⚠️ **Important Technical Note**:

DuckDB enforces foreign key constraints immediately during transactions, which affects delete operations:

- **Sequential Deletes Required**: Parent record deletes cannot be atomic; child records must be deleted first
- **Updates ARE Atomic**: All update operations with relationships use transactions
- **No True CASCADE DELETE**: DuckDB's `ON DELETE CASCADE` is unreliable; manual cascade implemented

**Impact**:
- Delete operations execute in correct order but are not atomic
- Partial failures possible (rare) but safe - orphaned records can be cleaned up
- All steps logged for audit trail
- Snapshots provide recovery mechanism

**Read more**: See `docs/DUCKDB_FK_LIMITATION.md` for technical details

### Logging

**Three separate log files** track all operations:

```
logs/
├── transactions.log    # All database operations (detailed)
├── backups.log         # Snapshot create/restore/cleanup
└── performance.log     # Operation timing and slow warnings
```

**Log Rotation**: Logs grow indefinitely - implement rotation if needed

**Performance Monitoring**: Operations >5 seconds trigger warnings in performance.log

---

## Testing

### Test Suite

Comprehensive test coverage includes:

```bash
tests/
├── conftest.py                          # Pytest fixtures and test database setup
├── test_transactions.py                 # Transaction behavior and atomicity
├── test_backup_restore_integration.py   # Backup/restore workflows
├── test_end_to_end.py                   # Full lifecycle and time-travel
└── test_backups.py                      # Basic backup functionality
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_transactions.py -v

# Run with coverage
uv run pytest tests/ --cov=models --cov=config --cov-report=html

# Run specific test
uv run pytest tests/test_end_to_end.py::test_full_measure_lifecycle_with_backups -v
```

### Test Database Isolation

Tests use **monkeypatch** to redirect database connections to temporary test databases:
- Production database never modified during tests
- Each test gets fresh database copy
- Automatic cleanup after tests complete

### Continuous Integration

Tests run automatically on:
- Pull requests (via GitHub Actions - configure if needed)
- Pre-commit hooks (configure if needed)
- Local development (manual)

---

## Deployment

### Local Deployment

Already covered in [Running the Application](#running-the-application)

### Streamlit Community Cloud

**Step-by-Step Guide**: See `DEPLOYMENT.md` for complete instructions

**Quick Summary**:

1. **Prepare Repository**
   - Commit all code to GitHub
   - Ensure `.gitignore` excludes secrets
   - Verify `requirements.txt` or `pyproject.toml` is present

2. **Configure MotherDuck**
   - Create account at https://app.motherduck.com/
   - Create database `lnrs_weca`
   - Load data from local database or CSV
   - Generate API token

3. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select repository and branch
   - Set main file: `app.py`
   - Configure secrets:
     ```toml
     DATABASE_MODE = "motherduck"
     database_name = "lnrs_weca"
     motherduck_token = "YOUR_TOKEN_HERE"
     ```

4. **Verify Deployment**
   - Check app loads successfully
   - Verify database connection
   - Test CRUD operations
   - Confirm backup UI shows informational message

**Production Considerations**:
- Backup functionality disabled on Streamlit Cloud (ephemeral filesystem)
- MotherDuck provides cloud infrastructure reliability
- No local file storage available
- Multi-user access supported

---

## Documentation

### Complete Documentation Set

| Document | Description |
|----------|-------------|
| **README.md** | This file - overview and quick start |
| **CLAUDE.md** | Developer guide with architecture details |
| **DEPLOYMENT.md** | Step-by-step deployment instructions |
| **TRANSACTION_DEPLOYMENT_PLAN.md** | Complete transaction & backup system implementation |
| **docs/TROUBLESHOOTING.md** | Common issues and recovery procedures |
| **DUCKDB_FK_LIMITATION.md** | Technical details on transaction limitations |
| **FK_ANALYSIS.md** | Research findings on foreign key behavior |

### Key Documentation Sections

- **Database Schema**: See `lnrs_3nf_o1.sql` and `lnrs_3nf_o1_schema.xml`
- **API Reference**: Inline docstrings in `models/` and `config/`
- **Testing Guide**: See test files in `tests/` for examples
- **Deployment Guide**: `DEPLOYMENT.md`

---

## Troubleshooting

### Common Issues

#### Backup Functionality Disabled

**Symptom**: Backup page shows warning message

**Cause**: Running on Streamlit Cloud (ephemeral filesystem)

**Solution**: This is expected behavior. For production:
- MotherDuck provides cloud infrastructure reliability
- Manual backups not needed in cloud deployment
- For local development with backups, run with `DATABASE_MODE=local`

#### Transaction Failed Error

**Symptom**: "Transaction failed and rolled back" error

**Cause**: Foreign key constraint violation or invalid data

**Solution**:
1. Check error message for specific constraint
2. Review `logs/transactions.log` for details
3. Verify data integrity before operation
4. For deletes, ensure no blocking relationships

#### Slow Operations

**Symptom**: Operations taking >5 seconds

**Cause**: Large dataset, many relationships, or disk I/O

**Solution**:
1. Check `logs/performance.log` for timing details
2. Run snapshot cleanup if >50 snapshots exist
3. Consider archiving old snapshots
4. Monitor disk space and I/O

#### Database Locked

**Symptom**: "Database is locked" error

**Cause**: Multiple concurrent connections or file lock

**Solution**:
1. Close other database connections
2. Restart application
3. Check for zombie processes: `ps aux | grep duckdb`

**Complete Troubleshooting Guide**: See `docs/TROUBLESHOOTING.md`

---

## Contributing

### Development Workflow

1. **Fork Repository**
2. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Make Changes** with tests
4. **Run Tests**: `uv run pytest tests/ -v`
5. **Commit**: `git commit -m "Add feature: description"`
6. **Push**: `git push origin feature/your-feature-name`
7. **Create Pull Request**

### Code Standards

- **Python Style**: PEP 8, enforced with Ruff
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Include docstrings for all public functions/classes
- **Testing**: Add tests for new features
- **Formatting**: Run `ruff check` and `ruff format` before committing

### Testing Requirements

All contributions must include:
- Unit tests for new functionality
- Integration tests if modifying database operations
- Documentation updates (README, CLAUDE.md, etc.)
- No breaking changes to existing functionality

### Code Review Process

Pull requests require:
- All tests passing
- Code review approval
- Documentation updates
- No merge conflicts

---

## Project Status

**Current Version**: 3.0

**Completion Status**: All phases complete ✅

- ✅ Phase 1: Core Transaction Implementation
- ✅ Phase 2: Backup Infrastructure
- ✅ Phase 3: Restore UI
- ✅ Phase 4: Testing & Monitoring

**Production Ready**: Yes

**Active Development**: Maintenance mode

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

---

## Acknowledgments

- **DuckDB** - High-performance analytical database
- **MotherDuck** - Cloud-native DuckDB platform
- **Streamlit** - Rapid web application framework
- **Polars** - Fast DataFrame library
- **GBIF** - Global Biodiversity Information Facility

---

## Support

For issues, questions, or contributions:

1. **Check Documentation**: Review relevant documentation files
2. **Search Issues**: Check existing GitHub issues
3. **Create Issue**: Open new issue with detailed description
4. **Contact**: Reach out to project maintainers

---

## Quick Reference Card

### Essential Commands

```bash
# Install dependencies
uv sync

# Run application (local)
streamlit run app.py

# Run tests
uv run pytest tests/ -v

# Check code formatting
ruff check .
ruff format .

# Export data
# Use Data Export page in UI

# Create backup
# Use Backup & Restore page in UI

# View logs
tail -f logs/transactions.log
tail -f logs/backups.log
tail -f logs/performance.log
```

### Environment Variables

```bash
# Local development
DATABASE_MODE=local

# Cloud production
DATABASE_MODE=motherduck
database_name=lnrs_weca
motherduck_token=YOUR_TOKEN
```

### Key Directories

```
lnrs-db-app/
├── data/               # Database files and backups
├── logs/               # Application logs
├── models/             # Data models and business logic
├── ui/pages/           # Streamlit pages
├── config/             # Configuration and utilities
├── tests/              # Test suite
└── docs/               # Additional documentation
```

---

**Last Updated**: 2025-11-13

**Document Version**: 1.0

**Maintained By**: Project Team
