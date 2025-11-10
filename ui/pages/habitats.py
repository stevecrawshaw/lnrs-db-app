"""Habitats page - View and manage habitat types."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.habitat import HabitatModel  # noqa: E402
from ui.components.tables import display_data_table  # noqa: E402

# Initialize model
habitat_model = HabitatModel()

# Initialize session state
if "habitat_view" not in st.session_state:
    st.session_state.habitat_view = "list"
if "selected_habitat_id" not in st.session_state:
    st.session_state.selected_habitat_id = None
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False
if "show_edit_form" not in st.session_state:
    st.session_state.show_edit_form = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False


def show_create_form():
    """Display form to create a new habitat."""
    st.subheader("➕ Create New Habitat")

    with st.form("create_habitat_form", clear_on_submit=True):
        habitat = st.text_input(
            "Habitat Type*",
            help="Name of the habitat type (required)",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Habitat", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate
            if not habitat or not habitat.strip():
                st.error("❌ Habitat Type is required")
                return

            # Get next habitat_id
            result = habitat_model.execute_raw_query(
                "SELECT MAX(habitat_id) FROM habitat"
            ).fetchone()
            max_id = result[0] if result else None
            next_id = (max_id or 0) + 1

            # Create habitat
            try:
                habitat_model.create(
                    {"habitat_id": next_id, "habitat": habitat.strip()}
                )
                st.success(f"✅ Successfully created habitat ID {next_id}!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating habitat: {str(e)}")


def show_edit_form(habitat_id: int):
    """Display form to edit an existing habitat."""
    habitat_data = habitat_model.get_by_id(habitat_id)

    if not habitat_data:
        st.error("Habitat not found")
        return

    st.subheader(f"✏️ Edit Habitat {habitat_id}")

    with st.form("edit_habitat_form"):
        habitat = st.text_input("Habitat Type*", value=habitat_data["habitat"])

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Update Habitat", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate
            if not habitat or not habitat.strip():
                st.error("❌ Habitat Type is required")
                return

            # Update habitat
            try:
                habitat_model.update(habitat_id, {"habitat": habitat.strip()})
                st.success(f"✅ Successfully updated habitat ID {habitat_id}!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating habitat: {str(e)}")


def show_delete_confirmation(habitat_id: int):
    """Show confirmation dialog before deleting."""
    habitat_data = habitat_model.get_by_id(habitat_id)

    if not habitat_data:
        st.error(f"Habitat ID {habitat_id} not found")
        return

    counts = habitat_model.get_relationship_counts(habitat_id)

    st.warning("⚠️ Are you sure you want to delete this habitat?")

    st.markdown(f"**Habitat:** {habitat_data['habitat']}")

    # Show impact
    total_relationships = sum(counts.values())
    if total_relationships > 0:
        st.error("**This will also delete the following relationships:**")
        for relationship, count in counts.items():
            if count > 0:
                relationship_display = relationship.replace("_", " ").title()
                st.write(f"- {count} {relationship_display}")
        st.write(f"\n**Total relationships to be removed: {total_relationships}**")
    else:
        st.info("This habitat has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width="stretch"):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Habitat", type="primary", width="stretch"):
            try:
                habitat_model.delete_with_cascade(habitat_id)
                st.success(f"✅ Successfully deleted habitat ID {habitat_id}!")
                st.session_state.show_delete_confirm = False
                st.session_state.habitat_view = "list"
                st.session_state.selected_habitat_id = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting habitat: {str(e)}")


def show_list_view():
    """Display list of all habitats."""
    st.title("🌳 Habitats")

    # Create button
    if st.button("➕ Create New Habitat", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

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

    # Display detail view
    def back_to_list():
        st.session_state.habitat_view = "list"
        st.session_state.selected_habitat_id = None
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title("🌳 Habitat Details")

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("← Back to List"):
            back_to_list()
            st.rerun()
    with col2:
        if st.button("✏️ Edit", width="stretch"):
            st.session_state.show_edit_form = True
            st.session_state.show_delete_confirm = False
    with col3:
        if st.button("🗑️ Delete", width="stretch"):
            st.session_state.show_delete_confirm = True
            st.session_state.show_edit_form = False

    # Show edit form if requested
    if st.session_state.show_edit_form:
        st.markdown("---")
        show_edit_form(habitat_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(habitat_id)
        st.markdown("---")

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Habitat ID:** {habitat_data['habitat_id']}")
        st.markdown("**Habitat Type:**")
        st.info(habitat_data["habitat"])

    with col2:
        st.markdown("**Area Counts:**")
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
                width="stretch",
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn(
                        "Area Name", width="medium"
                    ),
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
                width="stretch",
                hide_index=True,
                column_config={
                    "area_id": st.column_config.NumberColumn("ID", width="small"),
                    "area_name": st.column_config.TextColumn(
                        "Area Name", width="medium"
                    ),
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
