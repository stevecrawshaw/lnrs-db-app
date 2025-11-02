"""Species page - View and manage species data."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.species import SpeciesModel
from ui.components.tables import display_data_table

# Initialize model
species_model = SpeciesModel()

# Initialize session state
if "species_view" not in st.session_state:
    st.session_state.species_view = "list"
if "selected_species_id" not in st.session_state:
    st.session_state.selected_species_id = None


def show_list_view():
    """Display list of all species with taxonomy."""
    st.title("🦋 Species")

    total_count = species_model.count()
    st.info(f"**{total_count}** species with GBIF taxonomy data")

    # Get all species
    all_species = species_model.get_all(order_by="common_name")

    def on_view_details(species_id):
        st.session_state.selected_species_id = species_id
        st.session_state.species_view = "detail"

    display_data_table(
        data=all_species,
        title="All Species",
        entity_name="species",
        id_column="species_id",
        searchable_columns=["common_name", "scientific_name", "assemblage", "taxa"],
        column_config={
            "species_id": st.column_config.NumberColumn("ID", width="small"),
            "common_name": st.column_config.TextColumn("Common Name", width="medium"),
            "linnaean_name": st.column_config.TextColumn("Linnaean Name", width="medium"),
            "scientific_name": st.column_config.TextColumn("Scientific Name", width="medium"),
            "assemblage": st.column_config.TextColumn("Assemblage", width="medium"),
            "taxa": st.column_config.TextColumn("Taxa", width="small"),
            "kingdom": st.column_config.TextColumn("Kingdom", width="small"),
            "phylum": st.column_config.TextColumn("Phylum", width="small"),
            "class": st.column_config.TextColumn("Class", width="small"),
            "order": st.column_config.TextColumn("Order", width="small"),
            "family": st.column_config.TextColumn("Family", width="small"),
            "genus": st.column_config.TextColumn("Genus", width="small"),
            "species_link": st.column_config.LinkColumn("Info Link", width="small"),
            "gbif_species_url": st.column_config.LinkColumn("GBIF", width="small"),
        },
        show_actions=True,
        on_view_details=on_view_details,
    )


def show_detail_view():
    """Display details of a single species."""
    species_id = st.session_state.selected_species_id

    if species_id is None:
        st.error("No species selected")
        if st.button("← Back to List"):
            st.session_state.species_view = "list"
            st.rerun()
        return

    # Get species data
    species_data = species_model.get_by_id(species_id)

    if not species_data:
        st.error(f"Species ID {species_id} not found")
        if st.button("← Back to List"):
            st.session_state.species_view = "list"
            st.rerun()
        return

    # Get related data
    related_measures = species_model.get_related_measures(species_id)
    related_areas = species_model.get_related_areas(species_id)
    related_priorities = species_model.get_related_priorities(species_id)

    # Get counts
    counts = species_model.get_relationship_counts(species_id)

    # Display detail view
    def back_to_list():
        st.session_state.species_view = "list"
        st.session_state.selected_species_id = None

    st.title(f"🦋 {species_data['common_name']}")

    # Back button
    if st.button("← Back to List"):
        back_to_list()
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {species_data['species_id']}")
        st.markdown(f"**Common Name:** {species_data['common_name']}")
        st.markdown(f"**Scientific Name:** {species_data['scientific_name']}")
        st.markdown(f"**Linnaean Name:** {species_data['linnaean_name']}")

        if species_data.get('assemblage'):
            st.markdown(f"**Assemblage:** {species_data['assemblage']}")

        if species_data.get('taxa'):
            st.markdown(f"**Taxa:** {species_data['taxa']}")

        st.markdown(f"**Status:** {species_data.get('status', 'N/A')}")

        # Links
        if species_data.get('species_link'):
            st.markdown(f"**Info:** [{species_data['species_link']}]({species_data['species_link']})")

        if species_data.get('gbif_species_url'):
            st.markdown(f"**GBIF:** [{species_data['gbif_species_url']}]({species_data['gbif_species_url']})")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Measures", counts['measures'])
        st.metric("Areas", counts['areas'])
        st.metric("Priorities", counts['priorities'])

    # Display taxonomy
    st.markdown("---")
    st.subheader("Taxonomy")

    tax_col1, tax_col2, tax_col3 = st.columns(3)

    with tax_col1:
        st.markdown(f"**Kingdom:** {species_data.get('kingdom', 'N/A')}")
        st.markdown(f"**Phylum:** {species_data.get('phylum', 'N/A')}")

    with tax_col2:
        st.markdown(f"**Class:** {species_data.get('class', 'N/A')}")
        st.markdown(f"**Order:** {species_data.get('order', 'N/A')}")

    with tax_col3:
        st.markdown(f"**Family:** {species_data.get('family', 'N/A')}")
        st.markdown(f"**Genus:** {species_data.get('genus', 'N/A')}")

    # Display related data in tabs
    st.markdown("---")
    st.subheader("Related Data")

    tab1, tab2, tab3 = st.tabs(["Measures", "Areas", "Priorities"])

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
            st.info("No measures linked to this species.")

    with tab2:
        if len(related_areas) > 0:
            st.dataframe(
                related_areas.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn("Area Name", width="medium"),
                    "area_description": st.column_config.TextColumn("Description", width="large"),
                },
            )
            st.caption(f"Total: {len(related_areas):,} areas")
        else:
            st.info("No areas linked to this species.")

    with tab3:
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
            st.info("No priorities linked to this species.")


# Main page logic
if st.session_state.species_view == "list":
    show_list_view()
elif st.session_state.species_view == "detail":
    show_detail_view()
