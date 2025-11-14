"""Database Schema Visualization page.

Displays interactive ER diagram using React-based visualization hosted as Claude artifact.
"""

import streamlit as st
import streamlit.components.v1 as components

# Constants
EMBED_URL = "https://claude.site/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52/embed"
FULL_PAGE_URL = "https://claude.ai/public/artifacts/63e84958-e21f-4fcc-b550-cc0ac63c5a52"
IFRAME_HEIGHT = 1200

# Custom CSS for better layout
st.markdown(
    """
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
    /* Align expander and button vertically */
    [data-testid="column"] {
        display: flex;
        align-items: flex-start;
    }
    [data-testid="column"] > div {
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Title and description
st.title("🗂️ Database Schema")
st.markdown("Interactive Entity-Relationship diagram of the LNRS database")

# Info section and full-page link
col1, col2 = st.columns([3, 1])

with col1:
    with st.expander("ℹ️ About this diagram"):
        st.markdown(
            """
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

        **Database Architecture:**
        - **23 total tables** (20 tables + 3 views)
        - **10 core entity tables** (measure, area, priority, species, etc.)
        - **10 bridge tables** for many-to-many relationships
        - **3NF normalized** schema for data integrity
        """
        )

with col2:
    st.link_button(
        "🔗 Open Full Page",
        FULL_PAGE_URL,
        help="Open diagram in a new tab for full-screen viewing",
        use_container_width=True,
    )

# Main diagram section
st.subheader("📊 Database Structure")

# Embed the React ERD
components.iframe(src=EMBED_URL, height=IFRAME_HEIGHT, scrolling=True)

# Usage tips
st.info(
    "💡 **Tip:** Use mouse wheel to zoom, click and drag to pan. "
    "For the best viewing experience, click **'Open Full Page'** above."
)

# Footer with additional info
st.divider()
st.caption(
    """
    **Visualization:** React-based ERD hosted on Claude Artifacts |
    **Backup:** Mermaid-based schema generator available in `utils/schema_diagram_mermaid_backup.py`
    """
)
