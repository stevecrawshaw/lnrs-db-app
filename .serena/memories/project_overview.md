# LNRS Database CRUD Application - Project Overview

## Project Purpose
This is a Streamlit-based CRUD (Create, Read, Update, Delete) application for managing the **LNRS (Local Nature Recovery Strategy)** database. The application enables comprehensive management of biodiversity measures, priority areas, species, habitats, grants, and their complex relationships.

## Core Functionality
- Create, read, update, and delete records across 20+ normalized database tables
- Manage biodiversity measures, priority areas, species, and habitats
- Handle complex many-to-many relationships through bridge tables
- Export data to CSV format
- Switch between local DuckDB and MotherDuck (cloud) database modes
- Respect cascading deletes across related tables

## Database Architecture
The database uses a **normalized 3NF schema** stored in DuckDB format:
- **Main Database**: `data/lnrs_3nf_o1.duckdb` (33MB)
- **Schema Definition**: `lnrs_3nf_o1.sql` (root directory)
- **Schema XML**: `lnrs_3nf_o1_schema.xml` (additional reference)

### Core Tables (20+ total)
- **measure**: 780+ biodiversity actions/recommendations
- **area**: 50 priority areas (mapped to 694 polygons)
- **priority**: 33 biodiversity priorities grouped by themes
- **species**: 39 species of importance with GBIF taxonomy data
- **grant_table**: Financial incentives/grants for landowners
- **habitat**: Habitat types for creation and management
- **benefits**: Benefits delivered by measures

### Bridge Tables (Many-to-Many)
- measure_has_type, measure_has_stakeholder
- measure_area_priority (core relationship)
- measure_area_priority_grant
- species_area_priority
- measure_has_benefits, measure_has_species
- habitat_creation_area, habitat_management_area

### Key Views
- **source_table_recreated_vw**: Denormalized view joining all tables
- **apmg_slim_vw**: Slimmed view for app with key fields only

## Tech Stack
- **Database**: DuckDB 1.4.1+
- **Web Framework**: Streamlit 1.50.0+
- **Data Manipulation**: DuckDB relational Python API, Polars 1.34.0+
- **Python Version**: >= 3.13
- **Package Manager**: uv (modern, fast Python package manager)
- **Other Dependencies**: pyarrow, python-dotenv, ipykernel

## Project Structure
```
lnrs-db-app/
├── app.py                  # Main Streamlit application entry point
├── models/                 # Data models (ORM-like classes)
│   ├── base.py            # BaseModel with CRUD operations
│   ├── measure.py, area.py, priority.py, species.py
│   ├── grant.py, habitat.py, relationship.py
├── ui/                    # User interface components
│   ├── pages/             # Streamlit pages (measures, areas, etc.)
│   └── components/        # Reusable UI components (database_selector, tables)
├── config/                # Configuration modules
│   └── database.py        # DatabaseConnection singleton (local/MotherDuck)
├── utils/                 # Utility functions
├── data/                  # Database files and CSV source data
├── tests/                 # Test scripts (in root, not tests/)
├── .streamlit/            # Streamlit configuration
└── Documentation files    # Multiple markdown implementation guides
```

## Data Files
- **Database**: `data/lnrs_3nf_o1.duckdb`
- **CSV files**: Use `;` delimiter (not `,`)
- **Geospatial data**: `data/lnrs-sub-areas.parquet`
- **Backup**: `data/lnrs_3nf_o1_clean_copy.duckdb`

## Key Features
1. **Dual Database Mode**: Switch between local DuckDB and MotherDuck cloud database
2. **Interactive Schema Visualization**: React-based ER diagram with zoom/pan controls and full-page view
3. **Responsive Design**: Works on different screen sizes
4. **Foreign Key Enforcement**: Respects cascading deletes
5. **Error Handling**: Comprehensive error handling for database operations
6. **Data Export**: Export data to CSV format
7. **URL Validation**: Ensures grant records have valid URLs
8. **Transaction Support**: Atomic update operations with comprehensive logging
9. **Backup & Restore**: Automatic snapshots before deletes, manual backup creation, point-in-time recovery
10. **Comprehensive Logging**: Step-by-step operation logging to `logs/transactions.log`, `logs/backups.log`, `logs/performance.log`

## Transaction Implementation Status (Phase 1)

**Current Status:** Phase 1 - Core Transaction Implementation in progress (Weeks 1-2)

**Completed:**
- ✅ Section 1.2: Relationship CRUD operations with transactions
- ✅ Section 1.3: Atomic measure updates with relationships
- ✅ Section 1.1: Cascade delete operations (sequential approach due to DuckDB FK limitation)

**Key Limitation:**
DuckDB checks foreign key constraints immediately after each statement, preventing atomic cascade deletes. All parent record deletions use sequential approach with comprehensive logging. Update operations remain fully atomic.

**Documentation:**
- `TRANSACTION_DEPLOYMENT_PLAN.md` - Full deployment plan (4 phases, 5 weeks)
- `DUCKDB_FK_LIMITATION.md` - Detailed FK constraint limitation analysis
- `TRANSACTIONS_1_3_TESTS.md` - Manual verification tests for section 1.3
- See memory: `transaction_implementation_status` for complete details
