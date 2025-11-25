"""Database Schema Visualization page.

Displays interactive ER diagrams of the database schema using Mermaid.js.
"""

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.schema_diagram import (
    SchemaParser,
    generate_mermaid_html,
    get_schema_path,
)

# Custom CSS to maximize vertical space
st.markdown(
    """
    <style>
    /* Reduce padding in main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }

    /* Make iframe take more space */
    iframe {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        min-height: 800px !important;
    }

    /* Reduce spacing in expanders */
    .streamlit-expanderHeader {
        font-size: 14px;
    }

    /* Compact headers */
    h1 {
        padding-top: 0;
        margin-top: 0;
    }

    h2 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading schema...")
def get_schema_parser():
    """Get cached schema parser instance."""
    schema_path = get_schema_path()
    return SchemaParser(schema_path)


@st.cache_data(show_spinner="Generating diagram...")
def generate_diagram(diagram_type: str, include_all_columns: bool) -> str:
    """Generate Mermaid diagram based on type.

    Args:
        diagram_type: Type of diagram to generate
        include_all_columns: Whether to show all columns or just keys

    Returns:
        Mermaid diagram code
    """
    parser = get_schema_parser()

    if diagram_type == "Full Schema":
        return parser.generate_full_diagram(include_all_columns)
    elif diagram_type == "Core Tables":
        return parser.generate_core_diagram(include_all_columns)
    elif diagram_type == "Species & Relationships":
        return parser.generate_domain_diagram("species", include_all_columns)
    elif diagram_type == "Habitats & Areas":
        return parser.generate_domain_diagram("habitat", include_all_columns)
    elif diagram_type == "Grants & Funding":
        return parser.generate_domain_diagram("grant", include_all_columns)
    elif diagram_type == "Measure-Area-Priority Core":
        return parser.generate_domain_diagram(
            "measure-area-priority", include_all_columns
        )
    else:
        return parser.generate_full_diagram(include_all_columns)


# Page header
st.title("🗂️ Database Schema")

# Info expander (collapsed by default to save space)
with st.expander("ℹ️ About the Schema & Controls", expanded=False):
    st.markdown(
        """
    ### Database Architecture

    The LNRS database uses a **normalized 3NF (Third Normal Form)** schema with:

    - **Core Tables**: Main entities (measure, area, priority, species, grant_table, habitat, benefits)
    - **Bridge Tables**: Many-to-many relationships (e.g., `measure_area_priority`, `measure_has_species`)
    - **Dimension Tables**: Lookup tables (e.g., `measure_type`, `stakeholder`)
    - **Geospatial Tables**: Geographic data (`area_geom`)

    ### Diagram Legend

    - **PK**: Primary Key
    - **FK**: Foreign Key
    - **||--o{**: One-to-many relationship
    - **Tables in UPPERCASE**: Entity names

    ### Interactive Features

    - **Zoom Controls**: Use the buttons in the diagram (🔍 Zoom In/Out, ↺ Reset, ⛶ Fit Screen)
    - **Mouse Wheel**: Scroll to zoom in and out
    - **Click & Drag**: Pan around the diagram by clicking and dragging
    - **Double Click**: Quick zoom in on a specific area

    ### Navigation Tips

    - Start with **Core Tables** for an overview
    - Use **domain-specific views** to focus on specific areas
    - Toggle **Show all columns** to see complete table structures
    - Click **Fit Screen** button to auto-size the diagram to your viewport
    """
    )

# Controls
st.subheader("Diagram Options")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    diagram_type = st.selectbox(
        "Select Diagram View",
        [
            "Core Tables",
            "Full Schema",
            "Measure-Area-Priority Core",
            "Species & Relationships",
            "Habitats & Areas",
            "Grants & Funding",
        ],
        index=0,
        help="Choose which part of the schema to visualize",
    )

with col2:
    include_all_columns = st.checkbox(
        "Show all columns",
        value=False,
        help="Show all columns in tables (default: keys only)",
    )

with col3:
    st.markdown("")  # Spacer for alignment

# Generate and display diagram
st.subheader(f"📊 {diagram_type}")

try:
    # Generate Mermaid code
    mermaid_code = generate_diagram(diagram_type, include_all_columns)

    # Prominent full-screen option
    st.info(
        "🖥️ **For best viewing experience:** Download the HTML file below and open it in your browser for true full-screen viewing!"
    )

    # Create tabs for diagram and code
    tab1, tab2, tab3 = st.tabs(["📊 Diagram", "📝 Mermaid Code", "🖥️ Full Screen View"])

    with tab1:
        # Display diagram with interactive controls
        # Use very tall iframe to give plenty of vertical space
        html_code = generate_mermaid_html(mermaid_code, height=1000)
        components.html(html_code, height=2000, scrolling=True)

        st.info(
            "💡 **Controls:** Use the zoom buttons (top-right), mouse wheel to zoom, "
            "click and drag to pan. Click **Fit Screen** for optimal view."
        )

    with tab3:
        st.markdown("### Download Standalone HTML for Full-Screen Viewing")
        st.markdown(
            """
            For the **best viewing experience**, download the HTML file and open it in your browser.
            This gives you:
            - ✅ True full-screen mode
            - ✅ Better zoom and pan performance
            - ✅ No iframe constraints
            - ✅ Easier to navigate large diagrams
            """
        )

        # Generate HTML for download
        download_html = generate_mermaid_html(mermaid_code, height=1000)

        col1, col2 = st.columns([1, 3])
        with col1:
            st.download_button(
                label="📥 Download Full-Screen HTML",
                data=download_html,
                file_name=f"lnrs_schema_{diagram_type.lower().replace(' ', '_')}.html",
                mime="text/html",
                help="Download standalone HTML file for full-screen viewing",
                use_container_width=True,
            )
        with col2:
            st.markdown(
                """
                **Instructions:**
                1. Click the download button
                2. Open the downloaded HTML file in your browser
                3. Use F11 for true full-screen mode
                """
            )

    with tab2:
        # Display raw Mermaid code
        st.code(mermaid_code, language="mermaid")
        st.caption(
            "You can copy this code to use in other Mermaid-compatible tools "
            "(GitHub, GitLab, Notion, etc.)"
        )

except Exception as e:
    st.error(f"Error generating diagram: {e}")
    st.exception(e)

# Download options
st.subheader("💾 Export")

col1, col2 = st.columns(2)

with col1:
    # Download Mermaid code
    mermaid_code_download = generate_diagram(diagram_type, include_all_columns)
    st.download_button(
        label="Download Mermaid Code",
        data=mermaid_code_download,
        file_name=f"lnrs_schema_{diagram_type.lower().replace(' ', '_')}.mmd",
        mime="text/plain",
        help="Download the Mermaid diagram code",
    )

with col2:
    # Download as HTML
    html_download = generate_mermaid_html(mermaid_code_download, height=800)
    st.download_button(
        label="Download as HTML",
        data=html_download,
        file_name=f"lnrs_schema_{diagram_type.lower().replace(' ', '_')}.html",
        mime="text/html",
        help="Download a standalone HTML file with the diagram",
    )

# Footer
st.divider()
st.caption(
    """
    **Schema Source**: `lnrs_3nf_o1_schema.xml` | **Diagram Engine**: Mermaid.js |
    **Relationships**: Auto-inferred from foreign key patterns
    """
)
