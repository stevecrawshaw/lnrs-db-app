# Phase 2 Implementation: Read Operations

**Goal**: Implement data viewing for all entities
**Duration**: Week 2
**Status**: In Progress
**Started**: 2025-11-02

---

## Objectives

- [ ] Create reusable table display component
- [ ] Create search and filter components
- [ ] Implement list views for all 6 core entities
- [ ] Implement detail views with relationship display
- [ ] Test search and filter functionality
- [ ] Verify all data displays correctly

---

## Task Checklist

### 1. Reusable Components
- [x] Create `ui/components/tables.py` - Data table display with actions
- [x] Search functionality integrated into table component
- [x] Column configuration support
- [x] Detail view component with relationships

### 2. Entity Models
- [x] Create `models/priority.py` - Priority entity model
- [x] Create `models/grant.py` - Grant entity model
- [x] Create `models/habitat.py` - Habitat entity model
- [ ] Create `models/area.py` - Area entity model
- [ ] Create `models/species.py` - Species entity model
- [ ] Create `models/measure.py` - Measure entity model

### 3. List Views (Ordered by Complexity)
- [x] **Priorities** - Grouped by theme + table view with search
- [x] **Grants** - Grouped by scheme + table view with search
- [x] **Habitats** - Simple table with creation/management areas
- [ ] **Areas** - With funding schemes
- [ ] **Species** - With taxonomy fields (no images)
- [ ] **Measures** - With types, stakeholders, and relationship counts

### 4. Detail Views
- [x] Priority detail view - Shows linked measures, areas, species in tabs
- [x] Grant detail view - Shows funded measure-area-priority links
- [x] Habitat detail view - Show areas for creation/management
- [ ] Area detail view - Show measures, species, priorities, funding
- [ ] Species detail view - Show taxonomy and linked measures/areas
- [ ] Measure detail view - Show all relationships

### 5. Search and Filter
- [ ] Text search functionality
- [ ] Dropdown filters for categorical fields
- [ ] Multi-select filters where appropriate
- [ ] Clear filters button

### 6. Testing
- [ ] All list views load correctly
- [ ] Search works on all entities
- [ ] Filters work correctly
- [ ] Detail views show all relationships
- [ ] Pagination works (if implemented)
- [ ] No performance issues with full dataset

---

## Implementation Details

### Component Design

#### Table Display Component (`ui/components/tables.py`)
**Purpose**: Reusable data table with search, filter, and actions

**Features**:
- Configurable columns with types
- Search across specified columns
- Column-specific filters
- Row actions (view details, edit, delete)
- Pagination support
- Sorting support

#### Filter Component (`ui/components/filters.py`)
**Purpose**: Reusable search and filter widgets

**Features**:
- Text search input
- Single-select dropdown filters
- Multi-select filters
- Date range filters (if needed)
- Clear all filters button

### Entity Model Pattern

Each entity model inherits from `BaseModel` and adds:
- Relationship queries (get related entities)
- Custom views (e.g., grouped views)
- Formatted data for display

Example structure:
```python
class PriorityModel(BaseModel):
    @property
    def table_name(self) -> str:
        return "priority"

    @property
    def id_column(self) -> str:
        return "priority_id"

    def get_by_theme(self) -> dict[str, pl.DataFrame]:
        """Get priorities grouped by theme."""
        pass

    def get_related_measures(self, priority_id: int) -> pl.DataFrame:
        """Get measures linked to this priority."""
        pass
```

### List View Pattern

Each list view page includes:
1. Page title and count
2. Search and filter section
3. Data table display
4. Action buttons (view details)
5. Add new button (for later phases)

### Detail View Pattern

Each detail view shows:
1. Entity details (all fields)
2. Related entities (tabbed or sectioned)
3. Counts of relationships
4. Back to list button

---

## Entity Implementation Order

### 1. Priorities (Simplest)
**Table**: `priority` (33 records)
**Display**: Group by theme
**Relationships**: measures, areas, species via bridge tables
**Fields**: priority_id, biodiversity_priority, simplified_biodiversity_priority, theme

### 2. Grants (Simple)
**Table**: `grant_table` (168 records)
**Display**: Table grouped by scheme
**Relationships**: measures via measure_area_priority_grant
**Fields**: grant_id, grant_name, grant_scheme, url, grant_summary

### 3. Habitats (Simple)
**Table**: `habitat`
**Display**: Table with creation/management area counts
**Relationships**: Areas via habitat_creation_area and habitat_management_area
**Fields**: habitat_id, habitat

### 4. Areas (Moderate)
**Table**: `area` (68 records)
**Display**: Table with area details
**Relationships**: measures, priorities, species, funding schemes, habitats, geometries
**Fields**: area_id, area_name, area_description, area_link, bng_hab_mgt, bng_hab_creation

### 5. Species (Moderate)
**Table**: `species` (51 records)
**Display**: Table with taxonomy (no images per user requirement)
**Relationships**: measures, areas, priorities
**Fields**: species_id, common_name, linnaean_name, assemblage, taxa, scientific_name, etc.

### 6. Measures (Most Complex)
**Table**: `measure` (168 records)
**Display**: Table with types, stakeholders, relationship counts
**Relationships**: types, stakeholders, areas, priorities, grants, species, benefits
**Fields**: measure_id, measure, concise_measure, core_supplementary, mapped_unmapped, link_to_further_guidance

**Note**: Measures require JOINs to display:
- Measure types (via measure_has_type)
- Stakeholders (via measure_has_stakeholder)
- Area/priority counts (via measure_area_priority)

---

## Files to Create/Modify

### New Files
1. `ui/components/tables.py` - Table display component
2. `ui/components/filters.py` - Search/filter component
3. `models/priority.py` - Priority model
4. `models/grant.py` - Grant model
5. `models/habitat.py` - Habitat model
6. `models/area.py` - Area model
7. `models/species.py` - Species model
8. `models/measure.py` - Measure model

### Modified Files
1. `ui/pages/priorities.py` - Add list and detail views
2. `ui/pages/grants.py` - Add list and detail views
3. `ui/pages/areas.py` - Add list and detail views
4. `ui/pages/species.py` - Add list and detail views
5. `ui/pages/measures.py` - Add list and detail views
6. `ui/pages/home.py` - Update with links to entity lists (optional)

---

## Testing Checklist

### Component Tests
- [ ] Table component displays data correctly
- [ ] Table component handles empty data gracefully
- [ ] Filter component updates data on change
- [ ] Search component filters correctly

### Priority Tests
- [ ] List view shows all 33 priorities
- [ ] Priorities grouped by theme correctly
- [ ] Detail view shows linked measures/areas/species
- [ ] Search works on priority name

### Grant Tests
- [ ] List view shows all 168 grants
- [ ] Grants grouped by scheme
- [ ] Detail view shows linked measures
- [ ] Search works on grant name
- [ ] URL links are clickable

### Habitat Tests
- [ ] List view shows all habitats
- [ ] Creation area count shown
- [ ] Management area count shown
- [ ] Detail view shows all linked areas

### Area Tests
- [ ] List view shows all 68 areas
- [ ] Funding schemes displayed
- [ ] Detail view shows measures, priorities, species
- [ ] BNG habitat fields shown

### Species Tests
- [ ] List view shows all 51 species
- [ ] Taxonomy fields displayed (no images)
- [ ] Filter by assemblage works
- [ ] Filter by taxa works
- [ ] Detail view shows full taxonomy
- [ ] Detail view shows linked measures/areas

### Measure Tests
- [ ] List view shows all 168 measures
- [ ] Measure types displayed
- [ ] Stakeholders displayed
- [ ] Core/Supplementary badge shown
- [ ] Relationship counts shown
- [ ] Detail view shows all relationships
- [ ] Search works on measure text
- [ ] Filter by type works
- [ ] Filter by stakeholder works

---

## Performance Considerations

- [ ] Table rendering is fast (< 1 second)
- [ ] Search is responsive
- [ ] Filter updates are immediate
- [ ] No unnecessary database queries
- [ ] Use session state for caching where appropriate

---

## Issues Encountered

### Issue Log
*Document any issues encountered during implementation*

---

## Next Steps (Phase 3)

After Phase 2 completion:
1. Implement CREATE operations for simple entities
2. Add form validation
3. Implement UPDATE operations
4. Implement DELETE with cascade handling

---

**Phase 2 Status**: 🔄 In Progress (50% Complete)
**Started**: 2025-11-02
**Last Updated**: 2025-11-02
**Estimated Completion**: [In progress]

---

## Progress Summary

### ✅ Completed (3 of 6 entities)

**1. Priorities** ✓
- Model: `models/priority.py` with relationship queries
- Page: `ui/pages/priorities.py` with list and detail views
- Features:
  - Grouped by theme view
  - Table view with search
  - Detail view showing linked measures (2), areas (45), species (8) for sample
  - Relationship tabs (Measures, Areas, Species)
  - 33 total priorities displayed correctly

**2. Grants** ✓
- Model: `models/grant.py` with relationship queries
- Page: `ui/pages/grants.py` with list and detail views
- Features:
  - Grouped by scheme view
  - Table view with search
  - Detail view showing funded measure-area-priority links
  - Clickable URL links
  - 168 total grants displayed correctly

**3. Habitats** ✓
- Model: `models/habitat.py` with relationship queries
- Page: `ui/pages/habitats.py` with list and detail views
- Features:
  - List view with creation/management area counts
  - Detail view with two tabs (Creation Areas, Management Areas)
  - Search functionality
  - View details action
  - 33 total habitats displayed correctly

**4. Table Component** ✓
- File: `ui/components/tables.py`
- Features:
  - Reusable data table display
  - Integrated search across specified columns
  - Column configuration support
  - Detail view with relationship tabs
  - Grouped table display
  - Filter widget creation

### 🔄 In Progress

**Next entities to implement:**
1. Area (moderate - estimated 45 min)
2. Species (moderate - estimated 45 min)
3. Measure (complex - estimated 60 min)

### 📊 Files Created

**Models (3 files)**:
1. `models/priority.py` - 125 lines
2. `models/grant.py` - 65 lines
3. `models/habitat.py` - 140 lines

**Pages (3 files modified)**:
1. `ui/pages/priorities.py` - 226 lines (complete list + detail)
2. `ui/pages/grants.py` - 170 lines (complete list + detail)
3. `ui/pages/habitats.py` - 161 lines (complete list + detail)

**Components (1 file)**:
1. `ui/components/tables.py` - 320 lines (reusable components)

**Documentation (1 file)**:
1. `PHASE_2_IMPLEMENTATION.md` - This file

**App Navigation (1 file modified)**:
1. `app.py` - Added habitats page to navigation

**Total**: ~1,200 lines of new/updated code

### 🎯 What's Working

- ✅ Priority list view with theme grouping
- ✅ Priority detail view with 3 relationship tabs
- ✅ Grant list view with scheme grouping
- ✅ Grant detail view with funded measures
- ✅ Habitat list view with creation/management area counts
- ✅ Habitat detail view with 2 relationship tabs (Creation/Management Areas)
- ✅ Search functionality on text fields
- ✅ Column configuration for better display
- ✅ Session state management for view switching
- ✅ Back navigation between list and detail views

### 🧪 Test the App

To see the completed views:
```bash
uv run streamlit run app.py
```

Then navigate to:
- **Priorities** page - View 33 priorities grouped by 6 themes
- **Grants** page - View 168 grants grouped by schemes
- **Habitats** page - View 33 habitats with creation/management area counts

### 📝 Remaining Work

**To complete Phase 2, still need to create:**
1. Area model + page (moderate - funding schemes, multiple relationships)
2. Species model + page (moderate - taxonomy fields, no images)
3. Measure model + page (complex - types, stakeholders, many relationships)

**Estimated time**: 2-3 hours additional work
