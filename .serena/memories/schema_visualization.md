# Schema Visualization

## Overview

The LNRS database schema is visualized using an interactive React-based Entity-Relationship (ER) diagram hosted as a Claude artifact. This provides users with a visual understanding of the database structure, relationships, and table organization.

## Implementation Details

### Page Location
- **File**: `ui/pages/schema.py`
- **Navigation**: Main → Schema (🗂️ icon)
- **Implementation**: Simple iframe embed (~94 lines, 68.7% smaller than previous Mermaid version)

### React Artifact URLs

**Embed URL** (used in app):
```
https://claude.site/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52/embed
```

**Full-page URL** (for new tab viewing):
```
https://claude.ai/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52
```

### Features

1. **Interactive Controls**
   - Zoom in/out with mouse wheel
   - Click and drag to pan
   - Color-coded table types:
     - Blue: Entity tables (core data)
     - Green: Junction tables (relationships)
     - Purple: Support tables
   - Clickable tables to highlight relationships

2. **UI Components**
   - Info expander: Database architecture details
   - "Open Full Page" button: Opens artifact in new browser tab
   - 1200px iframe height for optimal viewing
   - Scrolling enabled for navigation

3. **Layout**
   - Two-column layout (3:1 ratio)
   - Left: Info expander
   - Right: Full-page link button
   - Full-width diagram display
   - Clean CSS styling with borders

### Code Structure

```python
# Constants
EMBED_URL = "https://claude.site/public/artifacts/.../embed"
FULL_PAGE_URL = "https://claude.ai/public/artifacts/..."
IFRAME_HEIGHT = 1200

# Main implementation
components.iframe(src=EMBED_URL, height=IFRAME_HEIGHT, scrolling=True)

# Full-page link
st.link_button("🔗 Open Full Page", FULL_PAGE_URL, ...)
```

## Database Schema Information

The diagram visualizes:
- **23 total tables** (20 tables + 3 views)
- **10 core entity tables**: measure, area, priority, species, grant_table, habitat, benefits, measure_type, stakeholder, area_funding_schemes
- **10 bridge tables**: measure_has_type, measure_has_stakeholder, measure_area_priority, measure_area_priority_grant, species_area_priority, measure_has_benefits, measure_has_species, habitat_creation_area, habitat_management_area, area_funding_schemes
- **3 views**: source_table, source_table_recreated_vw, apmg_slim_vw
- **3NF normalized** schema for data integrity

### Table Relationships

Key relationships shown:
- **measure ↔ area ↔ priority**: Core three-way relationship (measure_area_priority)
- **measure → types**: One-to-many via measure_has_type
- **measure → stakeholders**: One-to-many via measure_has_stakeholder
- **measure → species**: Many-to-many via measure_has_species
- **measure → benefits**: Many-to-many via measure_has_benefits
- **area → habitats**: Many-to-many via habitat_creation_area and habitat_management_area
- **species ↔ area ↔ priority**: Three-way relationship (species_area_priority)
- **grants**: Linked via measure_area_priority_grant

## Updating the Diagram

When the database schema changes:

1. **Edit React Artifact**
   - Navigate to: https://claude.ai/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52
   - Make changes to the React component
   - Update tables, relationships, or styling as needed

2. **Changes Reflect Immediately**
   - No deployment required
   - Changes appear instantly in the embedded version
   - Users see updated diagram on next page load

3. **If Artifact ID Changes**
   - Update constants in `ui/pages/schema.py`:
     ```python
     EMBED_URL = "new_embed_url"
     FULL_PAGE_URL = "new_full_page_url"
     ```

## Backup Implementation

### Mermaid Version (Deprecated but Preserved)

**Files preserved as backup:**
- `ui/pages/schema_mermaid_backup.py`: Old Mermaid-based schema page
- `utils/schema_diagram_mermaid_backup.py`: Mermaid diagram generator utility

**Capabilities:**
- Generates Mermaid ER diagram syntax from `lnrs_3nf_o1_schema.xml`
- Automatically infers primary and foreign keys
- Identifies bridge tables for many-to-many relationships
- Creates multiple diagram views:
  - Full schema
  - Core tables only
  - Domain-specific (species, habitats, grants, etc.)
- Exports Mermaid code and standalone HTML files

**Use Cases for Backup:**
- Offline schema visualization
- Generating static diagram exports
- Alternative visualization format
- Automatic diagram generation when schema XML changes

### Schema XML Source

**File**: `lnrs_3nf_o1_schema.xml`

Contains complete schema definition:
- All 23 tables with columns
- Column types and nullable constraints
- No explicit foreign key definitions (inferred from column names)

## Advantages of React Approach

**vs. Mermaid:**
1. ✅ **Superior UX**: Better interactivity, smoother zoom/pan
2. ✅ **No vertical constraints**: Full-screen capable in browser
3. ✅ **External hosting**: No maintenance overhead
4. ✅ **Simpler code**: 94 lines vs 240+ lines
5. ✅ **Color-coded**: Visual distinction between table types
6. ✅ **Clickable**: Highlight relationships on table click

**Trade-offs:**
1. ⚠️ **External dependency**: Requires claude.site availability
2. ⚠️ **Network required**: Won't work offline
3. ⚠️ **Manual updates**: Schema changes require artifact editing

## User Documentation

**Locations:**
- **README.md**: Section on Database Architecture → Schema Overview
- **CLAUDE.md**: Section on Schema Visualization with implementation details
- **In-app**: Info expander on Schema page

**User Instructions:**
1. Navigate to 🗂️ Schema in sidebar (under "Main")
2. Use mouse wheel to zoom in/out
3. Click and drag to pan around diagram
4. Click tables to highlight relationships
5. Use "🔗 Open Full Page" button for full-screen viewing in browser

## Deployment Considerations

### Local Development
- ✅ Works perfectly (network required)
- ✅ No filesystem dependencies
- ✅ Fast loading (external CDN)

### Streamlit Cloud
- ✅ Works in production
- ✅ No special configuration needed
- ✅ Artifact URL is permanent
- ⚠️ Requires internet connectivity

### MotherDuck Mode
- ✅ Compatible (schema visualization is independent of database connection)
- ✅ Same artifact works for both local and cloud modes

## Future Enhancements

Potential improvements:
1. **Query parameters**: Pass view type to React artifact (full/core/domain)
2. **Schema sync**: Auto-detect schema changes and highlight differences
3. **Export options**: Screenshot/PDF generation from diagram
4. **Search/filter**: Find specific tables or relationships
5. **Relationship paths**: Highlight connection paths between tables
