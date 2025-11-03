"""Areas page - View and manage priority areas."""

import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

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
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False
if "show_edit_form" not in st.session_state:
    st.session_state.show_edit_form = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        bool: True if URL is valid or empty, False otherwise
    """
    if not url or not url.strip():
        return True  # Empty URLs are allowed

    try:
        result = urlparse(url.strip())
        # Check that scheme and netloc are present
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def show_create_form():
    """Display form to create a new area."""
    st.subheader("➕ Create New Area")

    with st.form("create_area_form", clear_on_submit=True):
        area_name = st.text_input(
            "Area Name*",
            help="Name of the priority area (required)",
        )

        area_description = st.text_area(
            "Area Description*",
            help="Description of the area and its biodiversity significance (required)",
            height=150
        )

        area_link = st.text_input(
            "Area Link",
            help="Optional URL to more information about the area",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Area", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not area_name or not area_name.strip():
                st.error("❌ Area Name is required")
                return

            if not area_description or not area_description.strip():
                st.error("❌ Area Description is required")
                return

            # Validate URL if provided
            if area_link and not validate_url(area_link):
                st.error("❌ Area Link must be a valid URL (e.g., https://example.com)")
                return

            # Get next area_id
            max_id = area_model.execute_raw_query("SELECT MAX(area_id) FROM area").fetchone()[0]
            next_id = (max_id or 0) + 1

            # Create area
            try:
                area_model.create({
                    "area_id": next_id,
                    "area_name": area_name.strip(),
                    "area_description": area_description.strip(),
                    "area_link": area_link.strip() if area_link and area_link.strip() else None,
                    "bng_hab_mgt": None,
                    "bng_hab_creation": None,
                })
                st.success(f"✅ Successfully created area ID {next_id}!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating area: {str(e)}")


def show_edit_form(area_id: int):
    """Display form to edit an existing area."""
    area_data = area_model.get_by_id(area_id)

    if not area_data:
        st.error("Area not found")
        return

    st.subheader(f"✏️ Edit Area {area_id}")

    with st.form("edit_area_form"):
        area_name = st.text_input(
            "Area Name*",
            value=area_data['area_name']
        )

        area_description = st.text_area(
            "Area Description*",
            value=area_data['area_description'],
            height=150
        )

        area_link = st.text_input(
            "Area Link",
            value=area_data.get('area_link', '') or ''
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Area", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not area_name or not area_name.strip():
                st.error("❌ Area Name is required")
                return

            if not area_description or not area_description.strip():
                st.error("❌ Area Description is required")
                return

            # Validate URL if provided
            if area_link and not validate_url(area_link):
                st.error("❌ Area Link must be a valid URL (e.g., https://example.com)")
                return

            # Update area
            try:
                area_model.update(area_id, {
                    "area_name": area_name.strip(),
                    "area_description": area_description.strip(),
                    "area_link": area_link.strip() if area_link and area_link.strip() else None,
                })
                st.success(f"✅ Successfully updated area ID {area_id}!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating area: {str(e)}")


def show_delete_confirmation(area_id: int):
    """Show confirmation dialog before deleting."""
    area_data = area_model.get_by_id(area_id)
    counts = area_model.get_relationship_counts(area_id)

    st.warning(f"⚠️ Are you sure you want to delete this area?")

    st.markdown(f"**Area:** {area_data['area_name']}")
    st.markdown(f"**Description:** {area_data['area_description'][:100]}...")

    # Show impact
    total_relationships = sum(counts.values())
    if total_relationships > 0:
        st.error("**This will also delete the following relationships:**")
        for relationship, count in counts.items():
            if count > 0:
                relationship_display = relationship.replace('_', ' ').title()
                st.write(f"- {count} {relationship_display}")
        st.write(f"\n**Total relationships to be removed: {total_relationships}**")
        st.warning("⚠️ **This is a MAJOR deletion!** This area has many relationships. Consider carefully before proceeding.")
    else:
        st.info("This area has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Area", type="primary", use_container_width=True):
            try:
                area_model.delete_with_cascade(area_id)
                st.success(f"✅ Successfully deleted area ID {area_id}!")
                st.session_state.show_delete_confirm = False
                st.session_state.area_view = "list"
                st.session_state.selected_area_id = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting area: {str(e)}")


def show_list_view():
    """Display list of all areas with relationship counts."""
    st.title("🗺️ Priority Areas")

    # Create button
    if st.button("➕ Create New Area", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

    total_count = area_model.count()
    st.info(f"**{total_count}** priority areas for biodiversity conservation")

    # Get areas with relationship counts
    areas_with_counts = area_model.get_with_relationship_counts()

    # Add semicolon-delimited CSV export button
    col1, col2 = st.columns([4, 1])
    with col2:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"areas_export_{timestamp}.csv"
        csv_data = areas_with_counts.write_csv(separator=";")

        st.download_button(
            label="📥 CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            help="Export all areas as CSV with semicolon delimiter (safer for text with commas)",
        )

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
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title(f"🗺️ {area_data['area_name']}")

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("← Back to List"):
            back_to_list()
            st.rerun()
    with col2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.show_edit_form = True
            st.session_state.show_delete_confirm = False
    with col3:
        if st.button("🗑️ Delete", use_container_width=True):
            st.session_state.show_delete_confirm = True
            st.session_state.show_edit_form = False

    # Quick Actions section
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    # Check for orphan status (area not linked to any measures)
    is_orphan = counts['measures'] == 0

    if is_orphan:
        st.warning("⚠️ **This area has no linked measures.** Use Quick Actions to create links.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Link Measure", use_container_width=True, type="secondary"):
            # Set session state to pre-fill the form on relationships page
            st.session_state.quick_link_area_id = area_id
            st.session_state.quick_link_action = "create_map"
            st.switch_page("ui/pages/relationships.py")

    with col2:
        if st.button("🦋 Add Species", use_container_width=True, type="secondary"):
            # Navigate to species-area-priority tab
            st.session_state.quick_link_area_id = area_id
            st.session_state.quick_link_action = "create_species"
            st.switch_page("ui/pages/relationships.py")

    with col3:
        if st.button("🌳 Add Habitat", use_container_width=True, type="secondary"):
            # Navigate to habitat creation tab
            st.session_state.quick_link_area_id = area_id
            st.session_state.quick_link_action = "create_habitat"
            st.switch_page("ui/pages/relationships.py")

    # Show edit form if requested
    if st.session_state.show_edit_form:
        st.markdown("---")
        show_edit_form(area_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(area_id)
        st.markdown("---")

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
