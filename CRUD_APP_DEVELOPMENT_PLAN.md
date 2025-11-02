# LNRS Database CRUD Application - Development Plan

## Table of Contents
1. [Project Overview](#project-overview)
2. [MCP Server Integration](#mcp-server-integration)
3. [Database Architecture Analysis](#database-architecture-analysis)
4. [Technology Stack](#technology-stack)
5. [Application Architecture](#application-architecture)
6. [CRUD Operations Planning](#crud-operations-planning)
7. [UI/UX Design Approach](#uiux-design-approach)
8. [Data Validation and Error Handling](#data-validation-and-error-handling)
9. [Development Phases](#development-phases)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Considerations](#deployment-considerations)

---

## Project Overview

### Objectives
- Build a responsive Streamlit-based CRUD application for the LNRS (Local Nature Recovery Strategy) database
- Provide an intuitive interface for managing biodiversity measures, areas, priorities, species, habitats, and grants
- Ensure data integrity through proper cascade operations and foreign key constraint handling
- Enable non-technical users to perform database operations safely

### Key Challenges
- Complex many-to-many relationships requiring careful cascade delete operations
- 20+ interconnected tables with foreign key dependencies
- Maintaining referential integrity across bridge tables
- User-friendly interface for complex relational data operations

---

## MCP Server Integration

### Available MCP Servers

Three Model Context Protocol (MCP) servers are configured and connected for this project, providing enhanced development capabilities:

#### 1. **DuckDB MCP Server**
- **Purpose**: Direct database interaction through AI-assisted queries
- **Configuration**: `uvx mcp-server-duckdb --db-path ~/projects/lnrs-db-app/data/lnrs_3nf_o1.duckdb --keep-connection`
- **Key Features**:
  - Persistent connection maintains TEMP objects (macros like `max_meas()`)
  - SQL query execution and schema inspection
  - Data validation and integrity checking
  - Query optimization suggestions

**Development Use Cases**:
- Rapid prototyping of SQL queries during development
- Testing cascade delete operations before implementation
- Schema exploration and relationship validation
- Performance testing and query optimization

#### 2. **GitHub MCP Server**
- **Purpose**: Version control and collaboration
- **Configuration**: `npx -y @modelcontextprotocol/server-github`
- **Key Features**:
  - Repository management
  - Issue tracking
  - Pull request creation and review
  - Code search across GitHub

**Development Use Cases**:
- Automated commit and push operations
- Pull request creation with detailed descriptions
- Issue management for bug tracking and feature requests
- Documentation updates

#### 3. **Context7 MCP Server**
- **Purpose**: Up-to-date library documentation retrieval
- **Configuration**: `https://mcp.context7.com/mcp` (HTTP)
- **Key Features**:
  - Real-time documentation for Streamlit, DuckDB, Polars
  - Code examples and best practices
  - API reference lookup
  - Integration patterns

**Development Use Cases**:
- Quick reference for Streamlit components (forms, dataframes, multipage apps)
- DuckDB Python API patterns (relational API, transactions)
- Polars operations for data transformation
- Best practices and common patterns

### MCP-Enhanced Development Workflow

**Documentation-Driven Development**:
1. Use Context7 to retrieve latest API documentation for Streamlit, DuckDB, and Polars
2. Reference code examples from official docs during implementation
3. Stay updated with latest features (e.g., Streamlit 1.50+ dialog component)

**Database Development**:
1. Use DuckDB MCP server for schema exploration and query testing
2. Validate foreign key relationships before implementing CRUD operations
3. Test cascade delete sequences interactively
4. Optimize queries based on execution plans

**Version Control Integration**:
1. Use GitHub MCP for automated commits following best practices
2. Create pull requests with comprehensive descriptions
3. Track issues and feature requests
4. Maintain documentation in sync with code

### MCP Integration Benefits

- **Faster Development**: Direct access to documentation and database without context switching
- **Higher Code Quality**: Reference official examples and best practices in real-time
- **Better Testing**: Interactive database queries for validation
- **Improved Documentation**: Auto-generated commit messages and PR descriptions
- **Knowledge Retention**: Documentation insights integrated into development process

---

## Database Architecture Analysis

### Core Entity Tables (6)
1. **measure** - 780+ biodiversity actions/recommendations
2. **area** - 50 priority areas (linked to 694 polygons)
3. **priority** - 33 biodiversity priorities grouped by themes
4. **species** - 39 species with GBIF taxonomy data
5. **grant_table** - Financial incentives for landowners
6. **habitat** - Habitat types for creation and management

### Lookup/Bridge Tables (9)
1. **measure_has_type** - Measure to measure type mappings
2. **measure_has_stakeholder** - Measure to stakeholder mappings
3. **measure_area_priority** - Core relationship between measures, areas, and priorities
4. **measure_area_priority_grant** - Links grants to measure-area-priority combinations
5. **measure_has_benefits** - Measure to benefits mappings
6. **measure_has_species** - Measure to species mappings
7. **species_area_priority** - Species to area-priority mappings
8. **habitat_creation_area** - Habitat creation in areas
9. **habitat_management_area** - Habitat management in areas

### Supporting Tables (5)
1. **measure_type** - Types of measures (uses sequence: seq_measure_type_id)
2. **stakeholder** - Stakeholders (uses sequence: seq_stakeholder_id)
3. **benefits** - Benefits delivered by measures
4. **area_funding_schemes** - Local funding schemes per area
5. **area_geom** - Geospatial polygon data (694 records for 50 areas)

### Views
1. **source_table_recreated_vw** - Denormalized view recreating original data
2. **apmg_slim_vw** - Slim view with key fields for the app

### Critical Relationships
```
measure ──┬─── measure_has_type ──── measure_type
          ├─── measure_has_stakeholder ──── stakeholder
          ├─── measure_area_priority ──┬─── area
          │                            └─── priority
          ├─── measure_area_priority_grant ──── grant_table
          ├─── measure_has_benefits ──── benefits
          └─── measure_has_species ──── species

area ──┬─── measure_area_priority ──── priority
       ├─── species_area_priority ──── species
       ├─── area_funding_schemes
       ├─── habitat_creation_area ──── habitat
       └─── habitat_management_area ──── habitat

species ──┬─── species_area_priority ──┬─── area
          │                            └─── priority
          └─── measure_has_species ──── measure
```

---

## Technology Stack

### Core Technologies
- **Database**: DuckDB (local file-based, ACID compliant)
- **Web Framework**: Streamlit (v1.50.0+)
- **Data Manipulation**:
  - DuckDB relational Python API (primary)
  - Polars (for complex data transformations)
- **Python Version**: 3.13+
- **Package Manager**: uv
- **MCP Servers**: DuckDB, GitHub, Context7 (documentation and development assistance)

### Database Access Patterns

#### DuckDB Relational API (Primary Pattern)
Use DuckDB's relational API for clean, pythonic queries:

```python
import duckdb

# Connect to database
con = duckdb.connect('data/lnrs_3nf_o1.duckdb')

# Create a relation from a table
measures_rel = con.table("measure")

# Filter and project using relational API
filtered_measures = measures_rel.filter("core_supplementary = 'Core'").project("measure_id, measure, concise_measure")

# Get results as DataFrame
result_df = filtered_measures.df()

# Or convert to Polars for further manipulation
result_pl = filtered_measures.pl()
```

#### SQL for Complex Operations
Use raw SQL for complex joins, transactions, and cascade operations:

```python
# Transaction pattern for cascade deletes
con.begin()
try:
    # Cascade delete pattern
    con.execute("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure_has_stakeholder WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure_area_priority_grant WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure_area_priority WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure_has_benefits WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure_has_species WHERE measure_id = ?", [measure_id])
    con.execute("DELETE FROM measure WHERE measure_id = ?", [measure_id])
    con.commit()
except Exception as e:
    con.rollback()
    raise
```

#### Polars Integration
Use Polars for complex data transformations and SQL integration:

```python
import polars as pl

# Read data from DuckDB using Polars
query = "SELECT * FROM apmg_slim_vw"
df = pl.read_database(query, con)

# Or use Polars SQL context for multi-source queries
ctx = pl.SQLContext(
    measures=con.table("measure").pl(),
    areas=con.table("area").pl()
)

result = ctx.execute("""
    SELECT m.measure_id, m.measure, a.area_name
    FROM measures m
    JOIN areas a ON m.area_id = a.area_id
""").collect()
```

### Streamlit UI Patterns

#### Form Pattern with st.form
Batch user inputs to reduce reruns and improve performance:

```python
import streamlit as st

with st.form("measure_form"):
    st.subheader("Add New Measure")

    measure_text = st.text_area("Measure Description", max_chars=500)
    concise_measure = st.text_input("Concise Measure (Optional)")
    core_supp = st.selectbox("Core/Supplementary", ["Core", "Supplementary"])
    measure_types = st.multiselect("Measure Types", get_measure_types())
    stakeholders = st.multiselect("Stakeholders", get_stakeholders())

    submitted = st.form_submit_button("Create Measure")

    if submitted:
        # Process form data
        create_measure(measure_text, concise_measure, core_supp, measure_types, stakeholders)
        st.success("Measure created successfully!")
```

#### Interactive DataFrame Display
Use st.dataframe with column configuration and selection:

```python
import streamlit as st
import pandas as pd

# Display data with interactive features
df = get_measures_dataframe()

# Configure columns for better display
st.dataframe(
    df,
    use_container_width=True,
    hide_index=False,
    column_config={
        "measure_id": st.column_config.NumberColumn("ID", width="small"),
        "measure": st.column_config.TextColumn("Measure", width="large"),
        "link_to_further_guidance": st.column_config.LinkColumn("Guidance", width="medium"),
    },
    on_select="rerun",  # Streamlit 1.35+
)

# Handle row selections (Streamlit 1.35+)
selected_rows = st.session_state.get("dataframe_selection", {})
```

#### Data Editor for Inline Editing
Use st.data_editor for quick edits:

```python
import streamlit as st

# Editable dataframe
edited_df = st.data_editor(
    df,
    num_rows="dynamic",  # Allow adding/deleting rows
    column_config={
        "measure_type": st.column_config.SelectboxColumn(
            "Type",
            options=get_measure_types(),
            required=True,
        ),
    },
    hide_index=True,
)

if st.button("Save Changes"):
    save_changes(edited_df)
```

#### Multipage App Navigation
Use st.Page and st.navigation (Streamlit 1.50+):

```python
# app.py
import streamlit as st

# Define pages
home_page = st.Page("ui/pages/home.py", title="Dashboard", icon="🏠")
measures_page = st.Page("ui/pages/measures.py", title="Measures", icon="📋")
areas_page = st.Page("ui/pages/areas.py", title="Areas", icon="🗺️")
priorities_page = st.Page("ui/pages/priorities.py", title="Priorities", icon="🎯")

# Create navigation
pg = st.navigation([home_page, measures_page, areas_page, priorities_page])

# Run selected page
pg.run()
```

### Database Connection Management

#### Persistent Connection Pattern
Maintain a single persistent connection with `--keep-connection` to preserve macros:

```python
# config/database.py
import duckdb
from pathlib import Path

class DatabaseConnection:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self):
        if self._connection is None:
            db_path = Path(__file__).parent.parent / "data" / "lnrs_3nf_o1.duckdb"
            self._connection = duckdb.connect(str(db_path))
            # Load macros
            self._connection.execute("CREATE MACRO IF NOT EXISTS max_meas() AS (SELECT MAX(measure_id) + 1 FROM measure)")
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

# Usage
db = DatabaseConnection()
con = db.get_connection()
```

### Development Tools
- **Code Formatting**: Ruff (Python), SQLFluff (SQL with DuckDB dialect)
- **Interactive Development**: ipykernel with `#%%` code fences
- **Version Control**: Git with GitHub MCP integration
- **Documentation**: Context7 MCP for real-time API reference

---

## Application Architecture

### File Structure (Proposed)
```
lnrs-db-app/
├── app.py                          # Main Streamlit app entry point
├── config/
│   └── database.py                 # Database connection management
├── models/
│   ├── base.py                     # Base model with common CRUD methods
│   ├── measure.py                  # Measure entity operations
│   ├── area.py                     # Area entity operations
│   ├── priority.py                 # Priority entity operations
│   ├── species.py                  # Species entity operations
│   ├── grant.py                    # Grant entity operations
│   ├── habitat.py                  # Habitat entity operations
│   └── lookup.py                   # Bridge table operations
├── ui/
│   ├── components/
│   │   ├── forms.py                # Reusable form components
│   │   ├── tables.py               # Data display components
│   │   └── filters.py              # Filter and search components
│   ├── pages/
│   │   ├── home.py                 # Dashboard/overview
│   │   ├── measures.py             # Measure CRUD
│   │   ├── areas.py                # Area CRUD
│   │   ├── priorities.py           # Priority CRUD
│   │   ├── species.py              # Species CRUD
│   │   ├── grants.py               # Grant CRUD
│   │   └── reports.py              # Data views and reports
│   └── navigation.py               # App navigation logic
├── utils/
│   ├── validators.py               # Input validation functions
│   ├── cascade_operations.py      # Cascade delete/update handlers
│   ├── queries.py                  # Common SQL query templates
│   └── constants.py                # App constants and configurations
├── data/
│   └── lnrs_3nf_o1.duckdb         # DuckDB database file
├── tests/
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_cascade_operations.py
├── lnrs_3nf_o1.sql                # Database schema
├── lnrs_3nf_o1_schema.xml         # Schema documentation
├── CLAUDE.md                       # Development guidelines
├── CRUD_APP_DEVELOPMENT_PLAN.md   # This file
├── pyproject.toml                  # Dependencies
└── README.md                       # User documentation
```

### Design Patterns
- **Repository Pattern**: Models encapsulate database operations
- **Component-Based UI**: Reusable Streamlit components
- **Page-Based Navigation**: Streamlit multipage app structure
- **Validation Layer**: Separate validation logic from business logic
- **Connection Pooling**: Single persistent DuckDB connection with `--keep-connection`

---

## CRUD Operations Planning

### 1. Measure Operations

#### Create
**User Flow**: Form → Validate → Generate ID → Insert → Link to Types/Stakeholders → Success
**Technical Steps**:
1. Use `max_meas()` macro to generate new measure_id
2. Insert into `measure` table
3. Optionally insert into `measure_has_type` (many-to-many)
4. Optionally insert into `measure_has_stakeholder` (many-to-many)
5. Optionally link to `measure_area_priority` if specific area/priority combination provided

**Validation**:
- Required: measure description
- Optional: URLs must be valid format
- Dropdowns for measure types and stakeholders

#### Read
**Views**:
- List view: Paginated table with search/filter
- Detail view: Full measure with all relationships
- Related data: Show linked types, stakeholders, areas, priorities, grants

**Query Approach**:
```sql
-- Use apmg_slim_vw for list views
-- Join to all related tables for detail views
```

#### Update
**User Flow**: Select measure → Edit form (prepopulated) → Validate → Update → Update relationships → Success
**Technical Steps**:
1. Load measure by ID with all relationships
2. Update `measure` table fields
3. Delete and recreate entries in bridge tables (measure_has_type, measure_has_stakeholder)
4. Handle measure_area_priority updates carefully

**Validation**:
- Same as Create
- Prevent orphaning bridge table records

#### Delete
**User Flow**: Select measure → Confirm deletion → Cascade delete → Success
**Critical Cascade Order**:
1. Delete from `measure_has_type`
2. Delete from `measure_has_stakeholder`
3. Delete from `measure_area_priority_grant`
4. Delete from `measure_area_priority`
5. Delete from `measure_has_benefits`
6. Delete from `measure_has_species`
7. Delete from `measure`

**Safety**:
- Show impact analysis before deletion (e.g., "This will remove 5 area-priority links")
- Require confirmation checkbox
- Log deletions for audit trail

---

### 2. Area Operations

#### Create
**User Flow**: Form → Validate → Insert → Link to funding schemes → Success
**Technical Steps**:
1. Generate new area_id (use MAX(area_id) + 1 or similar)
2. Insert into `area` table
3. Optionally insert into `area_funding_schemes`
4. Note: `area_geom` geometries managed separately (GIS workflow)

**Validation**:
- Required: area_name
- Optional: area_link must be valid URL

#### Read
**Views**:
- List view: All areas with key attributes
- Detail view: Area with linked priorities, measures, species, habitats, funding
- Map view: Display area geometries from `area_geom`

#### Update
**User Flow**: Select area → Edit form → Validate → Update → Success
**Technical Steps**:
1. Update `area` table fields
2. Update `area_funding_schemes` if changed
3. Preserve relationships in bridge tables

#### Delete
**Critical Cascade Order**:
1. Delete from `measure_area_priority_grant`
2. Delete from `measure_area_priority`
3. Delete from `species_area_priority`
4. Delete from `area_funding_schemes`
5. Delete from `habitat_creation_area`
6. Delete from `habitat_management_area`
7. Delete from `area_geom` (geometry records)
8. Delete from `area`

**Safety**:
- Areas with many measures should trigger strong warning
- Show count of affected measures, species, priorities

---

### 3. Priority Operations

#### Create
**User Flow**: Form → Validate → Insert → Success
**Technical Steps**:
1. Generate new priority_id
2. Insert into `priority` table with biodiversity_priority, simplified name, and theme

**Validation**:
- Required: biodiversity_priority, theme
- Theme should be from predefined list (extract existing themes)

#### Read
**Views**:
- List view: Group by theme
- Detail view: Priority with linked measures, areas, species

#### Update
**User Flow**: Select priority → Edit form → Validate → Update → Success
**Technical Steps**:
1. Update `priority` table fields
2. Preserve relationships in bridge tables

#### Delete
**Critical Cascade Order**:
1. Delete from `measure_area_priority_grant`
2. Delete from `measure_area_priority`
3. Delete from `species_area_priority`
4. Delete from `priority`

**Safety**:
- Priorities linked to many measures should require strong confirmation

---

### 4. Species Operations

#### Create
**User Flow**: Form → GBIF lookup (optional) → Validate → Insert → Link to areas/priorities → Success
**Technical Steps**:
1. Generate new species_id
2. Manual entry OR GBIF API lookup to populate taxonomy fields
3. Insert into `species` table
4. Optionally link to `species_area_priority`

**Validation**:
- Required: common_name or linnaean_name
- GBIF fields populated if using API
- Image URL validation

#### Read
**Views**:
- List view: Grid with species images
- Detail view: Full taxonomy, images, linked areas/priorities/measures
- Filter by assemblage, taxa

#### Update
**User Flow**: Select species → Edit form → Validate → Update → Success

#### Delete
**Cascade Order**:
1. Delete from `species_area_priority`
2. Delete from `measure_has_species`
3. Delete from `species`

---

### 5. Grant Operations

#### Create
**User Flow**: Form → Validate URL → Insert → Success
**Technical Steps**:
1. Generate grant_id (could use scheme code + sequence)
2. Insert into `grant_table`

**Validation**:
- Required: grant_name, URL (must be valid)
- Note from CLAUDE.md: "Grant records without valid URLs should not be added"

#### Read
**Views**:
- List view: Grants grouped by scheme
- Detail view: Grant with linked measures, areas, priorities

#### Update
**User Flow**: Select grant → Edit form → Validate → Update → Success

#### Delete
**Cascade Order**:
1. Delete from `measure_area_priority_grant`
2. Delete from `grant_table`

**Safety**:
- Show which measures will lose grant funding link

---

### 6. Measure Type & Stakeholder Operations

These are simpler entities used in dropdowns/multi-select for measures.

#### Create
**User Flow**: Quick add form → Insert using sequence → Success
**Technical Steps**:
- Use `nextval('seq_measure_type_id')` for measure_type
- Use `nextval('seq_stakeholder_id')` for stakeholder

#### Delete
**Cascade Order** (Measure Type):
1. Delete from `measure_has_type`
2. Delete from `measure_type`

**Cascade Order** (Stakeholder):
1. Delete from `measure_has_stakeholder`
2. Delete from `stakeholder`

---

### 7. Habitat Operations

Habitats are linked to areas for both creation and management.

#### Create
**User Flow**: Form → Insert → Link to areas → Success

#### Read
**Views**:
- List view: All habitats
- Detail view: Habitat with areas for creation vs. management

#### Update
**User Flow**: Select habitat → Edit → Update links → Success
**Technical Steps**:
- Update `habitat` table
- Manage `habitat_creation_area` and `habitat_management_area` relationships

#### Delete
**Cascade Order**:
1. Delete from `habitat_creation_area`
2. Delete from `habitat_management_area`
3. Delete from `habitat`

---

### 8. Bridge Table Management

For managing many-to-many relationships directly.

**measure_area_priority** (Core relationship):
- CRUD interface for linking measures to specific area-priority combinations
- Use dropdown selects for measure, area, priority
- Display in table format with delete option

**measure_area_priority_grant**:
- Extends measure_area_priority with grant funding
- Dropdown for grant_id from available grants
- Filter by area or priority

**Other bridge tables** (measure_has_benefits, etc.):
- Simple multi-select interfaces
- Batch operations (select multiple benefits for a measure)

---

## UI/UX Design Approach

### Navigation Structure
```
Home (Dashboard)
├── Measures
│   ├── View All Measures
│   ├── Add New Measure
│   ├── Edit Measure
│   └── Manage Measure Types & Stakeholders
├── Areas
│   ├── View All Areas
│   ├── Add New Area
│   ├── Edit Area
│   └── Map View
├── Priorities
│   ├── View All Priorities (grouped by theme)
│   ├── Add New Priority
│   └── Edit Priority
├── Species
│   ├── View All Species
│   ├── Add New Species (with GBIF lookup)
│   └── Edit Species
├── Grants
│   ├── View All Grants
│   ├── Add New Grant
│   └── Edit Grant
├── Habitats
│   ├── View Habitats
│   ├── Add New Habitat
│   └── Manage Habitat-Area Links
├── Relationships
│   ├── Measure-Area-Priority Links
│   ├── Species-Area-Priority Links
│   └── Other Relationships
└── Reports & Views
    ├── Denormalized Data View (source_table_recreated_vw)
    ├── App Data View (apmg_slim_vw)
    └── Export Data
```

### Design Principles
1. **Responsive Layout**: Use Streamlit columns for flexible layouts
2. **Progressive Disclosure**: Show summaries first, details on demand
3. **Clear Feedback**: Success/error messages with st.success(), st.error()
4. **Confirmation Dialogs**: Use st.dialog() for destructive operations (Streamlit 1.50+)
5. **Data Tables**: Use st.dataframe() with filtering and sorting
6. **Forms**: Use st.form() to batch inputs and reduce reruns
7. **Search & Filter**: Provide text search and dropdown filters on list views

### Component Design

#### Form Component Pattern
```python
# Reusable form builder
def render_entity_form(entity_type, initial_data=None, mode='create'):
    with st.form(key=f"{entity_type}_form"):
        # Render fields based on entity schema
        # Populate with initial_data if mode='edit'
        # Return form data on submit
```

#### Table Component Pattern
```python
# Reusable data table with actions
def render_data_table(data, entity_type, actions=['edit', 'delete']):
    # Display dataframe
    # Add action buttons per row
    # Handle action clicks
```

#### Cascade Preview Component
```python
# Show what will be deleted before confirmation
def render_cascade_preview(entity_type, entity_id):
    # Query related records
    # Display counts and samples
    # Return boolean for user confirmation
```

### Page Layout Example (Measure CRUD)
```
[Sidebar Navigation]

[Main Content Area]
  Title: Manage Measures

  [Search Bar] [Filter by Type] [Filter by Stakeholder] [+ Add New]

  [Data Table]
  ID | Measure | Type | Stakeholder | Areas | Actions
  --------------------------------------------------------
  1  | ...     | ... | ...         | 5     | [Edit] [Delete]

  [Pagination Controls]
```

---

## Data Validation and Error Handling

### Input Validation Rules

#### URL Validation
- Required for grants (url field)
- Optional but validated for: area_link, species_link, link_to_further_guidance
- Use regex or urllib.parse to validate format
- Display helpful error message

#### Text Field Validation
- Required vs. optional fields clearly marked
- Max length constraints based on VARCHAR limits
- Sanitize inputs to prevent SQL injection (use parameterized queries)

#### ID Generation Validation
- Ensure max_meas() macro exists and works
- Fallback to SELECT MAX(measure_id) + 1 if macro fails
- Handle race conditions (unlikely in single-user DuckDB, but good practice)

#### Relationship Validation
- FK constraint checking before insert
- Prevent orphaned records
- Validate multi-select inputs (e.g., area_id must exist)

### Error Handling Strategy

#### Database Errors
```python
try:
    conn.execute(query)
except duckdb.ConstraintException as e:
    st.error(f"Database constraint violated: {e}")
    # Provide user-friendly explanation
except duckdb.IOException as e:
    st.error(f"Database file error: {e}")
    # Suggest checking file permissions
except Exception as e:
    st.error(f"Unexpected error: {e}")
    # Log full traceback for debugging
```

#### Cascade Operation Errors
- Wrap cascade deletes in transactions
- Rollback on any failure
- Display which step failed

#### User Input Errors
- Inline validation with st.error() next to field
- Form-level validation before submission
- Clear, actionable error messages

### Transaction Management
```python
# Use DuckDB transactions for multi-step operations
conn.begin()
try:
    # Step 1: Delete from bridge tables
    # Step 2: Delete from main table
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
```

---

## Development Phases

### Phase 1: Foundation (Week 1)
**Goal**: Set up project structure and database connection

**Tasks**:
- Set up file structure as outlined in Architecture section
- Create database connection manager (config/database.py)
  - Implement persistent connection with `--keep-connection`
  - Test macro loading (max_meas())
- Create base model class with common CRUD methods
- Set up Streamlit multipage app structure
- Create navigation component
- Test basic connection and query execution

**Deliverables**:
- Working app skeleton with navigation
- Database connection working
- Base model class tested

---

### Phase 2: Read Operations (Week 2)
**Goal**: Implement data viewing for all entities

**Tasks**:
- Create table display component (ui/components/tables.py)
- Implement list views for all 6 core entities:
  - Measures (use apmg_slim_vw)
  - Areas
  - Priorities (group by theme)
  - Species (with images)
  - Grants
  - Habitats
- Add search and filter components
- Implement detail views with relationship display
- Create dashboard/home page with summary statistics

**Deliverables**:
- All entities can be viewed in list and detail modes
- Search and filter working
- Dashboard showing key metrics

---

### Phase 3: Simple Entity CRUD (Week 3)
**Goal**: Implement CRUD for entities without complex cascade deletes

**Entities**:
- Measure Type (uses sequence)
- Stakeholder (uses sequence)
- Benefits
- Habitat

**Tasks**:
- Create form components for each entity
- Implement Create operations with validation
- Implement Update operations
- Implement Delete operations with simple cascade
- Add success/error messaging
- Test thoroughly

**Deliverables**:
- Complete CRUD for 4 simple entities
- Validated input handling
- Error handling working

---

### Phase 4: Priority & Grant CRUD (Week 4)
**Goal**: Implement CRUD for moderate complexity entities

**Tasks**:
- Priority CRUD with cascade delete to 3 bridge tables
- Grant CRUD with URL validation and cascade delete
- Implement cascade preview component
- Add confirmation dialogs for destructive operations
- Test cascade deletes thoroughly

**Deliverables**:
- Complete CRUD for Priority and Grant
- Cascade delete previews working
- Confirmation dialogs implemented

---

### Phase 5: Area CRUD (Week 5)
**Goal**: Implement CRUD for Area entity (complex cascades)

**Tasks**:
- Area CRUD with cascade to 6 related tables
- Area funding schemes management
- Map view integration (display area_geom)
- Comprehensive cascade delete testing
- Handle edge cases (areas with many measures)

**Deliverables**:
- Complete CRUD for Area
- Map view showing geometries
- Robust cascade delete handling

---

### Phase 6: Measure CRUD (Week 6)
**Goal**: Implement CRUD for most complex entity

**Tasks**:
- Measure CRUD with cascade to 6 bridge tables
- Multi-select for measure types and stakeholders
- Linking to measure_area_priority
- ID generation using max_meas() macro
- Comprehensive validation
- Complex cascade delete implementation

**Deliverables**:
- Complete CRUD for Measure
- All relationships manageable
- Robust error handling

---

### Phase 7: Species CRUD & Bridge Table Management (Week 7)
**Goal**: Complete remaining CRUD operations

**Tasks**:
- Species CRUD with GBIF integration (optional)
- Image display in species views
- Bridge table management interfaces:
  - measure_area_priority (core relationship)
  - measure_area_priority_grant
  - species_area_priority
  - measure_has_benefits
  - measure_has_species
  - habitat_creation_area
  - habitat_management_area
- Batch operations for bridge tables

**Deliverables**:
- Complete CRUD for Species
- All bridge tables manageable
- GBIF lookup functional (if implemented)

---

### Phase 8: Reports & Data Views (Week 8)
**Goal**: Add reporting and data export capabilities

**Tasks**:
- Implement view for source_table_recreated_vw (verify row count matches source_table)
- Implement view for apmg_slim_vw
- Add export to CSV functionality
- Create custom reports:
  - Measures by area
  - Measures by priority
  - Species by area
  - Grant funding by area/priority
- Add data visualization (charts/graphs using Streamlit)

**Deliverables**:
- Report pages functional
- Export working
- Data visualizations added

---

### Phase 9: Polish & Optimization (Week 9)
**Goal**: Improve UX and performance

**Tasks**:
- Optimize slow queries (add indexes if needed)
- Improve UI responsiveness
- Add loading states for long operations
- Implement better error messages
- Add help text and tooltips
- Responsive design testing (mobile/tablet)
- Code cleanup and refactoring

**Deliverables**:
- Fast, responsive app
- Polished UI/UX
- Clean, maintainable code

---

### Phase 10: Testing & Documentation (Week 10)
**Goal**: Comprehensive testing and documentation

**Tasks**:
- Write unit tests for models
- Write integration tests for CRUD operations
- Test cascade deletes exhaustively
- Create user documentation (README.md)
- Create developer documentation
- Record demo video/screenshots
- Deployment testing

**Deliverables**:
- Test suite passing
- Complete documentation
- App ready for deployment

---

## Testing Strategy

### Unit Tests
**Target**: Individual model methods
**Tool**: pytest
**Coverage**:
- CRUD methods in each model class
- Validation functions (validators.py)
- ID generation (max_meas() macro)
- Cascade operation functions

**Example**:
```python
# tests/test_models.py
def test_measure_create():
    # Test measure creation with valid data
def test_measure_create_invalid_url():
    # Test validation catches invalid URL
def test_measure_delete_cascade():
    # Test all bridge tables cleared
```

### Integration Tests
**Target**: End-to-end CRUD workflows
**Coverage**:
- Create → Read → Update → Delete cycles
- Bridge table relationship management
- Transaction rollbacks on errors

### Manual Testing Checklist
- [ ] All list views load and display data correctly
- [ ] All forms validate inputs properly
- [ ] All create operations insert data correctly
- [ ] All update operations modify data correctly
- [ ] All delete operations cascade properly
- [ ] Search and filter work on all list views
- [ ] Error messages are clear and helpful
- [ ] Confirmation dialogs appear for destructive actions
- [ ] App works on different screen sizes
- [ ] No SQL injection vulnerabilities
- [ ] No orphaned records after deletes

### Data Integrity Tests
- Verify source_table_recreated_vw row count matches source_table after operations
- Check foreign key constraints are enforced
- Verify cascade deletes don't leave orphaned bridge table records
- Test concurrent operations (if applicable)

---

## Deployment Considerations

### Local Deployment (Initial)
**Method**: Run via `uv run streamlit run app.py`
**Database**: Local file `data/lnrs_3nf_o1.duckdb`
**Users**: Single user (local machine)
**Backup**: Git versioning + manual DB backups

### Shared Deployment (Future)
**Options**:
1. **Streamlit Community Cloud**: Free, easy, but single-threaded (DuckDB file locking issues)
2. **Docker Container**: Deploy on server with persistent volume for DB file
3. **MotherDuck**: DuckDB cloud service for multi-user access

**Considerations**:
- DuckDB is not designed for high concurrency (single-writer)
- For multi-user, consider:
  - Read-only mode for most users
  - Queue write operations
  - OR migrate to PostgreSQL/SQLite with WAL mode
  - OR use MotherDuck for cloud DuckDB

### Database Backup Strategy
- **Automated backups**: Daily cron job to copy .duckdb file
- **Version control**: Commit DB to Git (if small enough) or use Git LFS
- **Export to CSV**: Periodic exports as backup
- **Schema versioning**: Track schema changes in lnrs_3nf_o1.sql

### Security Considerations
- **No user authentication in Phase 1**: Assume trusted local use
- **SQL injection prevention**: Use parameterized queries exclusively
- **Input sanitization**: Validate all user inputs
- **File permissions**: Restrict DB file access to app user
- **Future**: Add authentication (Streamlit-authenticator) if deploying publicly

### Performance Optimization
- **Indexing**: Add indexes on foreign key columns if queries slow
- **Query optimization**: Use views (apmg_slim_vw) for common joins
- **Caching**: Use st.cache_data() for static data (e.g., dropdown options)
- **Pagination**: Limit result sets to 50-100 records per page
- **Connection pooling**: Single persistent connection with `--keep-connection`

---

## Success Criteria

### Functional Requirements
- [ ] All 6 core entities have full CRUD operations
- [ ] All 9 bridge tables are manageable
- [ ] Cascade deletes work correctly for all entities
- [ ] No orphaned records after any operation
- [ ] Data validation prevents invalid entries
- [ ] Search and filter work on all list views
- [ ] Reports and data views accessible

### Non-Functional Requirements
- [ ] App loads in < 3 seconds
- [ ] CRUD operations complete in < 1 second
- [ ] UI is responsive on desktop, tablet, mobile
- [ ] Error messages are clear and actionable
- [ ] Code is well-documented and maintainable
- [ ] Test coverage > 80%

### User Experience
- [ ] Non-technical users can perform CRUD operations without training
- [ ] Destructive operations require confirmation
- [ ] Impact of deletions is clear before confirmation
- [ ] Forms are intuitive with clear labels
- [ ] Success/error feedback is immediate

---

## Risk Mitigation

### Risk 1: Complex Cascade Deletes
**Mitigation**:
- Implement transaction wrappers
- Create comprehensive cascade_operations.py utility module
- Test exhaustively with different data scenarios
- Add cascade preview before deletion

### Risk 2: Data Integrity Issues
**Mitigation**:
- Use DuckDB foreign key constraints
- Validate at application layer AND database layer
- Regular integrity checks against source_table_recreated_vw
- Comprehensive test suite

### Risk 3: Performance Degradation
**Mitigation**:
- Profile slow queries early
- Add indexes proactively
- Use views for complex joins
- Implement pagination

### Risk 4: DuckDB Multi-User Limitations
**Mitigation**:
- Start with single-user local deployment
- Document limitations clearly
- Plan migration path to MotherDuck or PostgreSQL if needed
- Implement read-only mode for viewers

### Risk 5: Scope Creep
**Mitigation**:
- Follow phased development plan strictly
- Defer "nice-to-have" features to post-launch
- Focus on core CRUD first, polish later
- Regular check-ins against success criteria

---

## Next Steps

1. **Review and Approve Plan**: Stakeholder review of this document
2. **Environment Setup**: Ensure uv, dependencies, and database are ready
3. **Begin Phase 1**: Set up project structure and database connection
4. **Iterative Development**: Follow phases 1-10 with regular testing
5. **Deployment**: Deploy locally first, then consider cloud options
6. **Maintenance**: Ongoing bug fixes and feature enhancements

---

## Appendix: Key SQL Patterns

### ID Generation Pattern
```sql
CREATE MACRO max_meas() AS (SELECT MAX(measure_id) + 1 FROM measure);
INSERT INTO measure (measure_id, ...) VALUES (max_meas(), ...);
```

### Cascade Delete Pattern (Measure)
```sql
BEGIN TRANSACTION;
DELETE FROM measure_has_type WHERE measure_id = ?;
DELETE FROM measure_has_stakeholder WHERE measure_id = ?;
DELETE FROM measure_area_priority_grant WHERE measure_id = ?;
DELETE FROM measure_area_priority WHERE measure_id = ?;
DELETE FROM measure_has_benefits WHERE measure_id = ?;
DELETE FROM measure_has_species WHERE measure_id = ?;
DELETE FROM measure WHERE measure_id = ?;
COMMIT;
```

### Bridge Table Insert Pattern
```sql
-- Insert measure-area-priority relationship
INSERT INTO measure_area_priority (measure_id, area_id, priority_id)
VALUES (?, ?, ?)
ON CONFLICT DO NOTHING; -- Prevent duplicates
```

### Validation Query Pattern
```sql
-- Check if FK exists before insert
SELECT COUNT(*) FROM area WHERE area_id = ?;
-- If count = 0, reject insert
```

---

## Documentation Sources

This development plan incorporates official documentation and best practices retrieved via Context7 MCP server:

### Streamlit Documentation
- **Source**: Streamlit Official Docs (`/streamlit/docs`)
- **Key Topics**: Forms (`st.form`), Data Display (`st.dataframe`, `st.data_editor`), Multipage Apps (`st.Page`, `st.navigation`)
- **Version Coverage**: Streamlit 1.50.0+ features including dialog components and enhanced dataframe interactions
- **Code Examples**: Form patterns, column configuration, row selection handlers

### DuckDB Documentation
- **Source**: DuckDB Official Documentation (`/websites/duckdb`)
- **Key Topics**: Python Relational API, Transactions, Foreign Keys, Macros, Connection Management
- **Code Examples**: Relational API patterns, transaction handling, persistent connections
- **Best Practices**: Single-writer model, TEMP object preservation, parameterized queries

### Polars Documentation
- **Source**: Polars Repository (`/pola-rs/polars`)
- **Key Topics**: DataFrame operations, SQL integration, DuckDB integration
- **Code Examples**: SQL context usage, database reading, multi-source queries
- **Best Practices**: Lazy evaluation, efficient data transformations

### MCP Integration
The development process leverages three MCP servers:
- **DuckDB MCP**: Interactive database testing and query validation
- **GitHub MCP**: Automated version control and documentation
- **Context7 MCP**: Real-time access to latest library documentation

---

**Document Version**: 2.0
**Created**: 2025-11-02
**Last Updated**: 2025-11-02
**Updates**: Added MCP server integration, practical code examples from official documentation, database access patterns
**Status**: Planning Phase - Ready for Implementation
