# Code Style and Conventions

## Python Code Style

### General Rules
- **Python Version**: >= 3.13
- **Line Length**: 88 characters (Black-compatible)
- **Indentation**: 4 spaces (NO tabs)
- **Quote Style**: Double quotes (`"`)
- **Encoding**: UTF-8

### Formatting Tool: Ruff
Configuration in `ruff.toml`:
- Line length: 88
- Target version: py313
- Auto-fix enabled for all rules

### Linting Rules (Ruff)
Enabled rule sets:
- **E, W**: pycodestyle errors and warnings
- **F**: pyflakes
- **UP**: pyupgrade (Python version upgrades)
- **S**: flake8-bandit (security)
- **B**: flake8-bugbear (bug detection)
- **SIM**: flake8-simplify
- **I**: isort (import sorting)

### Type Hints
- Use type hints where appropriate
- Not strictly enforced but encouraged for clarity

### Docstrings
- Include docstrings for functions and classes
- No specific format required (but should be clear)

### Import Organization
- Sorted by isort (via Ruff)
- Order: standard library, third-party, local

### Variable Naming
- **snake_case**: Functions, variables, methods
- **PascalCase**: Classes
- **UPPER_CASE**: Constants
- Dummy variables: Regex pattern `^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$`

## SQL Code Style

### General Rules
- **SQL Dialect**: DuckDB
- **Indentation**: 4 spaces
- **Formatting Tool**: SQLFluff with DuckDB dialect
- **Format on Save**: Enabled

### SQL Conventions
- Consistent naming conventions
- Comments for complex queries
- Proper indentation for readability

### Reserved Keywords
- Avoid using SQL reserved keywords as table names
- Example: Use `grant_table` instead of `grants`

## Project-Specific Patterns

### Database Operations
1. **Prefer DuckDB Relational Python API** over raw SQL wherever possible
2. **Use SQL only for complex operations** that are difficult with the API
3. **Always respect foreign key constraints** and cascading deletes

### Model Pattern
All models inherit from `BaseModel` in `models/base.py`:
- Each model represents a database table
- Models use `@abstractmethod` for `table_name` and `id_column`
- CRUD operations: `create()`, `get_all()`, `get_by_id()`, `update()`, `delete()`

### Database Connection Pattern
- Singleton pattern: `DatabaseConnection` class
- Auto-detects mode: local or MotherDuck
- Environment variable: `DATABASE_MODE`

### UI Page Pattern
Each page in `ui/pages/` follows a consistent structure:
- `show_list_view()`: Display all records
- `show_detail_view()`: Display single record
- `show_create_form()`: Form for creating records
- `show_edit_form()`: Form for editing records
- `show_delete_confirmation()`: Confirm before delete

### Error Handling
- All database operations should have try-except blocks
- User-friendly error messages in Streamlit
- Log errors appropriately

### Streamlit Best Practices
- Responsive design for different screen sizes
- Use Streamlit session state for form management
- Clear user feedback for all operations

## File Structure Conventions

### Module Organization
```python
# Standard library imports
import os
import sys

# Third-party imports
import streamlit as st
import duckdb

# Local imports
from models.base import BaseModel
from config.database import DatabaseConnection
```

### Path Handling
Use `Path(__file__).resolve().parent` for relative imports:
```python
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
```

## Testing Conventions

### Test Files
- Test files located in root directory (not in tests/ folder)
- Naming: `test_*.py`
- Use `DATABASE_MODE=local` for most tests

### Interactive Development
- Use `#%%` code fences for ipykernel interactive cells
- Helpful for testing and development

## Security

### Sensitive Data
- Never commit secrets to git
- Use `.streamlit/secrets.toml` for secrets (see template)
- Use environment variables for configuration

### URL Validation
- Grant records without valid URLs should not be added
- Implement URL validation in forms
