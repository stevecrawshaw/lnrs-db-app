"""Priorities page - View and manage biodiversity priorities."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.priority import PriorityModel  # noqa: E402
from ui.components.tables import display_data_table  # noqa: E402

logger = logging.getLogger(__name__)

# Initialize model
priority_model = PriorityModel()

# Initialize session state
if "priority_view" not in st.session_state:
    st.session_state.priority_view = "list"
if "selected_priority_id" not in st.session_state:
    st.session_state.selected_priority_id = None
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False
if "show_edit_form" not in st.session_state:
    st.session_state.show_edit_form = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False


def show_create_form():
    """Display form to create a new priority."""
    st.subheader("➕ Create New Priority")

    with st.form("create_priority_form", clear_on_submit=True):
        biodiversity_priority = st.text_area(
            "Biodiversity Priority*",
            help="Full description of the biodiversity priority (required)",
            height=100,
        )

        simplified_priority = st.text_input(
            "Simplified Priority", help="Optional simplified version"
        )

        theme = st.selectbox(
            "Theme*",
            options=[
                "Grassland and farmland",
                "Heathland and moorland",
                "Marine",
                "Wetlands, rivers and floodplains",
                "Woodland",
                "All habitats",
            ],
            help="Select the theme category (required)",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Priority", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate
            if not biodiversity_priority or not biodiversity_priority.strip():
                st.error("❌ Biodiversity Priority is required")
                return

            if not theme:
                st.error("❌ Theme is required")
                return

            # Get next priority_id
            result = priority_model.execute_raw_query(
                "SELECT MAX(priority_id) FROM priority"
            ).fetchone()
            max_id = result[0] if result else None
            next_id = (max_id or 0) + 1

            # Create priority
            try:
                priority_model.create(
                    {
                        "priority_id": next_id,
                        "biodiversity_priority": biodiversity_priority.strip(),
                        "simplified_biodiversity_priority": simplified_priority.strip()
                        if simplified_priority
                        else None,
                        "theme": theme,
                    }
                )
                st.success(f"✅ Successfully created priority ID {next_id}!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating priority: {str(e)}")


def show_edit_form(priority_id: int):
    """Display form to edit an existing priority."""
    priority_data = priority_model.get_by_id(priority_id)

    if not priority_data:
        st.error("Priority not found")
        return

    st.subheader(f"✏️ Edit Priority {priority_id}")

    with st.form("edit_priority_form"):
        biodiversity_priority = st.text_area(
            "Biodiversity Priority*",
            value=priority_data["biodiversity_priority"],
            height=100,
        )

        simplified_priority = st.text_input(
            "Simplified Priority",
            value=priority_data.get("simplified_biodiversity_priority", "") or "",
        )

        theme = st.selectbox(
            "Theme*",
            options=[
                "Grassland and farmland",
                "Heathland and moorland",
                "Marine",
                "Wetlands, rivers and floodplains",
                "Woodland",
                "All habitats",
            ],
            index=[
                "Grassland and farmland",
                "Heathland and moorland",
                "Marine",
                "Wetlands, rivers and floodplains",
                "Woodland",
                "All habitats",
            ].index(priority_data["theme"].strip())
            if priority_data["theme"].strip()
            in [
                "Grassland and farmland",
                "Heathland and moorland",
                "Marine",
                "Wetlands, rivers and floodplains",
                "Woodland",
                "All habitats",
            ]
            else 0,
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Update Priority", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate
            if not biodiversity_priority or not biodiversity_priority.strip():
                st.error("❌ Biodiversity Priority is required")
                return

            # Update priority
            try:
                priority_model.update(
                    priority_id,
                    {
                        "biodiversity_priority": biodiversity_priority.strip(),
                        "simplified_biodiversity_priority": simplified_priority.strip()
                        if simplified_priority
                        else None,
                        "theme": theme,
                    },
                )
                st.success(f"✅ Successfully updated priority ID {priority_id}!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating priority: {str(e)}")


def show_delete_confirmation(priority_id: int):
    """Show confirmation dialog before deleting."""
    priority_data = priority_model.get_by_id(priority_id)

    if not priority_data:
        st.error(f"Priority ID {priority_id} not found")
        return

    counts = priority_model.get_relationship_counts(priority_id)

    st.warning("⚠️ Are you sure you want to delete this priority?")

    st.markdown(f"**Priority:** {priority_data['biodiversity_priority'][:100]}...")
    st.markdown(f"**Theme:** {priority_data['theme']}")

    # Show impact
    total_relationships = sum(counts.values())
    if total_relationships > 0:
        st.error("**This will also delete the following relationships:**")
        for relationship, count in counts.items():
            if count > 0:
                st.write(f"- {count} {relationship}")
        st.write(f"\n**Total relationships to be removed: {total_relationships}**")
    else:
        st.info("This priority has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width="stretch"):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Priority", type="primary", width="stretch"):
            try:
                priority_model.delete_with_cascade(priority_id)
                st.success(f"✅ Successfully deleted priority ID {priority_id}!")
                st.session_state.show_delete_confirm = False
                st.session_state.priority_view = "list"
                st.session_state.selected_priority_id = None
                st.rerun()
            except duckdb.Error as e:
                error_msg = str(e)
                if "constraint" in error_msg.lower():
                    st.error("❌ Cannot delete: This priority is referenced by other data")
                elif "not found" in error_msg.lower():
                    st.error("❌ Priority not found")
                else:
                    st.error(f"❌ Database error: {error_msg}")
                logger.exception("Operation failed for user")


def show_list_view():
    """Display list of all priorities."""
    st.title("🎯 Biodiversity Priorities")

    # Create button
    if st.button("➕ Create New Priority", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

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
            clean_theme = theme.strip().replace("\xa0", "")

            with st.expander(
                f"**{clean_theme}** ({len(priorities)} priorities)",
                expanded=True,
            ):
                # Display priorities in this theme
                priorities_display = priorities.select(
                    [
                        "priority_id",
                        "biodiversity_priority",
                        "simplified_biodiversity_priority",
                    ]
                )

                st.dataframe(
                    priorities_display.to_pandas(),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "priority_id": st.column_config.NumberColumn(
                            "ID", width="small"
                        ),
                        "biodiversity_priority": st.column_config.TextColumn(
                            "Biodiversity Priority", width="large"
                        ),
                        "simplified_biodiversity_priority": st.column_config.TextColumn(
                            "Simplified", width="medium"
                        ),
                    },
                    on_select="rerun",
                    selection_mode="single-row",
                )

    else:
        # Show all priorities as a single table
        all_priorities = priority_model.get_all(order_by="theme, biodiversity_priority")

        # Clean theme names in the dataframe
        all_priorities = all_priorities.with_columns(
            pl.col("theme").str.strip_chars().str.replace_all("\xa0", "")
        )

        # Add semicolon-delimited CSV export button
        _, col2 = st.columns([4, 1])
        with col2:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"priorities_export_{timestamp}.csv"
            csv_data = all_priorities.write_csv(separator=";")

            st.download_button(
                label="📥 CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                width="stretch",
                help=(
                    "Export all priorities as CSV with semicolon delimiter "
                    "(safer for text with commas)"
                ),
            )

        def on_view_details(priority_id):
            st.session_state.selected_priority_id = priority_id
            st.session_state.priority_view = "detail"

        display_data_table(
            data=all_priorities,
            title="All Priorities",
            entity_name="priority",
            id_column="priority_id",
            searchable_columns=[
                "biodiversity_priority",
                "simplified_biodiversity_priority",
                "theme",
            ],
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
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title("🎯 Priority Details")

    # Action buttons
    col1, col2, col3, _ = st.columns([2, 1, 1, 1])
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

    # Quick Actions section
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    # Check for orphan status (priority not linked to any measures)
    is_orphan = counts["measures"] == 0

    if is_orphan:
        st.warning(
            "⚠️ **This priority has no linked measures.** "
            "Use Quick Actions to create links."
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Link Measure", width="stretch", type="secondary"):
            # Set session state to pre-fill the form on relationships page
            st.session_state.quick_link_priority_id = priority_id
            st.session_state.quick_link_action = "create_map"
            st.switch_page("ui/pages/relationships.py")

    with col2:
        if st.button("🦋 Add Species", width="stretch", type="secondary"):
            # Navigate to species-area-priority tab
            st.session_state.quick_link_priority_id = priority_id
            st.session_state.quick_link_action = "create_species"
            st.switch_page("ui/pages/relationships.py")

    with col3:
        if st.button("👁️ View All Links", width="stretch", type="secondary"):
            # Navigate to relationships page filtered for this priority
            st.session_state.filter_priority_id = priority_id
            st.switch_page("ui/pages/relationships.py")

    # Show edit form if requested
    if st.session_state.show_edit_form:
        st.markdown("---")
        show_edit_form(priority_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(priority_id)
        st.markdown("---")

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {priority_data['priority_id']}")
        # Clean theme name for display
        clean_theme = priority_data["theme"].strip().replace("\xa0", "")
        st.markdown(f"**Theme:** {clean_theme}")
        st.markdown("**Biodiversity Priority:**")
        st.info(priority_data["biodiversity_priority"])

    with col2:
        st.markdown("**Simplified:**")
        if priority_data["simplified_biodiversity_priority"]:
            st.write(priority_data["simplified_biodiversity_priority"])
        else:
            st.caption("_Not provided_")

        st.markdown("---")
        st.markdown("**Relationship Counts:**")
        st.metric("Measures", counts["measures"])
        st.metric("Areas", counts["areas"])
        st.metric("Species", counts["species"])

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
                    "concise_measure": st.column_config.TextColumn(
                        "Concise", width="medium"
                    ),
                    "core_supplementary": st.column_config.TextColumn(
                        "Type", width="small"
                    ),
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
                    "area_name": st.column_config.TextColumn(
                        "Area Name", width="medium"
                    ),
                    "area_description": st.column_config.TextColumn(
                        "Description", width="large"
                    ),
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
                    "common_name": st.column_config.TextColumn(
                        "Common Name", width="medium"
                    ),
                    "linnaean_name": st.column_config.TextColumn(
                        "Scientific Name", width="medium"
                    ),
                    "assemblage": st.column_config.TextColumn(
                        "Assemblage", width="medium"
                    ),
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
