# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based CRUD application for managing the LNRS (Local Nature Recovery Strategy) database. The database is stored in DuckDB and follows a normalized (3NF) schema with 20+ tables tracking biodiversity measures, areas, priorities, species, habitats, and grants.

## Key Technologies

- **Database**: DuckDB (`data/lnrs_3nf_o1.duckdb`)
- **Web Framework**: Streamlit
- **Data Manipulation**: DuckDB's relational Python API and Polars
- **Python Version**: >=3.13
- **Package Manager**: uv (evident from `uv.lock`)

## Database Architecture

The database uses a normalized 3NF schema with the following core structure:

### Core Tables
- **measure**: Actions/recommendations for biodiversity (780+ records)
- **area**: Priority areas for biodiversity (50 areas, mapped to 694 polygons)
- **priority**: 33 biodiversity priorities grouped by themes
- **species**: 39 species of importance with GBIF data
- **grant_table**: Financial incentives/grants for landowners
- **habitat**: Habitat types for creation and management
- **benefits**: Benefits delivered by measures

### Bridge Tables (Many-to-Many Relationships)
- **measure_has_type**: Links measures to measure types
- **measure_has_stakeholder**: Links measures to stakeholders
- **measure_area_priority**: Core relationship between measures, areas, and priorities
- **measure_area_priority_grant**: Links grants to measure-area-priority combinations
- **species_area_priority**: Links species to areas and priorities
- **measure_has_benefits**: Links measures to benefits
- **measure_has_species**: Links measures to species
- **habitat_creation_area**: Links habitats to areas for creation
- **habitat_management_area**: Links habitats to areas for management

### Important Views
- **source_table_recreated_vw**: Recreates the original denormalized data by joining all tables
- **apmg_slim_vw**: Slimmed down view for the app with key fields only

## Development Commands

### Setup and Installation
```bash
# Install dependencies using uv
uv sync

# Or using pip
pip install -r pyproject.toml
```

### Running the Application
```bash
# Run the Streamlit app (command TBD - check for main app file)
streamlit run app.py  # or main.py, check actual filename
```

### Database Operations

The database is managed through DuckDB CLI or Python API. Schema is defined in `lnrs_3nf_o1.sql`. For additional context, the schema is also represented in the `lnrs_3nf_o1_schema.xml` file.

To recreate the database:
```bash
# Remove existing database
rm data/lnrs_3nf_o1.duckdb

# Run DuckDB CLI
./duckdb data/lnrs_3nf_o1.duckdb

# Execute schema file
.read lnrs_3nf_o1.sql
```

## CRUD Operations - Critical Constraints

**IMPORTANT**: All delete operations must respect foreign key constraints and cascade properly. The database has complex many-to-many relationships that require careful handling.

### Deleting Records - Required Cascade Order

When deleting from core tables, you MUST delete from dependent tables first:

**Delete a Measure:**
1. Delete from `measure_has_type` where `measure_id` matches
2. Delete from `measure_has_stakeholder` where `measure_id` matches
3. Delete from `measure_area_priority_grant` where `measure_id` matches
4. Delete from `measure_area_priority` where `measure_id` matches
5. Delete from `measure_has_benefits` where `measure_id` matches
6. Delete from `measure_has_species` where `measure_id` matches
7. Finally delete from `measure`

**Delete a Priority:**
1. Delete from `measure_area_priority_grant` where `priority_id` matches
2. Delete from `measure_area_priority` where `priority_id` matches
3. Delete from `species_area_priority` where `priority_id` matches
4. Finally delete from `priority`

**Delete an Area:**
1. Delete from `measure_area_priority_grant` where `area_id` matches
2. Delete from `measure_area_priority` where `area_id` matches
3. Delete from `species_area_priority` where `area_id` matches
4. Delete from `area_funding_schemes` where `area_id` matches
5. Delete from `habitat_creation_area` where `area_id` matches
6. Delete from `habitat_management_area` where `area_id` matches
7. Finally delete from `area`

### Creating New Records

When creating measures, use the `max_meas()` macro pattern to generate new IDs:
```sql
CREATE MACRO max_meas() AS (SELECT MAX(measure_id) + 1 FROM measure);
INSERT INTO measure (measure_id, ...) VALUES (max_meas(), ...);
```

For `measure_type` and `stakeholder` tables, use sequences:
- `seq_measure_type_id`
- `seq_stakeholder_id`

## Data Files Location

Source data files are expected in `data/` directory:
- CSV files use `;` as delimiter (not `,`)
- Main database: `data/lnrs_3nf_o1.duckdb`
- Schema: `lnrs_3nf_o1.sql` (root directory)
- Geospatial data: `data/lnrs-sub-areas.parquet`

## Important Constraints

1. **Use DuckDB's relational Python API wherever possible** for data manipulation
2. **Use SQL only for complex operations**
3. **Ensure all operations respect CASCADING deletes** as shown above
4. **The app must be responsive** and work on different screen sizes
5. **Include error handling** for all database operations
6. **Grant records without valid URLs should not be added** to the database

## Schema Notes

- `grant_table` is used instead of `grants` (reserved keyword)
- `area_geom` contains 694 polygon geometries linked to 50 areas via `area_id`
- Species data includes GBIF taxonomy and image URLs
- The view `source_table_recreated_vw` should have the same row count as the original `source_table`

## Python Rules
This rule applies to all Python files in the project.

### File Pattern
*.py

### Description
When working with Python files, we use uv as our package manager and runtime. Python files should be executed using the command `uv run {file}`.

### Formatting
- Use 4 spaces for indentation
- Follow PEP 8 style guide
- Use Ruff for code formatting and linting
- Format on save

### Best Practices
- Use type hints where appropriate
- Include docstrings for functions and classes
- Use virtual environments with uv for dependency management
- Use ipykernel code fences like `#%%` for interactive development and testing

## SQL Rules
This rule applies to all SQL files in the project.
### File Pattern
*.sql

### Description
When working with SQL files, we use DuckDB as our database engine. SQL files should be executed using the command `duckdb local.db -f {file}`.

### Formatting
- Use 4 spaces for indentation
- Use SQLFluff for formatting with DuckDB dialect
- Format on save

## Commands
- Run SQL file: duckdb local.db -f {file}

## Best Practices
- Use consistent naming conventions
- Include comments for complex queries
- Use proper indentation for readability
- Follow DuckDB's SQL dialect specifications