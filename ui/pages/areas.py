"""Areas page - View and manage priority areas."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.area import AreaModel
from ui.components.tables import display_data_table

# Initialize model
area_model = AreaModel()

# Initialize session state
if "area_view" not in st.session_state:
    st.session_state.area_view = "list"
if "selected_area_id" not in st.session_state:
    st.session_state.selected_area_id = None


def show_list_view():
    """Display list of all areas with relationship counts."""
    st.title("🗺️ Priority Areas")

    total_count = area_model.count()
    st.info(f"**{total_count}** priority areas for biodiversity conservation")

    # Get areas with relationship counts
    areas_with_counts = area_model.get_with_relationship_counts()

    def on_view_details(area_id):
        st.session_state.selected_area_id = area_id
        st.session_state.area_view = "detail"

    display_data_table(
        data=areas_with_counts,
        title="All Areas",
        entity_name="area",
        id_column="area_id",
        searchable_columns=["area_name", "area_description"],
        column_config={
            "area_id": st.column_config.NumberColumn("ID", width="small"),
            "area_name": st.column_config.TextColumn("Area Name", width="medium"),
            "area_description": st.column_config.TextColumn("Description", width="large"),
            "area_link": st.column_config.LinkColumn("Link", width="small"),
            "measures": st.column_config.NumberColumn("Measures", width="small"),
            "priorities": st.column_config.NumberColumn("Priorities", width="small"),
            "species": st.column_config.NumberColumn("Species", width="small"),
            "creation_habitats": st.column_config.NumberColumn("Creation", width="small"),
            "management_habitats": st.column_config.NumberColumn("Management", width="small"),
            "funding_schemes": st.column_config.NumberColumn("Funding", width="small"),
        },
        show_actions=True,
        on_view_details=on_view_details,
    )


def show_detail_view():
    """Display details of a single area."""
    area_id = st.session_state.selected_area_id

    if area_id is None:
        st.error("No area selected")
        if st.button("← Back to List"):
            st.session_state.area_view = "list"
            st.rerun()
        return

    # Get area data
    area_data = area_model.get_by_id(area_id)

    if not area_data:
        st.error(f"Area ID {area_id} not found")
        if st.button("← Back to List"):
            st.session_state.area_view = "list"
            st.rerun()
        return

    # Get related data
    related_measures = area_model.get_measures(area_id)
    related_priorities = area_model.get_priorities(area_id)
    related_species = area_model.get_species(area_id)
    creation_habitats = area_model.get_creation_habitats(area_id)
    management_habitats = area_model.get_management_habitats(area_id)
    funding_schemes = area_model.get_funding_schemes(area_id)

    # Get counts
    counts = area_model.get_relationship_counts(area_id)

    # Display detail view
    def back_to_list():
        st.session_state.area_view = "list"
        st.session_state.selected_area_id = None

    st.title(f"🗺️ {area_data['area_name']}")

    # Back button
    if st.button("← Back to List"):
        back_to_list()
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {area_data['area_id']}")
        st.markdown("**Description:**")
        st.info(area_data['area_description'])

        if area_data.get('area_link'):
            st.markdown(f"**Link:** [{area_data['area_link']}]({area_data['area_link']})")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Measures", counts['measures'])
        st.metric("Priorities", counts['priorities'])
        st.metric("Species", counts['species'])
        st.metric("Creation Habitats", counts['creation_habitats'])
        st.metric("Management Habitats", counts['management_habitats'])
        st.metric("Funding Schemes", counts['funding_schemes'])

    # Display related data in tabs
    st.markdown("---")
    st.subheader("Related Data")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Measures",
        "Priorities",
        "Species",
        "Creation Habitats",
        "Management Habitats",
        "Funding Schemes"
    ])

    with tab1:
        if len(related_measures) > 0:
            st.dataframe(
                related_measures.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "measure_id": st.column_config.NumberColumn("ID", width="small"),
                    "measure": st.column_config.TextColumn("Measure", width="large"),
                    "concise_measure": st.column_config.TextColumn("Concise", width="medium"),
                    "core_supplementary": st.column_config.TextColumn("Type", width="small"),
                },
            )
            st.caption(f"Total: {len(related_measures):,} measures")
        else:
            st.info("No measures linked to this area.")

    with tab2:
        if len(related_priorities) > 0:
            st.dataframe(
                related_priorities.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "priority_id": st.column_config.NumberColumn("ID", width="small"),
                    "biodiversity_priority": st.column_config.TextColumn(
                        "Biodiversity Priority", width="large"
                    ),
                    "simplified_biodiversity_priority": st.column_config.TextColumn(
                        "Simplified", width="medium"
                    ),
                    "theme": st.column_config.TextColumn("Theme", width="medium"),
                },
            )
            st.caption(f"Total: {len(related_priorities):,} priorities")
        else:
            st.info("No priorities linked to this area.")

    with tab3:
        if len(related_species) > 0:
            st.dataframe(
                related_species.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "species_id": st.column_config.NumberColumn("ID", width="small"),
                    "common_name": st.column_config.TextColumn("Common Name", width="medium"),
                    "linnaean_name": st.column_config.TextColumn("Scientific Name", width="medium"),
                    "assemblage": st.column_config.TextColumn("Assemblage", width="medium"),
                    "usage_key": st.column_config.TextColumn("GBIF Key", width="small"),
                },
            )
            st.caption(f"Total: {len(related_species):,} species")
        else:
            st.info("No species linked to this area.")

    with tab4:
        if len(creation_habitats) > 0:
            st.dataframe(
                creation_habitats.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "habitat_id": st.column_config.NumberColumn("ID", width="small"),
                    "habitat": st.column_config.TextColumn("Habitat Type", width="large"),
                },
            )
            st.caption(f"Total: {len(creation_habitats):,} habitats designated for creation")
        else:
            st.info("No habitats designated for creation in this area.")

    with tab5:
        if len(management_habitats) > 0:
            st.dataframe(
                management_habitats.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "habitat_id": st.column_config.NumberColumn("ID", width="small"),
                    "habitat": st.column_config.TextColumn("Habitat Type", width="large"),
                },
            )
            st.caption(f"Total: {len(management_habitats):,} habitats requiring management")
        else:
            st.info("No habitats requiring management in this area.")

    with tab6:
        if len(funding_schemes) > 0:
            st.dataframe(
                funding_schemes.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn("Area", width="medium"),
                    "local_funding_schemes": st.column_config.TextColumn("Funding Schemes", width="large"),
                },
            )
            st.caption(f"Total: {len(funding_schemes):,} funding schemes")
        else:
            st.info("No funding schemes available for this area.")


# Main page logic
if st.session_state.area_view == "list":
    show_list_view()
elif st.session_state.area_view == "detail":
    show_detail_view()
