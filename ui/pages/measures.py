"""Measures page - View and manage biodiversity measures."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.measure import MeasureModel
from ui.components.tables import display_data_table

# Initialize model
measure_model = MeasureModel()

# Initialize session state
if "measure_view" not in st.session_state:
    st.session_state.measure_view = "list"
if "selected_measure_id" not in st.session_state:
    st.session_state.selected_measure_id = None


def show_list_view():
    """Display list of all measures with types, stakeholders, and counts."""
    st.title("📋 Biodiversity Measures")

    total_count = measure_model.count()
    st.info(f"**{total_count}** measures for biodiversity conservation")

    # Get all measures with relationship counts
    all_measures = measure_model.get_with_relationship_counts()

    def on_view_details(measure_id):
        st.session_state.selected_measure_id = measure_id
        st.session_state.measure_view = "detail"

    display_data_table(
        data=all_measures,
        title="All Measures",
        entity_name="measure",
        id_column="measure_id",
        searchable_columns=["measure", "concise_measure", "types", "stakeholders"],
        column_config={
            "measure_id": st.column_config.NumberColumn("ID", width="small"),
            "measure": st.column_config.TextColumn("Measure", width="large"),
            "concise_measure": st.column_config.TextColumn("Concise", width="large"),
            "core_supplementary": st.column_config.TextColumn("Type", width="small"),
            "mapped_unmapped": st.column_config.TextColumn("Mapped", width="small"),
            "types": st.column_config.TextColumn("Measure Types", width="medium"),
            "stakeholders": st.column_config.TextColumn("Stakeholders", width="medium"),
            "areas": st.column_config.NumberColumn("Areas", width="small"),
            "priorities": st.column_config.NumberColumn("Priorities", width="small"),
            "species": st.column_config.NumberColumn("Species", width="small"),
            "benefits": st.column_config.NumberColumn("Benefits", width="small"),
        },
        show_actions=True,
        on_view_details=on_view_details,
    )


def show_detail_view():
    """Display details of a single measure."""
    measure_id = st.session_state.selected_measure_id

    if measure_id is None:
        st.error("No measure selected")
        if st.button("← Back to List"):
            st.session_state.measure_view = "list"
            st.rerun()
        return

    # Get measure data
    measure_data = measure_model.get_by_id(measure_id)

    if not measure_data:
        st.error(f"Measure ID {measure_id} not found")
        if st.button("← Back to List"):
            st.session_state.measure_view = "list"
            st.rerun()
        return

    # Get related data
    types = measure_model.get_types(measure_id)
    stakeholders = measure_model.get_stakeholders(measure_id)
    related_areas = measure_model.get_related_areas(measure_id)
    related_priorities = measure_model.get_related_priorities(measure_id)
    related_grants = measure_model.get_related_grants(measure_id)
    related_species = measure_model.get_related_species(measure_id)
    benefits = measure_model.get_benefits(measure_id)

    # Get counts
    counts = measure_model.get_relationship_counts(measure_id)

    # Display detail view
    def back_to_list():
        st.session_state.measure_view = "list"
        st.session_state.selected_measure_id = None

    st.title(f"📋 Measure {measure_data['measure_id']}")

    # Back button
    if st.button("← Back to List"):
        back_to_list()
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {measure_data['measure_id']}")

        # Type badge
        if measure_data.get('core_supplementary'):
            if measure_data['core_supplementary'] == 'Core (BNG)':
                st.success(f"🎯 {measure_data['core_supplementary']}")
            else:
                st.info(f"📌 {measure_data['core_supplementary']}")

        st.markdown("**Full Measure:**")
        st.info(measure_data['measure'])

        if measure_data.get('concise_measure'):
            st.markdown("**Concise Description:**")
            st.write(measure_data['concise_measure'])

        if measure_data.get('mapped_unmapped'):
            st.markdown(f"**Mapping Status:** {measure_data['mapped_unmapped']}")

        if measure_data.get('link_to_further_guidance'):
            st.markdown(f"**Guidance:** [{measure_data['link_to_further_guidance']}]({measure_data['link_to_further_guidance']})")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Types", counts['types'])
        st.metric("Stakeholders", counts['stakeholders'])
        st.metric("Areas", counts['areas'])
        st.metric("Priorities", counts['priorities'])
        st.metric("Grants", counts['grants'])
        st.metric("Species", counts['species'])
        st.metric("Benefits", counts['benefits'])

    # Display related data in tabs
    st.markdown("---")
    st.subheader("Related Data")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Types",
        "Stakeholders",
        "Areas",
        "Priorities",
        "Grants",
        "Species",
        "Benefits"
    ])

    with tab1:
        if len(types) > 0:
            st.dataframe(
                types.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "measure_type_id": st.column_config.NumberColumn("ID", width="small"),
                    "measure_type": st.column_config.TextColumn("Measure Type", width="large"),
                },
            )
            st.caption(f"Total: {len(types):,} measure types")
        else:
            st.info("No measure types defined for this measure.")

    with tab2:
        if len(stakeholders) > 0:
            st.dataframe(
                stakeholders.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "stakeholder_id": st.column_config.NumberColumn("ID", width="small"),
                    "stakeholder": st.column_config.TextColumn("Stakeholder", width="large"),
                },
            )
            st.caption(f"Total: {len(stakeholders):,} stakeholders")
        else:
            st.info("No stakeholders defined for this measure.")

    with tab3:
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
            st.info("No areas linked to this measure.")

    with tab4:
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
            st.info("No priorities linked to this measure.")

    with tab5:
        if len(related_grants) > 0:
            st.dataframe(
                related_grants.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "grant_id": st.column_config.NumberColumn("ID", width="small"),
                    "grant_name": st.column_config.TextColumn("Grant Name", width="large"),
                    "grant_scheme": st.column_config.TextColumn("Scheme", width="medium"),
                    "url": st.column_config.LinkColumn("URL", width="small"),
                },
            )
            st.caption(f"Total: {len(related_grants):,} grants")
        else:
            st.info("No grants linked to this measure.")

    with tab6:
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
                    "taxa": st.column_config.TextColumn("Taxa", width="small"),
                },
            )
            st.caption(f"Total: {len(related_species):,} species")
        else:
            st.info("No species linked to this measure.")

    with tab7:
        if len(benefits) > 0:
            st.dataframe(
                benefits.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "benefit_id": st.column_config.NumberColumn("ID", width="small"),
                    "benefit": st.column_config.TextColumn("Benefit", width="large"),
                },
            )
            st.caption(f"Total: {len(benefits):,} benefits")
        else:
            st.info("No benefits linked to this measure.")


# Main page logic
if st.session_state.measure_view == "list":
    show_list_view()
elif st.session_state.measure_view == "detail":
    show_detail_view()
