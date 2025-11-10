# Database Operations Guide

## Database Schema Overview

### Database Type
- **DuckDB**: Embedded analytical database
- **File**: `data/lnrs_3nf_o1.duckdb` (33MB)
- **Schema**: Third Normal Form (3NF)
- **Tables**: 20+ tables with complex relationships

### Key Characteristics
- In-process SQL OLAP database
- Fast analytical queries
- Column-oriented storage
- Full SQL support
- Excellent Pandas/Polars integration

## Core Tables

### Main Entity Tables

1. **measure** (780+ records)
   - Primary Key: `measure_id`
   - Biodiversity actions and recommendations
   - Fields: title, summary, detail, responsibility, image_url

2. **area** (50 records)
   - Primary Key: `area_id`
   - Priority areas for biodiversity
   - Linked to 694 polygon geometries in `area_geom`

3. **priority** (33 records)
   - Primary Key: `priority_id`
   - Biodiversity priorities grouped by themes
   - Fields: priority, theme, priority_detail

4. **species** (39 records)
   - Primary Key: `species_id`
   - Species of importance with GBIF taxonomy
   - Fields: common_name, taxon_name, taxon_key, image_url

5. **grant_table** (multiple records)
   - Primary Key: `grant_id`
   - Financial incentives and grants
   - Fields: grant_name, grant_detail, grant_url, target

6. **habitat** (multiple records)
   - Primary Key: `habitat_id`
   - Habitat types for creation and management
   - Fields: habitat_name, habitat_type

7. **benefits** (multiple records)
   - Primary Key: `benefit_id`
   - Benefits delivered by measures

## Bridge/Junction Tables

These implement many-to-many relationships:

1. **measure_area_priority**
   - Core relationship: measures ↔ areas ↔ priorities
   - Composite key: (measure_id, area_id, priority_id)

2. **measure_area_priority_grant**
   - Links grants to measure-area-priority combinations
   - Fields: measure_id, area_id, priority_id, grant_id

3. **measure_has_type**
   - Links measures to measure types
   - Fields: measure_id, measure_type_id

4. **measure_has_stakeholder**
   - Links measures to stakeholders
   - Fields: measure_id, stakeholder_id

5. **species_area_priority**
   - Links species to areas and priorities
   - Fields: species_id, area_id, priority_id

6. **measure_has_benefits**
   - Links measures to benefits
   - Fields: measure_id, benefit_id

7. **measure_has_species**
   - Links measures to species
   - Fields: measure_id, species_id

8. **habitat_creation_area**
   - Links habitats to areas for creation
   - Fields: habitat_id, area_id

9. **habitat_management_area**
   - Links habitats to areas for management
   - Fields: habitat_id, area_id

## Important Views

### source_table_recreated_vw
- Recreates original denormalized source data
- Joins all tables together
- Should match original source_table row count

### apmg_slim_vw
- Slimmed down view for app usage
- Contains key fields from multiple tables
- Used for displaying related data

## CRUD Operations

### Create Operations

#### Using Macros for ID Generation
```sql
-- Macro definition (already in schema)
CREATE MACRO max_meas() AS (SELECT MAX(measure_id) + 1 FROM measure);

-- Insert using macro
INSERT INTO measure (measure_id, title, summary, detail, responsibility, image_url)
VALUES (max_meas(), 'New Measure', 'Summary', 'Detail', 'Responsibility', 'url');
```

#### Using Sequences
```sql
-- For measure_type
INSERT INTO measure_type (measure_type_id, measure_type)
VALUES (nextval('seq_measure_type_id'), 'New Type');

-- For stakeholder
INSERT INTO stakeholder (stakeholder_id, stakeholder)
VALUES (nextval('seq_stakeholder_id'), 'New Stakeholder');
```

### Read Operations

#### Using DuckDB Relational API (Preferred)
```python
# Get entire table as relation
conn = db.get_connection()
measures_rel = conn.table('measure')

# Filter
filtered = measures_rel.filter('measure_id = 1')

# Convert to DataFrame
df = measures_rel.df()

# Convert to Polars
pl_df = measures_rel.pl()
```

#### Using Raw SQL
```python
result = db.execute_query("SELECT * FROM measure WHERE measure_id = ?", [1])
```

### Update Operations

```sql
UPDATE measure
SET title = 'Updated Title',
    summary = 'Updated Summary'
WHERE measure_id = 123;
```

### Delete Operations - CRITICAL

**MUST follow cascading delete order** to respect foreign keys.

#### Delete a Measure (7 steps)
```sql
-- 1. Delete measure types
DELETE FROM measure_has_type WHERE measure_id = ?;

-- 2. Delete stakeholders
DELETE FROM measure_has_stakeholder WHERE measure_id = ?;

-- 3. Delete grants
DELETE FROM measure_area_priority_grant WHERE measure_id = ?;

-- 4. Delete area-priority relationships
DELETE FROM measure_area_priority WHERE measure_id = ?;

-- 5. Delete benefits
DELETE FROM measure_has_benefits WHERE measure_id = ?;

-- 6. Delete species
DELETE FROM measure_has_species WHERE measure_id = ?;

-- 7. Finally delete measure
DELETE FROM measure WHERE measure_id = ?;
```

#### Delete a Priority (3 steps)
```sql
-- 1. Delete grants
DELETE FROM measure_area_priority_grant WHERE priority_id = ?;

-- 2. Delete measure relationships
DELETE FROM measure_area_priority WHERE priority_id = ?;

-- 3. Delete species relationships
DELETE FROM species_area_priority WHERE priority_id = ?;

-- 4. Finally delete priority
DELETE FROM priority WHERE priority_id = ?;
```

#### Delete an Area (6 steps)
```sql
-- 1. Delete grants
DELETE FROM measure_area_priority_grant WHERE area_id = ?;

-- 2. Delete measure relationships
DELETE FROM measure_area_priority WHERE area_id = ?;

-- 3. Delete species relationships
DELETE FROM species_area_priority WHERE area_id = ?;

-- 4. Delete funding schemes
DELETE FROM area_funding_schemes WHERE area_id = ?;

-- 5. Delete habitat creation
DELETE FROM habitat_creation_area WHERE area_id = ?;

-- 6. Delete habitat management
DELETE FROM habitat_management_area WHERE area_id = ?;

-- 7. Finally delete area
DELETE FROM area WHERE area_id = ?;
```

## Transaction Management

Always use transactions for multi-step operations:

```python
try:
    conn.execute("BEGIN TRANSACTION")
    
    # Execute multiple related queries
    conn.execute("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id])
    conn.execute("DELETE FROM measure WHERE measure_id = ?", [measure_id])
    
    conn.execute("COMMIT")
except Exception as e:
    conn.execute("ROLLBACK")
    raise e
```

## Common Queries

### Get Measure with All Related Data
```sql
SELECT 
    m.measure_id,
    m.title,
    m.summary,
    a.area_name,
    p.priority,
    g.grant_name
FROM measure m
LEFT JOIN measure_area_priority map ON m.measure_id = map.measure_id
LEFT JOIN area a ON map.area_id = a.area_id
LEFT JOIN priority p ON map.priority_id = p.priority_id
LEFT JOIN measure_area_priority_grant mapg ON map.measure_id = mapg.measure_id
LEFT JOIN grant_table g ON mapg.grant_id = g.grant_id
WHERE m.measure_id = ?;
```

### Count Measures by Area
```sql
SELECT 
    a.area_name,
    COUNT(DISTINCT m.measure_id) as measure_count
FROM area a
LEFT JOIN measure_area_priority map ON a.area_id = map.area_id
LEFT JOIN measure m ON map.measure_id = m.measure_id
GROUP BY a.area_name
ORDER BY measure_count DESC;
```

### Get Species for an Area
```sql
SELECT 
    s.common_name,
    s.taxon_name,
    p.priority
FROM species s
JOIN species_area_priority sap ON s.species_id = sap.species_id
JOIN area a ON sap.area_id = a.area_id
JOIN priority p ON sap.priority_id = p.priority_id
WHERE a.area_id = ?;
```

## Performance Considerations

### Indexing
- Primary keys are automatically indexed
- Foreign keys should be indexed for joins
- DuckDB handles this automatically for small datasets

### Query Optimization
- Use the relational API for filtering (pushes down to database)
- Avoid `SELECT *` in production queries
- Use EXPLAIN to analyze query plans

### Memory Management
- DuckDB loads data on-demand
- Connection pooling via singleton pattern
- Close connections when done (but reuse singleton)

## Data Validation Rules

1. **Grant URLs**: Must be valid URLs
2. **Foreign Keys**: Must reference existing records
3. **Required Fields**: Cannot be NULL where specified
4. **Unique Constraints**: Where defined in schema

## Export/Import

### Export to CSV
```sql
COPY (SELECT * FROM measure) TO 'export.csv' WITH (HEADER, DELIMITER ',');
```

### Import from CSV
```sql
COPY measure FROM 'import.csv' WITH (HEADER, DELIMITER ';');
```

Note: Source CSV files use `;` delimiter, not `,`.

## Backup and Restore

### Backup
```bash
cp data/lnrs_3nf_o1.duckdb data/lnrs_3nf_o1_backup_$(date +%Y%m%d).duckdb
```

### Restore
```bash
cp data/lnrs_3nf_o1_backup_20241110.duckdb data/lnrs_3nf_o1.duckdb
```

### Schema Export
```sql
-- In DuckDB CLI
.schema > schema_export.sql
```
