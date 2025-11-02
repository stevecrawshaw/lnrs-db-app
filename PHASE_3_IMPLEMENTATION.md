# Phase 3 Implementation: Create, Update, Delete Operations

**Goal**: Implement full CRUD operations for all entities
**Duration**: Week 3
**Status**: 🔄 Not Started
**Started**: [To be determined]

---

## Objectives

- [ ] Implement CREATE operations for all entities
- [ ] Implement UPDATE operations for all entities
- [ ] Implement DELETE operations with proper cascade handling
- [ ] Add form validation for all inputs
- [ ] Implement error handling and user feedback
- [ ] Add confirmation dialogs for destructive operations

---

## Task Checklist

### 1. Reusable Form Components
- [ ] Create `ui/components/forms.py` - Form builder with validation
- [ ] Text input with validation
- [ ] Number input with min/max validation
- [ ] Dropdown select for foreign keys
- [ ] Multi-select for many-to-many relationships
- [ ] URL validation for link fields
- [ ] Success/error message components

### 2. CREATE Operations (Ordered by Complexity)

#### Simple Entities (No dependencies)
- [ ] **Priorities** - Create new biodiversity priority
  - Form fields: biodiversity_priority, simplified_biodiversity_priority, theme
  - No dependencies

- [ ] **Habitats** - Create new habitat type
  - Form fields: habitat
  - No dependencies

#### Moderate Entities (Foreign key dependencies)
- [ ] **Grants** - Create new grant/funding scheme
  - Form fields: grant_name, grant_scheme, url, grant_summary
  - URL validation required

- [ ] **Species** - Create new species entry
  - Form fields: common_name, linnaean_name, assemblage, taxa, scientific_name
  - Optional: GBIF integration for taxonomy lookup

- [ ] **Areas** - Create new priority area
  - Form fields: area_name, area_description, area_link
  - Optional: Link to funding schemes

#### Complex Entities (Many-to-many relationships)
- [ ] **Measures** - Create new measure
  - Form fields: measure, concise_measure, core_supplementary, mapped_unmapped, link_to_further_guidance
  - Relationships: types (multi-select), stakeholders (multi-select)
  - Note: Area-Priority linkage comes later

### 3. UPDATE Operations

- [ ] **Priorities** - Edit existing priority
  - Update basic fields
  - Warn if linked to measures/areas/species

- [ ] **Grants** - Edit existing grant
  - Update basic fields
  - URL validation

- [ ] **Habitats** - Edit existing habitat
  - Update basic fields
  - Warn if linked to areas

- [ ] **Areas** - Edit existing area
  - Update basic fields
  - Update funding schemes

- [ ] **Species** - Edit existing species
  - Update taxonomy fields
  - Validate scientific names

- [ ] **Measures** - Edit existing measure
  - Update basic fields
  - Update types and stakeholders (multi-select)

### 4. DELETE Operations (With Cascade Handling)

**CRITICAL**: All delete operations must respect foreign key constraints as documented in CLAUDE.md

- [ ] **Priorities** - Delete with cascade
  - Cascade order:
    1. Delete from `measure_area_priority_grant` where priority_id matches
    2. Delete from `measure_area_priority` where priority_id matches
    3. Delete from `species_area_priority` where priority_id matches
    4. Finally delete from `priority`
  - Confirmation dialog showing impact

- [ ] **Grants** - Delete with cascade
  - Cascade order:
    1. Delete from `measure_area_priority_grant` where grant_id matches
    2. Finally delete from `grant_table`
  - Confirmation dialog

- [ ] **Habitats** - Delete with cascade
  - Cascade order:
    1. Delete from `habitat_creation_area` where habitat_id matches
    2. Delete from `habitat_management_area` where habitat_id matches
    3. Finally delete from `habitat`
  - Confirmation dialog

- [ ] **Areas** - Delete with cascade
  - Cascade order:
    1. Delete from `measure_area_priority_grant` where area_id matches
    2. Delete from `measure_area_priority` where area_id matches
    3. Delete from `species_area_priority` where area_id matches
    4. Delete from `area_funding_schemes` where area_id matches
    5. Delete from `habitat_creation_area` where area_id matches
    6. Delete from `habitat_management_area` where area_id matches
    7. Finally delete from `area`
  - Confirmation dialog showing all relationships

- [ ] **Species** - Delete with cascade
  - Cascade order:
    1. Delete from `species_area_priority` where species_id matches
    2. Delete from `measure_has_species` where species_id matches
    3. Finally delete from `species`
  - Confirmation dialog

- [ ] **Measures** - Delete with cascade
  - Cascade order:
    1. Delete from `measure_has_type` where measure_id matches
    2. Delete from `measure_has_stakeholder` where measure_id matches
    3. Delete from `measure_area_priority_grant` where measure_id matches
    4. Delete from `measure_area_priority` where measure_id matches
    5. Delete from `measure_has_benefits` where measure_id matches
    6. Delete from `measure_has_species` where measure_id matches
    7. Finally delete from `measure`
  - Confirmation dialog showing all relationships

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

### Priority Tests
- [ ] Create new priority
- [ ] Update priority name and theme
- [ ] Delete priority with no relationships
- [ ] Delete priority with relationships (cascade)
- [ ] Validation: Required fields

### Grant Tests
- [ ] Create new grant with URL
- [ ] Update grant details
- [ ] Delete grant
- [ ] Validation: URL format

### Habitat Tests
- [ ] Create new habitat
- [ ] Update habitat name
- [ ] Delete habitat with area links (cascade)

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

✅ Users can create new records for all 6 entities
✅ Users can update existing records
✅ Users can delete records with proper cascade handling
✅ All forms validate inputs correctly
✅ Error messages are clear and helpful
✅ Database integrity is maintained
✅ No orphaned records after deletes

---

**Phase 3 Status**: 🔄 Not Started
**Estimated Duration**: 2-3 weeks
**Priority**: High

---

## Next Steps

After Phase 3 completion:
1. Phase 4: Advanced features (bulk operations, import/export)
2. Phase 5: User authentication and authorization
3. Phase 6: Audit logging and history tracking
4. Phase 7: API development for external integrations
