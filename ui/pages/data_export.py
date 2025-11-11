"""Data Export page - Export relationship data to CSV format."""

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.relationship import RelationshipModel

# Initialize model
relationship_model = RelationshipModel()

# ==============================================================================
# PAGE CONTENT
# ==============================================================================

st.title("📊 Data Export")
st.markdown(
    """
    Export relationship data to CSV format for external analysis and reporting.
    All exports include timestamps in filenames for version tracking.
    """
)

# ==============================================================================
# SECTION 1: APMG SLIM VIEW EXPORT
# ==============================================================================

st.header("1. APMG Slim View Export")
st.markdown(
    """
    Export the **Area-Priority-Measure-Grant (APMG)** denormalized view containing
    all core relationships in a single table. This view recreates the original source
    table structure with all relationships expanded.
    """
)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Columns included:**")
    st.markdown(
        """
        - Core/Supplementary indicator, Measure type, Stakeholder
        - Area name and ID
        - Priority and ID, Biodiversity priority description
        - Measure details (full and concise descriptions)
        - Grant information (ID, name, URL)
        - Link to further guidance
        """
    )

with col2:
    # Get record count
    try:
        with st.spinner("Loading data..."):
            apmg_data = relationship_model.get_apmg_slim_view()
            record_count = len(apmg_data)

        st.metric("Total Records", f"{record_count:,}")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"apmg_slim_export_{timestamp}.csv"

        # Convert to CSV
        csv_data = apmg_data.write_csv()

        # Download button
        st.download_button(
            label="📥 Download APMG CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            type="primary",
            width="stretch",
        )

        st.caption(f"Filename: `{filename}`")

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")

st.markdown("---")

# ==============================================================================
# SECTION 2: BRIDGE TABLE EXPORTS
# ==============================================================================

st.header("2. Bridge Table Exports")
st.markdown("Export individual bridge table data for specific relationship types.")

export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    st.subheader("Measure-Area-Priority")
    st.caption("Core relationships between measures, areas, and priorities")
    try:
        map_data = relationship_model.get_all_measure_area_priority()
        st.metric("Records", f"{len(map_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"measure_area_priority_{timestamp}.csv"
        csv_data = map_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_map",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col2:
    st.subheader("Grant Funding")
    st.caption("Links grants to measure-area-priority combinations")
    try:
        grant_data = relationship_model.get_all_measure_area_priority_grants()
        st.metric("Records", f"{len(grant_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"measure_area_priority_grant_{timestamp}.csv"
        csv_data = grant_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_grant",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col3:
    st.subheader("Species-Area-Priority")
    st.caption("Links species to areas and priorities")
    try:
        species_data = relationship_model.get_all_species_area_priority()
        st.metric("Records", f"{len(species_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"species_area_priority_{timestamp}.csv"
        csv_data = species_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_species",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("")
export_col4, export_col5, export_col6 = st.columns(3)

with export_col4:
    st.subheader("Habitat Creation")
    st.caption("Habitats designated for creation in areas")
    try:
        habitat_creation_data = relationship_model.get_all_habitat_creation_areas()
        st.metric("Records", f"{len(habitat_creation_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"habitat_creation_area_{timestamp}.csv"
        csv_data = habitat_creation_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_habitat_creation",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col5:
    st.subheader("Habitat Management")
    st.caption("Habitats requiring management in areas")
    try:
        habitat_management_data = relationship_model.get_all_habitat_management_areas()
        st.metric("Records", f"{len(habitat_management_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"habitat_management_area_{timestamp}.csv"
        csv_data = habitat_management_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_habitat_management",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col6:
    st.subheader("Unfunded Links")
    st.caption("Measure-area-priority links without grants")
    try:
        unfunded_data = relationship_model.get_unfunded_measure_area_priority_links()
        st.metric("Records", f"{len(unfunded_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"unfunded_links_{timestamp}.csv"
        csv_data = unfunded_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_unfunded",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ==============================================================================
# FOOTER
# ==============================================================================

st.markdown("---")
st.info(
    """
    **💡 Tip**: All exported files include timestamps
    in their filenames (YYYY-MM-DD_HHMMSS)
    to prevent overwrites and track versions.
    """
)
