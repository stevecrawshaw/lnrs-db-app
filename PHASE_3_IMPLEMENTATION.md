# Phase 3 Implementation: Create, Update, Delete Operations

**Goal**: Implement full CRUD operations for all entities
**Duration**: Week 3
**Status**: ✅ COMPLETE (All 6 Entities Implemented!)
**Started**: 2025-11-02
**Phase 3A Completed**: 2025-11-02
**Phase 3B Completed**: 2025-11-02 (All Entities Done!)
**Completion Date**: 2025-11-02

---

## Objectives

- [x] Implement CREATE operations for simple entities (Phase 3A)
- [x] Implement UPDATE operations for simple entities (Phase 3A)
- [x] Implement DELETE operations with proper cascade handling for simple entities (Phase 3A)
- [x] Add form validation for all inputs (Phase 3A)
- [x] Implement error handling and user feedback (Phase 3A)
- [x] Add confirmation dialogs for destructive operations (Phase 3A)
- [x] Implement CREATE operations for complex entities (Phase 3B) - All Complete ✅
- [x] Implement UPDATE operations for complex entities (Phase 3B) - All Complete ✅
- [x] Implement DELETE operations for complex entities (Phase 3B) - All Complete ✅
- [x] Implement Measures CRUD (Phase 3B) - ✅ COMPLETE!

---

## Task Checklist

### 1. Reusable Form Components
- [x] Inline forms with validation (implemented in each page)
- [x] Text input with validation
- [x] Text area with validation
- [x] Dropdown select for themes
- [x] URL validation for link fields (grants)
- [x] Success/error message components (using st.success/st.error)
- [ ] Separate `ui/components/forms.py` module (not needed - inline forms work well)
- [ ] Multi-select for many-to-many relationships (deferred to Phase 3B)

### 2. CREATE Operations (Ordered by Complexity)

#### Simple Entities (No dependencies) - ✅ PHASE 3A COMPLETE
- [x] **Priorities** - Create new biodiversity priority
  - Form fields: biodiversity_priority, simplified_biodiversity_priority, theme
  - Auto-incrementing priority_id
  - Theme dropdown with 6 options
  - Validation for required fields
  - Location: `ui/pages/priorities.py:32-98`

- [x] **Habitats** - Create new habitat type
  - Form fields: habitat
  - Auto-incrementing habitat_id
  - Validation for required field
  - Location: `ui/pages/habitats.py:31-71`

#### Moderate Entities (Foreign key dependencies) - ✅ PHASE 3A COMPLETE
- [x] **Grants** - Create new grant/funding scheme
  - Form fields: grant_id (user-provided), grant_name, grant_scheme, url, grant_summary
  - URL validation using `urllib.parse.urlparse`
  - Duplicate ID check
  - Validation for required fields
  - Location: `ui/pages/grants.py:52-132`

- [x] **Species** - Create new species entry ✅ PHASE 3B COMPLETE
  - Form fields: common_name, linnaean_name, assemblage, taxa, scientific_name
  - Optional taxonomy fields: kingdom, phylum, class, order, family, genus
  - Auto-incrementing species_id
  - Validation for required fields
  - Location: `ui/pages/species.py:32-123`

- [x] **Areas** - Create new priority area ✅ PHASE 3B COMPLETE
  - Form fields: area_name, area_description, area_link
  - Auto-incrementing area_id
  - URL validation for area_link
  - Validation for required fields
  - Location: `ui/pages/areas.py:53-117`

#### Complex Entities (Many-to-many relationships)
- [x] **Measures** - Create new measure ✅ PHASE 3B COMPLETE
  - Form fields: measure, concise_measure, core_supplementary, mapped_unmapped, link_to_further_guidance
  - Multi-select relationships: types (11 options), stakeholders (5 options), benefits (8 options)
  - Auto-incrementing measure_id using MAX() pattern
  - URL validation for link_to_further_guidance
  - Validation for required fields
  - Location: `ui/pages/measures.py:53-172`
  - Note: Area-Priority linkage comes later

### 3. UPDATE Operations

#### Phase 3A - ✅ COMPLETE
- [x] **Priorities** - Edit existing priority
  - Update biodiversity_priority, simplified_biodiversity_priority, theme
  - Form pre-populated with existing data
  - Same validation as CREATE
  - Location: `ui/pages/priorities.py:100-177`

- [x] **Grants** - Edit existing grant
  - Update grant_name, grant_scheme, url, grant_summary
  - URL validation (same as CREATE)
  - Cannot change grant_id
  - Location: `ui/pages/grants.py:135-205`

- [x] **Habitats** - Edit existing habitat
  - Update habitat name
  - Form pre-populated with existing data
  - Location: `ui/pages/habitats.py:74-115`

#### Phase 3B - ✅ Species & Areas COMPLETE

- [x] **Areas** - Edit existing area ✅
  - Update area_name, area_description, area_link
  - URL validation (same as CREATE)
  - Form pre-populated with existing data
  - Location: `ui/pages/areas.py:120-183`

- [x] **Species** - Edit existing species ✅
  - Update common_name, scientific_name, assemblage, taxa
  - Update taxonomy fields (kingdom through genus)
  - Form pre-populated with existing data
  - Location: `ui/pages/species.py:126-220`

- [x] **Measures** - Edit existing measure ✅
  - Update all basic fields (measure, concise_measure, etc.)
  - Update multi-select relationships (types, stakeholders, benefits)
  - Pre-populate multiselects with existing relationships
  - Delete old relationships and add new ones on update
  - Location: `ui/pages/measures.py:175-319`

### 4. DELETE Operations (With Cascade Handling)

**CRITICAL**: All delete operations must respect foreign key constraints as documented in CLAUDE.md

#### Phase 3A - ✅ COMPLETE

- [x] **Priorities** - Delete with cascade
  - Cascade order (from CLAUDE.md):
    1. Delete from `measure_area_priority_grant` where priority_id matches
    2. Delete from `measure_area_priority` where priority_id matches
    3. Delete from `species_area_priority` where priority_id matches
    4. Finally delete from `priority`
  - Confirmation dialog showing relationship impact
  - Model method: `models/priority.py:127-165`
  - UI: `ui/pages/priorities.py:179-216`

- [x] **Grants** - Delete with cascade
  - Cascade order (from CLAUDE.md):
    1. Delete from `measure_area_priority_grant` where grant_id matches
    2. Finally delete from `grant_table`
  - Confirmation dialog showing relationship impact
  - Model method: `models/grant.py:80-108`
  - UI: `ui/pages/grants.py:208-246`

- [x] **Habitats** - Delete with cascade
  - Cascade order (from CLAUDE.md):
    1. Delete from `habitat_creation_area` where habitat_id matches
    2. Delete from `habitat_management_area` where habitat_id matches
    3. Finally delete from `habitat`
  - Confirmation dialog showing relationship impact
  - Model method: `models/habitat.py:104-137`
  - UI: `ui/pages/habitats.py:118-154`

#### Phase 3B - ✅ Species & Areas COMPLETE

- [x] **Areas** - Delete with cascade ✅
  - Cascade order (from CLAUDE.md):
    1. Delete from `measure_area_priority_grant` where area_id matches
    2. Delete from `measure_area_priority` where area_id matches
    3. Delete from `species_area_priority` where area_id matches
    4. Delete from `area_funding_schemes` where area_id matches
    5. Delete from `habitat_creation_area` where area_id matches
    6. Delete from `habitat_management_area` where area_id matches
    7. Finally delete from `area`
  - Model method: `models/area.py:220-273`
  - UI: `ui/pages/areas.py:186-224`
  - Confirmation dialog showing relationship impact
  - **6-table cascade delete** - most complex after measures!

- [x] **Species** - Delete with cascade ✅
  - Cascade order (from CLAUDE.md):
    1. Delete from `species_area_priority` where species_id matches
    2. Delete from `measure_has_species` where species_id matches
    3. Finally delete from `species`
  - Model method: `models/species.py:109-142`
  - UI: `ui/pages/species.py:223-261`
  - Confirmation dialog showing relationship impact

- [x] **Measures** - Delete with cascade ✅
  - Cascade order (from CLAUDE.md):
    1. Delete from `measure_has_type` where measure_id matches
    2. Delete from `measure_has_stakeholder` where measure_id matches
    3. Delete from `measure_area_priority_grant` where measure_id matches
    4. Delete from `measure_area_priority` where measure_id matches
    5. Delete from `measure_has_benefits` where measure_id matches
    6. Delete from `measure_has_species` where measure_id matches
    7. Finally delete from `measure`
  - Model method: `models/measure.py:280-333`
  - UI: `ui/pages/measures.py:322-364`
  - Confirmation dialog with comprehensive relationship impact preview
  - **6-table cascade delete** - tied with Areas for most complex!
  - Extra warning for measures with 20+ relationships showing all relationships

### 5. Validation & Error Handling

- [ ] Required field validation
- [ ] URL format validation for links
- [ ] Duplicate name detection (where appropriate)
- [ ] Foreign key validation
- [ ] Max length validation for text fields
- [ ] SQL injection prevention (already handled by BaseModel)
- [ ] User-friendly error messages
- [ ] Success confirmations

### 6. Testing

- [ ] CREATE operations work for all entities
- [ ] UPDATE operations preserve relationships
- [ ] DELETE cascade works correctly
- [ ] Validation catches invalid inputs
- [ ] Error messages are clear and helpful
- [ ] UI remains responsive during operations
- [ ] Database integrity maintained after operations

---

## Implementation Strategy

### Phase 3A: Simple CRUD (Week 1)
Focus on entities with minimal dependencies:
1. Priorities (simplest)
2. Habitats (simple)
3. Grants (moderate - URL validation)

### Phase 3B: Complex CRUD (Week 2)
Entities with more complexity:
4. Species (taxonomy fields)
5. Areas (funding schemes, multiple relationships)
6. Measures (most complex - types, stakeholders, many relationships)

### Phase 3C: Advanced Features (Week 3)
- Bulk operations
- Import/Export functionality
- Advanced validation
- Audit logging

---

## Form Design Patterns

### CREATE Form Pattern
```python
def show_create_form():
    """Display form to create new entity."""
    with st.form("create_entity_form"):
        # Form fields
        name = st.text_input("Name*", help="Required field")
        description = st.text_area("Description")

        # Submit button
        submitted = st.form_submit_button("Create")

        if submitted:
            # Validate inputs
            if not name:
                st.error("Name is required")
                return

            # Create entity
            try:
                entity_id = model.create({
                    "name": name,
                    "description": description
                })
                st.success(f"Created successfully! ID: {entity_id}")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating entity: {str(e)}")
```

### UPDATE Form Pattern
```python
def show_update_form(entity_id):
    """Display form to update existing entity."""
    entity = model.get_by_id(entity_id)

    with st.form("update_entity_form"):
        # Pre-populate fields
        name = st.text_input("Name*", value=entity['name'])
        description = st.text_area("Description", value=entity.get('description', ''))

        # Submit button
        submitted = st.form_submit_button("Update")

        if submitted:
            # Validate and update
            try:
                model.update(entity_id, {
                    "name": name,
                    "description": description
                })
                st.success("Updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating: {str(e)}")
```

### DELETE Confirmation Pattern
```python
def show_delete_confirmation(entity_id):
    """Show confirmation dialog before deleting."""
    entity = model.get_by_id(entity_id)
    counts = model.get_relationship_counts(entity_id)

    st.warning(f"⚠️ Delete {entity['name']}?")

    # Show impact
    if sum(counts.values()) > 0:
        st.error("This will also delete:")
        for relationship, count in counts.items():
            if count > 0:
                st.write(f"- {count} {relationship}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Delete", type="primary"):
            try:
                model.delete_with_cascade(entity_id)
                st.success("Deleted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {str(e)}")
```

---

## Database Operations to Add to BaseModel

### In `models/base.py`:

```python
def create(self, data: dict) -> int:
    """Create a new record and return its ID."""
    pass

def update(self, id: int, data: dict) -> bool:
    """Update an existing record."""
    pass

def delete(self, id: int) -> bool:
    """Delete a record (simple delete, no cascade)."""
    pass
```

### Entity-Specific Delete Methods

Each model will need a custom `delete_with_cascade()` method that follows the cascade order specified in CLAUDE.md.

---

## UI/UX Considerations

1. **Form Placement**: Add forms in modal dialogs or expandable sections to avoid cluttering list views
2. **Inline Editing**: Consider inline editing for simple fields
3. **Multi-step Forms**: Break complex forms (like Measures) into steps
4. **Validation Feedback**: Real-time validation with clear error messages
5. **Loading States**: Show spinners during database operations
6. **Confirmation Dialogs**: Always confirm destructive operations
7. **Success Messages**: Clear feedback when operations succeed

---

## Performance Considerations

- [ ] Batch operations where possible
- [ ] Use transactions for cascade deletes
- [ ] Validate inputs before database operations
- [ ] Cache foreign key lookups for dropdowns
- [ ] Limit dropdown options for large tables

---

## Security Considerations

- [ ] SQL injection prevention (handled by BaseModel parameterized queries)
- [ ] Input sanitization for text fields
- [ ] URL validation to prevent malicious links
- [ ] Role-based access control (future phase)
- [ ] Audit logging for all CUD operations (future phase)

---

## Files to Create/Modify

### New Files
1. `ui/components/forms.py` - Reusable form components
2. `ui/components/dialogs.py` - Confirmation dialogs

### Modified Files
1. All model files - Add create(), update(), delete_with_cascade() methods
2. All page files - Add create, update, delete UI
3. `models/base.py` - Add base CRUD methods

---

## Testing Checklist

### Phase 3A Tests - ✅ COMPLETE

#### Priority Tests
- [x] Create new priority
- [x] Update priority name and theme
- [x] Delete priority with no relationships
- [x] Delete priority with relationships (cascade)
- [x] Validation: Required fields

#### Grant Tests
- [x] Create new grant with URL
- [x] Update grant details
- [x] Delete grant
- [x] Validation: URL format
- [x] Duplicate ID detection

#### Habitat Tests
- [x] Create new habitat
- [x] Update habitat name
- [x] Delete habitat with area links (cascade)

### Phase 3B Tests - Pending

### Area Tests
- [ ] Create new area
- [ ] Update area description and funding schemes
- [ ] Delete area with all relationships (cascade)

### Species Tests
- [ ] Create new species with taxonomy
- [ ] Update species taxonomy
- [ ] Delete species with relationships (cascade)

### Measure Tests
- [ ] Create new measure with types and stakeholders
- [ ] Update measure and relationships
- [ ] Delete measure with all relationships (cascade)
- [ ] Validation: Required fields

---

## Known Challenges

1. **Cascade Deletes**: Must follow exact order specified in CLAUDE.md
2. **Many-to-Many UI**: Need intuitive multi-select for relationships
3. **Validation Complexity**: Different entities have different rules
4. **User Feedback**: Clear communication of what will be deleted
5. **Performance**: Large cascade deletes may be slow

---

## Success Criteria

### Phase 3A - ✅ COMPLETE
✅ Users can create new records for simple entities (Priorities, Habitats, Grants)
✅ Users can update existing records for simple entities
✅ Users can delete records with proper cascade handling for simple entities
✅ All forms validate inputs correctly
✅ URL validation works for grants
✅ Error messages are clear and helpful
✅ Database integrity is maintained
✅ No orphaned records after deletes
✅ Confirmation dialogs show relationship impact

### Phase 3B - Pending
- [ ] Users can create new records for complex entities (Species, Areas, Measures)
- [ ] Users can update existing records for complex entities
- [ ] Users can delete records with proper cascade handling for complex entities

---

**Phase 3 Status**: 🔄 In Progress (Phase 3A Complete)
**Phase 3A Completed**: 2025-11-02 (Same day!)
**Estimated Duration for Phase 3B**: 1-2 weeks
**Priority**: High

---

## Phase 3A Completion Summary

### ✅ What Was Completed (2025-11-02)

**Entities Implemented (3 of 6):**
1. **Priorities** - Full CRUD with theme dropdown and cascade delete
2. **Habitats** - Full CRUD with cascade delete
3. **Grants** - Full CRUD with URL validation and cascade delete

**Files Modified/Created:**

**Models (3 files):**
- `models/priority.py` - Added `delete_with_cascade()` method (lines 127-165)
- `models/habitat.py` - Added `delete_with_cascade()` method (lines 104-137)
- `models/grant.py` - Added `delete_with_cascade()` method (lines 80-108)

**Pages (3 files rewritten):**
- `ui/pages/priorities.py` - Complete CRUD implementation (464 lines)
  - CREATE form with theme dropdown and auto-incrementing ID
  - UPDATE form with pre-populated data
  - DELETE confirmation showing relationship impact
  - Session state for form visibility

- `ui/pages/habitats.py` - Complete CRUD implementation (330 lines)
  - CREATE form with auto-incrementing ID
  - UPDATE form with pre-populated data
  - DELETE confirmation showing area relationships

- `ui/pages/grants.py` - Complete CRUD implementation (437 lines)
  - CREATE form with URL validation and duplicate ID check
  - UPDATE form with URL validation
  - DELETE confirmation showing funded measure links
  - URL validation using `urllib.parse`

**Components (1 file updated):**
- `ui/components/tables.py` - Fixed to handle both integer and string IDs (lines 105-111)
  - Now supports grant IDs (text) and numeric IDs (priorities, habitats, etc.)

**Total Code:** ~1,200+ lines of new/updated code

### 🎯 What's Working

- ✅ CREATE operations with validation for all 3 simple entities
- ✅ UPDATE operations with pre-populated forms
- ✅ DELETE operations with proper cascade handling
- ✅ Confirmation dialogs showing relationship impact before delete
- ✅ URL validation for grants using `urllib.parse.urlparse`
- ✅ Auto-incrementing IDs for priorities and habitats
- ✅ User-provided IDs for grants with duplicate checking
- ✅ Session state management for form visibility
- ✅ Success/error messages for all operations
- ✅ Cancel buttons on all forms
- ✅ Table component handles both integer and string IDs

### 🧪 Testing Completed

All CRUD operations tested and verified working in live app:
- Priority CRUD operations ✓
- Habitat CRUD operations ✓
- Grant CRUD operations ✓
- URL validation on grants ✓
- Cascade deletes following CLAUDE.md specifications ✓

### 📝 Patterns Established

1. **Form Pattern**: Inline forms with `st.form()`, validation, and cancel buttons
2. **Cascade Delete Pattern**: Follow exact order from CLAUDE.md, show impact in confirmation
3. **Session State Pattern**: Use flags for form visibility (`show_create_form`, `show_edit_form`, `show_delete_confirm`)
4. **ID Pattern**: Auto-increment for numeric IDs, user-provided for text IDs
5. **Validation Pattern**: Check required fields, validate URLs, check for duplicates

---

## Next Steps (Phase 3B)

After Phase 3A completion, implement CRUD for complex entities:
1. **Species** - CRUD with taxonomy fields
2. **Areas** - CRUD with funding schemes and multiple relationships
3. **Measures** - CRUD with types, stakeholders, and many relationships (most complex)

Then:
4. Phase 4: Advanced features (bulk operations, import/export)
5. Phase 5: User authentication and authorization
6. Phase 6: Audit logging and history tracking
7. Phase 7: API development for external integrations
