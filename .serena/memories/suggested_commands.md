# Suggested Commands for LNRS Database App

## Package Management (using uv)

### Install Dependencies
```bash
uv sync                    # Install all dependencies from uv.lock
```

### Add New Dependency
```bash
uv add <package-name>      # Add new package
uv add --dev <package>     # Add dev dependency
```

## Running the Application

### Start Streamlit App (Local Mode)
```bash
DATABASE_MODE=local uv run streamlit run app.py
```

### Start Streamlit App (MotherDuck Mode)
```bash
DATABASE_MODE=motherduck uv run streamlit run app.py
```

### Default Run (Mode Auto-Selected)
```bash
uv run streamlit run app.py
```

## Code Quality & Formatting

### Run Ruff Linter
```bash
uv run ruff check .                    # Check all files
uv run ruff check --fix .              # Auto-fix issues
uv run ruff check path/to/file.py      # Check specific file
```

### Run Ruff Formatter
```bash
uv run ruff format .                   # Format all files
uv run ruff format path/to/file.py     # Format specific file
```

## Database Operations

### Connect to DuckDB CLI
```bash
duckdb data/lnrs_3nf_o1.duckdb
```

### Execute SQL File
```bash
duckdb data/lnrs_3nf_o1.duckdb -f <file.sql>
```

### Recreate Database from Schema
```bash
rm data/lnrs_3nf_o1.duckdb
duckdb data/lnrs_3nf_o1.duckdb
# In DuckDB CLI:
.read lnrs_3nf_o1.sql
```

## Testing

### Run Python Test Scripts
```bash
DATABASE_MODE=local uv run python test_database_selector.py
DATABASE_MODE=local uv run python test_local_mode.py
DATABASE_MODE=motherduck uv run python test_motherduck_mode.py
uv run python test_relationships.py
uv run python test_csv_export.py
uv run python test_phase_7d.py
uv run python test_phase_7e.py
```

### Test Database Connection
```bash
uv run python -c "from config.database import DatabaseConnection; db = DatabaseConnection(); db.test_connection()"
```

### Validate Schema
```bash
uv run python validate_motherduck_schema.py
```

## Development Tools

### Start Interactive Python Session
```bash
uv run ipython
```

### Start Jupyter Kernel
```bash
uv run jupyter notebook
```

### Run Python Script
```bash
uv run python <script.py>
```

## SQLFluff (SQL Formatting)

### Format SQL Files
```bash
sqlfluff format <file.sql> --dialect duckdb
```

### Lint SQL Files
```bash
sqlfluff lint <file.sql> --dialect duckdb
```

## Git Operations

### Common Git Commands
```bash
git status                 # Check status
git add .                  # Stage all changes
git commit -m "message"    # Commit changes
git push                   # Push to remote
```

## Environment Variables

### Set Database Mode
```bash
export DATABASE_MODE=local        # Use local DuckDB
export DATABASE_MODE=motherduck   # Use MotherDuck cloud
```

### Check Current Environment
```bash
env | grep DATABASE_MODE
```

## System Utilities (Linux)

### File Operations
```bash
ls -la                     # List files with details
cd <directory>             # Change directory
grep -r "pattern" .        # Search for pattern
find . -name "*.py"        # Find Python files
```

### Process Management
```bash
ps aux | grep streamlit    # Find streamlit process
kill <PID>                 # Kill process
```
