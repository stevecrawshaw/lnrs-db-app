"""Habitats page - View habitat types and their areas."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.habitat import HabitatModel
from ui.components.tables import display_data_table

# Initialize model
habitat_model = HabitatModel()

# Initialize session state
if "habitat_view" not in st.session_state:
    st.session_state.habitat_view = "list"
if "selected_habitat_id" not in st.session_state:
    st.session_state.selected_habitat_id = None


def show_list_view():
    """Display list of all habitats."""
    st.title("🌳 Habitats")

    total_count = habitat_model.count()
    st.info(f"**{total_count}** habitat types for creation and management")

    # Get habitats with area counts
    habitats_with_counts = habitat_model.get_with_area_counts()

    def on_view_details(habitat_id):
        st.session_state.selected_habitat_id = habitat_id
        st.session_state.habitat_view = "detail"

    display_data_table(
        data=habitats_with_counts,
        title="Habitat Types",
        entity_name="habitat",
        id_column="habitat_id",
        searchable_columns=["habitat"],
        column_config={
            "habitat_id": st.column_config.NumberColumn("ID", width="small"),
            "habitat": st.column_config.TextColumn("Habitat Type", width="large"),
            "creation_areas": st.column_config.NumberColumn(
                "Creation Areas",
                width="small",
                help="Number of areas where this habitat can be created",
            ),
            "management_areas": st.column_config.NumberColumn(
                "Management Areas",
                width="small",
                help="Number of areas where this habitat requires management",
            ),
        },
        show_actions=True,
        on_view_details=on_view_details,
    )


def show_detail_view():
    """Display details of a single habitat."""
    habitat_id = st.session_state.selected_habitat_id

    if habitat_id is None:
        st.error("No habitat selected")
        if st.button("← Back to List"):
            st.session_state.habitat_view = "list"
            st.rerun()
        return

    # Get habitat data
    habitat_data = habitat_model.get_by_id(habitat_id)

    if not habitat_data:
        st.error(f"Habitat ID {habitat_id} not found")
        if st.button("← Back to List"):
            st.session_state.habitat_view = "list"
            st.rerun()
        return

    # Get related data
    creation_areas = habitat_model.get_creation_areas(habitat_id)
    management_areas = habitat_model.get_management_areas(habitat_id)

    st.title(f"🌳 Habitat Details")

    # Back button
    if st.button("← Back to List"):
        st.session_state.habitat_view = "list"
        st.session_state.selected_habitat_id = None
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Habitat ID:** {habitat_data['habitat_id']}")
        st.markdown("**Habitat Type:**")
        st.info(habitat_data['habitat'])

    with col2:
        st.metric("Creation Areas", len(creation_areas))
        st.metric("Management Areas", len(management_areas))

    # Display related areas in tabs
    st.markdown("---")
    st.subheader("Related Areas")

    tab1, tab2 = st.tabs(["Creation Areas", "Management Areas"])

    with tab1:
        st.caption("Areas where this habitat type can be created")
        if len(creation_areas) > 0:
            st.dataframe(
                creation_areas.to_pandas(),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn("Area Name", width="medium"),
                    "area_description": st.column_config.TextColumn(
                        "Description", width="large"
                    ),
                },
            )
            st.caption(f"Total: {len(creation_areas):,} areas")
        else:
            st.info("No areas designated for creation of this habitat type.")

    with tab2:
        st.caption("Areas where this habitat type requires management")
        if len(management_areas) > 0:
            st.dataframe(
                management_areas.to_pandas(),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn("Area Name", width="medium"),
                    "area_description": st.column_config.TextColumn(
                        "Description", width="large"
                    ),
                },
            )
            st.caption(f"Total: {len(management_areas):,} areas")
        else:
            st.info("No areas designated for management of this habitat type.")


# Main page logic
if st.session_state.habitat_view == "list":
    show_list_view()
elif st.session_state.habitat_view == "detail":
    show_detail_view()
