# Codebase Architecture

## Application Structure

### Entry Point: `app.py`
The main Streamlit application uses the multi-page app pattern:
```python
st.Page("ui/pages/home.py", title="Dashboard", icon="🏠")
st.Page("ui/pages/measures.py", title="Measures", icon="📋")
# ... other pages
```

Navigation is handled through Streamlit's built-in page navigation.

## Architecture Layers

### 1. Presentation Layer (`ui/`)

#### Pages (`ui/pages/`)
Each page corresponds to a major entity:
- **home.py**: Dashboard with statistics
- **measures.py**: Measures CRUD operations
- **areas.py**: Areas CRUD operations
- **priorities.py**: Priorities CRUD operations
- **species.py**: Species CRUD operations
- **grants.py**: Grants CRUD operations
- **habitats.py**: Habitats CRUD operations
- **relationships.py**: Manage many-to-many relationships
- **data_export.py**: Export data to CSV

#### Components (`ui/components/`)
Reusable UI components:
- **database_selector.py**: Switch between local/MotherDuck modes
- **tables.py**: Reusable table display components

#### Page Pattern
Each CRUD page follows this structure:
```python
def show_list_view():
    """Display all records in a table"""
    
def show_detail_view(record_id):
    """Display single record details"""
    
def show_create_form():
    """Form to create new record"""
    
def show_edit_form(record_id):
    """Form to edit existing record"""
    
def show_delete_confirmation(record_id):
    """Confirmation dialog for deletion"""
```

### 2. Data Layer (`models/`)

#### Base Model (`models/base.py`)
Abstract base class providing CRUD operations:
```python
class BaseModel:
    @abstractmethod
    def table_name(self) -> str
    
    @abstractmethod
    def id_column(self) -> str
    
    # CRUD methods
    def get_all()
    def get_by_id(id)
    def create(data)
    def update(id, data)
    def delete(id)
    def filter(**kwargs)
    def exists(id)
    def count()
```

#### Entity Models
Each model extends BaseModel:
- **measure.py**: MeasureModel
- **area.py**: AreaModel
- **priority.py**: PriorityModel
- **species.py**: SpeciesModel
- **grant.py**: GrantModel
- **habitat.py**: HabitatModel
- **relationship.py**: RelationshipModel

Models use DuckDB's relational Python API for database operations.

### 3. Database Layer (`config/`)

#### Database Connection (`config/database.py`)

**Singleton Pattern** for database connections:
```python
class DatabaseConnection:
    _instance = None
    _connection = None
    _mode = None  # 'local' or 'motherduck'
```

**Key Methods**:
- `get_connection()`: Returns active DuckDB connection
- `get_connection_info()`: Returns mode and database info
- `set_mode(mode)`: Switch between local/MotherDuck
- `can_switch_mode()`: Check if mode switch is safe
- `test_connection()`: Verify connection works
- `execute_query(query)`: Execute SQL query
- `execute_transaction(queries)`: Execute multiple queries in transaction
- `get_table(table_name)`: Get table as DuckDB relation
- `_load_macros()`: Load custom SQL macros

**Connection Modes**:
1. **Local Mode**: Uses `data/lnrs_3nf_o1.duckdb`
2. **MotherDuck Mode**: Uses cloud database via `md:` prefix

**Mode Selection**:
- Environment variable: `DATABASE_MODE`
- Streamlit secrets: `database.mode`
- Default: local

## Data Flow

### Read Operation Flow
```
User clicks in UI
  ↓
Page function (ui/pages/*)
  ↓
Model method (models/*.py)
  ↓
BaseModel.get_all() / get_by_id()
  ↓
DatabaseConnection.get_table()
  ↓
DuckDB relation → DataFrame
  ↓
Streamlit displays data
```

### Write Operation Flow
```
User submits form
  ↓
Page validation (ui/pages/*)
  ↓
Model method (models/*.py)
  ↓
BaseModel.create() / update() / delete()
  ↓
DatabaseConnection.execute_query()
  ↓
DuckDB executes SQL
  ↓
Success/error feedback to user
```

### Delete Operation with Cascading
```
User confirms delete
  ↓
Model.delete(id)
  ↓
Check foreign key constraints
  ↓
Delete from bridge tables first
  ↓
Delete from main table last
  ↓
Commit transaction
  ↓
Success feedback
```

## Important Patterns

### 1. Cascading Delete Pattern
Critical for data integrity. Delete order for measures:
```python
1. measure_has_type (where measure_id = X)
2. measure_has_stakeholder (where measure_id = X)
3. measure_area_priority_grant (where measure_id = X)
4. measure_area_priority (where measure_id = X)
5. measure_has_benefits (where measure_id = X)
6. measure_has_species (where measure_id = X)
7. measure (where measure_id = X)
```

### 2. ID Generation Pattern
Uses DuckDB macros for new IDs:
```sql
CREATE MACRO max_meas() AS (SELECT MAX(measure_id) + 1 FROM measure);
INSERT INTO measure (measure_id, ...) VALUES (max_meas(), ...);
```

Sequences for some tables:
- `seq_measure_type_id`
- `seq_stakeholder_id`

### 3. Database Abstraction Pattern
- Models don't know about Streamlit
- UI pages don't write SQL directly
- DatabaseConnection handles all SQL execution
- Clear separation of concerns

### 4. Session State Pattern
Streamlit session state for:
- Current database mode
- Form state management
- Navigation state

## Database Schema Organization

### Core Tables (Main Entities)
- measure, area, priority, species, grant_table, habitat, benefits

### Lookup Tables (Bridge/Junction)
- measure_has_type
- measure_has_stakeholder
- measure_area_priority (core relationship)
- measure_area_priority_grant
- species_area_priority
- measure_has_benefits
- measure_has_species
- habitat_creation_area
- habitat_management_area

### Dimension Tables
- measure_type, stakeholder, area_funding_schemes

### Geospatial
- area_geom (694 polygons for 50 areas)

## Configuration Files

### Python Configuration
- **pyproject.toml**: Dependencies and project metadata
- **ruff.toml**: Linting and formatting rules
- **.python-version**: Python version (3.13)
- **uv.lock**: Locked dependencies

### Streamlit Configuration
- **.streamlit/secrets.toml.template**: Template for secrets

### SQL Configuration
- **lnrs_3nf_o1.sql**: Database schema definition
- **lnrs_to_motherduck.sql**: MotherDuck migration script

## Testing Structure

Tests are in root directory (not tests/ folder):
- **test_database_selector.py**: Database mode switching
- **test_local_mode.py**: Local database operations
- **test_motherduck_mode.py**: MotherDuck operations
- **test_relationships.py**: Relationship management
- **test_csv_export.py**: Data export functionality
- **test_phase_7d.py**, **test_phase_7e.py**: Phase-specific tests

## Deployment Considerations

### Local Development
- Uses local DuckDB file
- Fast, no network required
- Full data available

### Production (Streamlit Cloud)
- Can use MotherDuck (cloud DuckDB)
- Requires secrets configuration
- Network-dependent

### Environment Variables
- `DATABASE_MODE`: local or motherduck
- Secrets in `.streamlit/secrets.toml`
