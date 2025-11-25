# Schema React Embed Implementation Plan

## Problem Statement

The current Mermaid-based ER diagram approach has vertical space constraints within Streamlit's iframe limitations, making it difficult for users to view and navigate the database schema effectively. The downloadable HTML approach is not user-friendly.

## Proposed Solution

Replace the Mermaid implementation with a simple iframe embed of a React-based ERD created in Claude Artifacts. This provides a superior viewing experience with better interactivity and no vertical constraints.

## Implementation Plan

### 1. Create New Schema Page (Simple Embed)

**File:** `ui/pages/schema.py` (replace existing)

**Approach:**
- Use `st.components.v1.iframe()` to embed the Claude artifact
- Provide full-screen height (80vh or similar)
- Keep it simple - no complex diagram generation
- Optional: Add basic controls/info text

**Key Features:**
- ✅ Single iframe embed - no tabs, no complexity
- ✅ Full viewport height utilization
- ✅ React-based ERD with superior UX
- ✅ No vertical scrolling issues
- ✅ No download required
- ✅ Always up-to-date (hosted externally)

### 2. Update or Remove Utility Module

**File:** `utils/schema_diagram.py`

**Options:**

**Option A: Keep as backup**
- Rename to `utils/schema_diagram_mermaid_backup.py`
- Keep for future reference or alternative use
- Remove from active imports

**Option B: Delete entirely**
- Remove the file
- Clean up any references

**Recommendation:** Option A - keep as backup in case we need Mermaid export later

### 3. Code Structure

```python
# ui/pages/schema.py (NEW VERSION)

import streamlit as st
import streamlit.components.v1 as components

# Constants
EMBED_URL = "https://claude.site/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52/embed"
FULL_PAGE_URL = "https://claude.ai/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52"
IFRAME_HEIGHT = 1200

# Custom CSS for better layout
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    iframe {
        width: 100% !important;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🗂️ Database Schema")
st.markdown("Interactive Entity-Relationship diagram of the LNRS database")

# Info section and full-page link
col1, col2 = st.columns([3, 1])

with col1:
    with st.expander("ℹ️ About this diagram"):
        st.markdown("""
        This interactive ER diagram shows the complete structure of the LNRS database.

        **Features:**
        - Interactive zoom and pan
        - Clickable tables to see relationships
        - Modern React-based visualization
        - Full-screen viewing

        **Tables shown:**
        - Core entities (measures, areas, priorities, species, grants, habitats)
        - Bridge tables (many-to-many relationships)
        - Lookup tables
        """)

with col2:
    st.markdown("")  # Spacer
    st.link_button(
        "🔗 Open Full Page",
        FULL_PAGE_URL,
        help="Open diagram in a new tab for full-screen viewing",
        use_container_width=True
    )

# Main diagram section
st.subheader("📊 Database Structure")

# Embed the React ERD
components.iframe(
    src=EMBED_URL,
    height=IFRAME_HEIGHT,
    scrolling=True
)

# Usage tips
st.info("💡 Use mouse wheel to zoom, click and drag to pan. For best experience, click 'Open Full Page' above.")
```

### 4. Styling Considerations

**CSS customizations:**
```python
st.markdown("""
<style>
    /* Maximize viewport for diagram */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }

    /* Full width iframe */
    iframe {
        width: 100% !important;
        min-height: 900px;
    }
</style>
""", unsafe_allow_html=True)
```

### 5. Navigation Updates

**File:** `app.py`

**No changes needed** - the schema page is already registered in navigation
- Schema page already exists as: `st.Page("ui/pages/schema.py", title="Schema", icon="🗂️")`
- Already in navigation under "Main": `[home_page, schema_page]`

### 6. Testing Plan

**Manual Tests:**
1. ✅ Navigate to Schema page
2. ✅ Verify iframe loads correctly
3. ✅ Test zoom and pan interactions
4. ✅ Verify full viewport utilization
5. ✅ Test on different screen sizes
6. ✅ Verify no vertical scrolling issues

**Browser Tests:**
- Chrome
- Firefox
- Safari (if available)
- Edge

### 7. Deployment Considerations

**Pros of this approach:**
- ✅ **Simple** - Just an iframe, no complex code
- ✅ **External hosting** - Claude handles the React app
- ✅ **No maintenance** - Schema updates can be done in Claude artifact
- ✅ **Better UX** - React provides superior interactivity
- ✅ **No dependencies** - No Mermaid, no svg-pan-zoom libraries
- ✅ **No vertical constraints** - React app handles its own layout

**Cons to consider:**
- ⚠️ **External dependency** - Relies on claude.site being available
- ⚠️ **Network required** - Won't work offline
- ⚠️ **Static URL** - If artifact changes, URL must be updated
- ⚠️ **No auto-sync** - Schema changes require manual artifact update

**Mitigations:**
- Document the artifact URL in CLAUDE.md
- Add fallback message if iframe fails to load
- Keep Mermaid code as backup option

### 8. Documentation Updates

**File:** `CLAUDE.md`

Add section:
```markdown
## Schema Visualization

The database schema is visualized using a React-based ERD hosted as a Claude artifact.

**Artifact URL:** https://claude.site/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52/embed

**To update the schema diagram:**
1. Edit the React artifact at Claude
2. Update the embed URL in `ui/pages/schema.py` if artifact ID changes
3. No deployment needed - changes reflect immediately

**Backup approach:**
The Mermaid-based schema generator is preserved in `utils/schema_diagram_mermaid_backup.py`
for export or alternative visualization needs.
```

### 9. File Changes Summary

**Files to modify:**
- ✅ `ui/pages/schema.py` - Complete rewrite (simple iframe embed)
- ✅ `CLAUDE.md` - Add schema artifact documentation

**Files to rename (backup):**
- ✅ `utils/schema_diagram.py` → `utils/schema_diagram_mermaid_backup.py`

**Files unchanged:**
- ✅ `app.py` - No changes needed (page already registered)

**Files to potentially remove:**
- ❌ None (keep everything as backup)

### 10. Implementation Steps

**Step 1:** Backup current implementation
```bash
cp ui/pages/schema.py ui/pages/schema_mermaid_backup.py
mv utils/schema_diagram.py utils/schema_diagram_mermaid_backup.py
```

**Step 2:** Create new simple schema.py with iframe embed

**Step 3:** Test in local environment
```bash
streamlit run app.py
```

**Step 4:** Verify all functionality

**Step 5:** Update documentation (CLAUDE.md)

**Step 6:** Commit changes

### 11. Rollback Plan

If the React embed approach doesn't work:

1. Restore previous version:
   ```bash
   cp ui/pages/schema_mermaid_backup.py ui/pages/schema.py
   mv utils/schema_diagram_mermaid_backup.py utils/schema_diagram.py
   ```

2. Alternative: Improve Mermaid with iframe sandbox attributes

3. Alternative: Explore dbdiagram.io or other hosted ERD services

### 12. Future Enhancements (Optional)

**If React approach works well:**

1. **Add view controls:**
   - Buttons to focus on specific domains (species, habitats, grants)
   - Toggle between full schema and core tables
   - Requires React artifact to support query parameters

2. **Fallback handling:**
   ```python
   try:
       components.iframe(src=SCHEMA_URL, height=1000)
   except Exception as e:
       st.error("Unable to load schema diagram")
       st.info("Contact admin or view backup Mermaid diagram")
   ```

3. **Performance monitoring:**
   - Track if iframe loads successfully
   - Log errors for debugging

## Estimated Complexity

- **Implementation Time:** 15-30 minutes
- **Testing Time:** 10-15 minutes
- **Complexity Level:** LOW (simple iframe embed)
- **Risk Level:** LOW (easy to rollback)

## Recommendation

✅ **PROCEED with this implementation**

This approach is:
- Much simpler than Mermaid
- Solves the vertical constraint problem
- Provides better UX
- Easy to implement and maintain
- Low risk with easy rollback

## Questions & Answers - CONFIRMED ✅

1. **Is the React artifact URL permanent or will it change?**
   - ✅ **CONFIRMED:** Artifact URL is permanent

2. **Should we keep Mermaid code as backup?**
   - ✅ **CONFIRMED:** Yes, keep Mermaid code as backup

3. **What height should the iframe be?**
   - ✅ **CONFIRMED:** Use suggested height (1000-1200px), may need adjustment later

4. **Do you want any controls/options, or just a simple embed?**
   - ✅ **CONFIRMED:** Simple embed to start, **PLUS** include link to full-page version
   - **Full-page URL:** https://claude.ai/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52

5. **Should we handle offline/network error cases?**
   - ⚠️ Nice to have, but not required for initial implementation

---

## Updated Requirements

Based on user feedback, the implementation will include:

1. **Primary feature:** Simple iframe embed of React ERD
2. **Secondary feature:** "Open in full page" button/link that opens the artifact in a new tab
3. **Backup:** Keep Mermaid implementation as fallback
4. **Height:** Start with 1000-1200px, adjustable if needed

**Status: APPROVED - Ready to implement**
