"""Priorities page - View and manage biodiversity priorities."""

import sys
from pathlib import Path

import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.priority import PriorityModel
from ui.components.tables import display_data_table, display_detail_view, display_grouped_table

# Initialize model
priority_model = PriorityModel()

# Initialize session state
if "priority_view" not in st.session_state:
    st.session_state.priority_view = "list"
if "selected_priority_id" not in st.session_state:
    st.session_state.selected_priority_id = None


def show_list_view():
    """Display list of all priorities."""
    st.title("🎯 Biodiversity Priorities")

    total_count = priority_model.count()
    st.info(f"**{total_count}** biodiversity priorities organized by themes")

    # View options
    view_mode = st.radio(
        "View Mode",
        ["Grouped by Theme", "All Priorities (Table)"],
        horizontal=True,
    )

    if view_mode == "Grouped by Theme":
        # Get priorities grouped by theme
        by_theme = priority_model.get_by_theme()

        for theme, priorities in by_theme.items():
            # Clean theme name (remove non-breaking spaces and other whitespace)
            clean_theme = theme.strip().replace('\xa0', '')

            with st.expander(
                f"**{clean_theme}** ({len(priorities)} priorities)",
                expanded=True,
            ):
                # Display priorities in this theme
                priorities_display = priorities.select([
                    "priority_id",
                    "biodiversity_priority",
                    "simplified_biodiversity_priority",
                ])

                st.dataframe(
                    priorities_display.to_pandas(),
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
                    },
                )

    else:
        # Show all priorities as a single table
        all_priorities = priority_model.get_all(order_by="theme, biodiversity_priority")

        # Clean theme names in the dataframe
        all_priorities = all_priorities.with_columns(
            pl.col("theme").str.strip_chars().str.replace_all('\xa0', '')
        )

        def on_view_details(priority_id):
            st.session_state.selected_priority_id = priority_id
            st.session_state.priority_view = "detail"

        display_data_table(
            data=all_priorities,
            title="All Priorities",
            entity_name="priority",
            id_column="priority_id",
            searchable_columns=["biodiversity_priority", "simplified_biodiversity_priority", "theme"],
            column_config={
                "priority_id": st.column_config.NumberColumn("ID", width="small"),
                "biodiversity_priority": st.column_config.TextColumn(
                    "Biodiversity Priority", width="large"
                ),
                "simplified_biodiversity_priority": st.column_config.TextColumn(
                    "Simplified", width="medium"
                ),
                "theme": st.column_config.TextColumn("Theme", width="large"),
            },
            show_actions=True,
            on_view_details=on_view_details,
        )


def show_detail_view():
    """Display details of a single priority."""
    priority_id = st.session_state.selected_priority_id

    if priority_id is None:
        st.error("No priority selected")
        if st.button("← Back to List"):
            st.session_state.priority_view = "list"
            st.rerun()
        return

    # Get priority data
    priority_data = priority_model.get_by_id(priority_id)

    if not priority_data:
        st.error(f"Priority ID {priority_id} not found")
        if st.button("← Back to List"):
            st.session_state.priority_view = "list"
            st.rerun()
        return

    # Get related data
    related_measures = priority_model.get_related_measures(priority_id)
    related_areas = priority_model.get_related_areas(priority_id)
    related_species = priority_model.get_related_species(priority_id)

    # Get counts
    counts = priority_model.get_relationship_counts(priority_id)

    # Display detail view
    def back_to_list():
        st.session_state.priority_view = "list"
        st.session_state.selected_priority_id = None

    st.title(f"🎯 Priority Details")

    # Back button
    if st.button("← Back to List"):
        back_to_list()
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {priority_data['priority_id']}")
        # Clean theme name for display
        clean_theme = priority_data['theme'].strip().replace('\xa0', '')
        st.markdown(f"**Theme:** {clean_theme}")
        st.markdown("**Biodiversity Priority:**")
        st.info(priority_data['biodiversity_priority'])

    with col2:
        st.markdown("**Simplified:**")
        if priority_data['simplified_biodiversity_priority']:
            st.write(priority_data['simplified_biodiversity_priority'])
        else:
            st.caption("_Not provided_")

        st.markdown("---")
        st.markdown("**Relationship Counts:**")
        st.metric("Measures", counts['measures'])
        st.metric("Areas", counts['areas'])
        st.metric("Species", counts['species'])

    # Display related data in tabs
    st.markdown("---")
    st.subheader("Related Data")

    tab1, tab2, tab3 = st.tabs(["Measures", "Areas", "Species"])

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
            st.info("No measures linked to this priority.")

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
            st.info("No areas linked to this priority.")

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
                },
            )
            st.caption(f"Total: {len(related_species):,} species")
        else:
            st.info("No species linked to this priority.")


# Main page logic
if st.session_state.priority_view == "list":
    show_list_view()
elif st.session_state.priority_view == "detail":
    show_detail_view()
