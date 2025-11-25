"""Data Export page - Export relationship data to CSV format."""

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.area import AreaModel
from models.grant import GrantModel
from models.habitat import HabitatModel
from models.measure import MeasureModel
from models.priority import PriorityModel
from models.relationship import RelationshipModel
from models.species import SpeciesModel

# Initialize models
relationship_model = RelationshipModel()
area_model = AreaModel()
priority_model = PriorityModel()
measure_model = MeasureModel()
species_model = SpeciesModel()
grant_model = GrantModel()
habitat_model = HabitatModel()

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

st.markdown("---")

# ==============================================================================
# SECTION 3: CORE AND SUPPORT TABLE EXPORTS
# ==============================================================================

st.header("3. Core and Support Table Exports")
st.markdown(
    "Export core and support tables containing base entities and reference data."
)

# Row 1: Core tables (area, priority, measure)
export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    st.subheader("Area")
    st.caption("Priority areas for biodiversity")
    try:
        area_data = area_model.get_all()
        st.metric("Records", f"{len(area_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"area_{timestamp}.csv"
        csv_data = area_data.write_csv()

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

with export_col2:
    st.subheader("Priority")
    st.caption("Biodiversity priorities and themes")
    try:
        priority_data = priority_model.get_all()
        st.metric("Records", f"{len(priority_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"priority_{timestamp}.csv"
        csv_data = priority_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_priority",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col3:
    st.subheader("Measure")
    st.caption("Conservation measures and recommendations")
    try:
        measure_data = measure_model.get_all()
        st.metric("Records", f"{len(measure_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"measure_{timestamp}.csv"
        csv_data = measure_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_measure",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("")

# Row 2: Core tables continued (species, grants, habitat)
export_col4, export_col5, export_col6 = st.columns(3)

with export_col4:
    st.subheader("Species")
    st.caption("Species of importance with GBIF data")
    try:
        species_data = species_model.get_all()
        st.metric("Records", f"{len(species_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"species_{timestamp}.csv"
        csv_data = species_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_species_table",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col5:
    st.subheader("Grant Table")
    st.caption("Available grants and funding schemes")
    try:
        grant_data = grant_model.get_all()
        st.metric("Records", f"{len(grant_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"grant_table_{timestamp}.csv"
        csv_data = grant_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_grant_table",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col6:
    st.subheader("Habitat")
    st.caption("Habitat types for creation/management")
    try:
        habitat_data = habitat_model.get_all()
        st.metric("Records", f"{len(habitat_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"habitat_{timestamp}.csv"
        csv_data = habitat_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_habitat",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("")

# Row 3: Support tables (measure_type, benefits, area_funding_schemes)
export_col7, export_col8, export_col9 = st.columns(3)

with export_col7:
    st.subheader("Measure Type")
    st.caption("Classification of measure types")
    try:
        measure_type_data = measure_model.get_all_measure_types()
        st.metric("Records", f"{len(measure_type_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"measure_type_{timestamp}.csv"
        csv_data = measure_type_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_measure_type",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col8:
    st.subheader("Benefits")
    st.caption("Benefits delivered by measures")
    try:
        benefits_data = measure_model.get_all_benefits()
        st.metric("Records", f"{len(benefits_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"benefits_{timestamp}.csv"
        csv_data = benefits_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_benefits",
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")

with export_col9:
    st.subheader("Area Funding Schemes")
    st.caption("Funding schemes per area")
    try:
        # Query the area_funding_schemes table directly
        funding_schemes_data = relationship_model.execute_raw_query(
            "SELECT * FROM area_funding_schemes ORDER BY id"
        ).pl()
        st.metric("Records", f"{len(funding_schemes_data):,}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"area_funding_schemes_{timestamp}.csv"
        csv_data = funding_schemes_data.write_csv()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            width="stretch",
            key="export_area_funding_schemes",
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
