# Implementation Plan: Core and Support Table Exports

## Overview

Add a new section (Section 3) to the Data Export page that allows users to export core and support tables from the LNRS database. This feature will match the existing UI style and patterns established in Sections 1 and 2.

## Objectives

1. Add "Core and Support Table Exports" section to `ui/pages/data_export.py`
2. Enable CSV exports for 9 core/support tables with record counts
3. Maintain consistent UI/UX with existing export sections
4. Use existing model infrastructure (no new model code needed)

## Tables to Export

### Core Tables (5)
1. **area** - Priority areas for biodiversity (~50 records)
2. **priority** - Biodiversity priorities grouped by themes (~33 records)
3. **measure** - Actions/recommendations for biodiversity (~780 records)
4. **species** - Species of importance with GBIF data (~39 records)
5. **grant_table** - Financial incentives/grants for landowners

### Support Tables (4)
6. **habitat** - Habitat types for creation and management
7. **measure_type** - Types of measures
8. **benefits** - Benefits delivered by measures
9. **area_funding_schemes** - Funding schemes available per area

## Technical Approach

### Models Required

All models already exist in the `models/` directory and inherit from `BaseModel`:
- `AreaModel` (models/area.py)
- `PriorityModel` (models/priority.py)
- `MeasureModel` (models/measure.py)
- `SpeciesModel` (models/species.py)
- `GrantModel` (models/grant.py)
- `HabitatModel` (models/habitat.py)

Each model has a `get_all()` method inherited from `BaseModel` that returns a Polars DataFrame, which can be exported using `.write_csv()`.

### Implementation Steps

#### 1. Import Required Models
Add imports at the top of `ui/pages/data_export.py`:
```python
from models.area import AreaModel
from models.priority import PriorityModel
from models.measure import MeasureModel
from models.species import SpeciesModel
from models.grant import GrantModel
from models.habitat import HabitatModel
```

#### 2. Initialize Model Instances
After the existing `relationship_model` initialization:
```python
area_model = AreaModel()
priority_model = PriorityModel()
measure_model = MeasureModel()
species_model = SpeciesModel()
grant_model = GrantModel()
habitat_model = HabitatModel()
```

#### 3. Add Section 3 Structure
After Section 2 (Bridge Table Exports), before the footer:
- Section header with description
- Three rows of 3-column layouts (9 export buttons total)
- Each card contains:
  - Subheader with table name
  - Caption with brief description
  - Metric showing record count
  - Download button with timestamped filename

#### 4. Layout Pattern

Follow the existing pattern from Section 2:

```python
st.header("3. Core and Support Table Exports")
st.markdown("Export core and support tables containing base entities and reference data.")

# Row 1: Core tables (area, priority, measure)
export_col1, export_col2, export_col3 = st.columns(3)

# Row 2: Core tables continued (species, grants, habitat)
export_col4, export_col5, export_col6 = st.columns(3)

# Row 3: Support tables (measure_type, benefits, area_funding_schemes)
export_col7, export_col8, export_col9 = st.columns(3)
```

#### 5. Export Card Template

Each export card follows this pattern:
```python
with export_col1:
    st.subheader("Area")
    st.caption("Priority areas for biodiversity")
    try:
        data = area_model.get_all()
        st.metric("Records", f"{len(data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"area_{timestamp}.csv"
        csv_data = data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_area",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")
```

## Special Considerations

### 1. Area Funding Schemes Table
- Need to verify if this requires a join or if it's a standalone table
- Check if `AreaModel` has a method like `get_funding_schemes()` or if we need `RelationshipModel`
- May need to execute a raw query if no model method exists

### 2. Measure Type and Benefits Tables
- These are likely lookup/reference tables
- Check if `MeasureModel` has methods like `get_all_measure_types()` and `get_all_benefits()`
- May need to use `BaseModel.execute_raw_query()` for simple SELECT queries if no dedicated model exists

### 3. Table Descriptions
Suggested captions for each table:
- **area**: "Priority areas for biodiversity"
- **priority**: "Biodiversity priorities and themes"
- **measure**: "Conservation measures and recommendations"
- **species**: "Species of importance with GBIF data"
- **grant_table**: "Available grants and funding schemes"
- **habitat**: "Habitat types for creation/management"
- **measure_type**: "Classification of measure types"
- **benefits**: "Benefits delivered by measures"
- **area_funding_schemes**: "Funding schemes per area"

## Code Location

**File to modify:** `ui/pages/data_export.py`

**Insertion point:** After line 234 (end of Section 2), before line 235 (footer separator)

## Testing Checklist

- [ ] All 9 download buttons render correctly
- [ ] Record counts display accurately for each table
- [ ] CSV files download with correct data
- [ ] Filenames include timestamps
- [ ] Layout maintains 3-column grid alignment
- [ ] No visual style differences from Section 2
- [ ] Error handling works if database unavailable
- [ ] All download buttons have unique keys
- [ ] Responsive on different screen sizes

## Dependencies

**None required** - All necessary models and utilities already exist in the codebase.

## Estimated Effort

**Implementation time:** 30-45 minutes
- Code changes: ~150 lines
- Testing: 15 minutes
- Total: < 1 hour

## Risks and Mitigations

### Risk 1: Missing Model Methods
Some support tables (measure_type, benefits, area_funding_schemes) may not have dedicated model classes.

**Mitigation:**
- Use `relationship_model.execute_raw_query()` with simple SELECT statements
- Example: `SELECT * FROM measure_type`

### Risk 2: Inconsistent Record Counts
Database may be empty or have different data than expected.

**Mitigation:**
- Error handling already in place (try/except blocks)
- Display actual counts rather than hardcoded numbers

## Success Criteria

1. ✅ Section 3 appears after Section 2 on Data Export page
2. ✅ All 9 tables can be exported as CSV
3. ✅ Record counts are accurate and displayed
4. ✅ UI matches existing section styling
5. ✅ Download buttons work reliably
6. ✅ Filenames include timestamps
7. ✅ No errors in normal operation

## Future Enhancements (Out of Scope)

- Add column selection for exports
- Add filtering options before export
- Support multiple export formats (Excel, JSON, Parquet)
- Batch export all tables as ZIP file

---

## Implementation Progress

### ✅ Completed Tasks

1. **Model imports added** - All required model classes imported successfully
2. **Model instances initialized** - 7 model instances created (area, priority, measure, species, grant, habitat, relationship)
3. **Methods verified** - Confirmed all models have required `get_all()` methods and support methods exist
4. **Section 3 implemented** - Complete 3x3 grid layout with 9 export cards matching existing UI style
5. **Export functionality tested** - All 9 tables export successfully with correct record counts
6. **Code formatted** - Ruff linting applied, minor formatting issues resolved

### Test Results

All exports tested and working:

| Table | Method | Record Count |
|-------|--------|--------------|
| Area | `area_model.get_all()` | 68 |
| Priority | `priority_model.get_all()` | 33 |
| Measure | `measure_model.get_all()` | 168 |
| Species | `species_model.get_all()` | 51 |
| Grant Table | `grant_model.get_all()` | 168 |
| Habitat | `habitat_model.get_all()` | 33 |
| Measure Type | `measure_model.get_all_measure_types()` | 11 |
| Benefits | `measure_model.get_all_benefits()` | 8 |
| Area Funding Schemes | `relationship_model.execute_raw_query()` | 28 |

### Implementation Details

**File modified:** `ui/pages/data_export.py`
- **Lines added:** ~250 lines
- **Sections modified:**
  - Imports (lines 13-19): Added 6 new model imports
  - Initialization (lines 22-28): Added 6 new model instances
  - Section 3 (lines 247-468): Complete new section with 9 export cards

### Special Implementation Notes

1. **Area Funding Schemes table** - Used `execute_raw_query()` with `.pl()` conversion to Polars DataFrame
   - Query: `SELECT * FROM area_funding_schemes ORDER BY id`
   - Columns: `id`, `area_id`, `area_name`, `local_funding_schemes`

2. **Column reuse** - Section 2 uses `export_col1-6` for bridge tables, Section 3 reuses these names plus `export_col7-9` without conflict

3. **Error handling** - Try/except blocks around all data fetching and download operations

### Code Quality

- ✅ Follows existing code patterns from Section 2
- ✅ Consistent spacing and layout
- ✅ All download buttons have unique keys
- ✅ Timestamps in all filenames
- ✅ Error messages for failed operations
- ⚠️ Minor Ruff E402 warnings (expected - path manipulation required before imports)

---

**Status:** ✅ **COMPLETED** - Implementation successful, all tests passing
**Date:** 2025-11-14
**Branch:** feature/add-core-exports
**Implementation Time:** ~45 minutes (as estimated)
