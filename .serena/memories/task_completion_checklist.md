# Task Completion Checklist

When completing any coding task in this project, follow this checklist:

## 1. Code Quality Checks

### Run Ruff Linter
```bash
uv run ruff check .
```
- Fix any errors or warnings
- Use `--fix` flag for auto-fixable issues

### Run Ruff Formatter
```bash
uv run ruff format .
```
- Ensure all Python files are properly formatted
- 4 spaces indentation, 88 character line length

## 2. Type Safety (Optional but Recommended)

### Review Type Hints
- Ensure new functions have appropriate type hints
- Use Python 3.13+ type syntax

## 3. Database Operations

### If Database Schema Changed
```bash
# Test the schema
duckdb data/lnrs_3nf_o1.duckdb
# Verify tables and relationships
```

### If CRUD Operations Modified
- Test create, read, update, delete operations
- Verify cascading deletes work correctly
- Test foreign key constraints

## 4. Testing

### Run Relevant Test Scripts
```bash
# For local database changes
DATABASE_MODE=local uv run python test_local_mode.py

# For database selector changes
DATABASE_MODE=local uv run python test_database_selector.py

# For relationship changes
uv run python test_relationships.py

# For export functionality
uv run python test_csv_export.py
```

### Manual Testing
```bash
# Start the app and test manually
DATABASE_MODE=local uv run streamlit run app.py
```
- Test the specific feature you modified
- Check for any UI/UX issues
- Verify error handling works

## 5. SQL File Changes

### If SQL Files Modified
```bash
# Format SQL files
sqlfluff format <file.sql> --dialect duckdb

# Lint SQL files
sqlfluff lint <file.sql> --dialect duckdb
```

## 6. Documentation

### Update Documentation If Needed
- Update CLAUDE.md if architecture changed
- Update README.md if user-facing changes
- Update implementation phase docs if applicable
- Add comments to complex code

## 7. Security Checks

### Review Security
- No hardcoded secrets or credentials
- URL validation for user inputs
- SQL injection prevention (use parameterized queries)
- Proper error handling to avoid exposing sensitive info

## 8. Git Operations

### Before Committing
```bash
# Check status
git status

# Review changes
git diff

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: descriptive message about changes"
```

### Commit Message Format
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, etc.
- Be descriptive and specific
- Reference issue numbers if applicable

## 9. Pre-Deployment Checks

### If Preparing for Deployment
- Review `PRE_DEPLOYMENT_CHECKLIST.md`
- Verify secrets configuration
- Test with MotherDuck mode if deploying to cloud
```bash
DATABASE_MODE=motherduck uv run python test_motherduck_mode.py
```

## 10. Code Review Checklist

### Self-Review
- [ ] Code follows project style conventions
- [ ] All linting rules pass
- [ ] Code is formatted correctly
- [ ] Type hints added where appropriate
- [ ] Docstrings added for new functions/classes
- [ ] Error handling implemented
- [ ] Tests pass (manual or automated)
- [ ] No security vulnerabilities introduced
- [ ] Foreign key constraints respected
- [ ] Cascading deletes work correctly
- [ ] UI is responsive
- [ ] Documentation updated if needed
- [ ] No debug print statements left in code
- [ ] Environment variables used for configuration

## Quick Checklist (Minimum)

For small changes, at minimum:
1. ✅ `uv run ruff check .` passes
2. ✅ `uv run ruff format .` applied
3. ✅ Manual test in Streamlit app works
4. ✅ No errors in console
5. ✅ Git commit with descriptive message
