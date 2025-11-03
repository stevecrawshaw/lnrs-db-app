"""Measures page - View and manage biodiversity measures."""

import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

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
    """Display form to create a new measure."""
    st.subheader("➕ Create New Measure")

    # Get options for dropdowns
    all_types = measure_model.get_all_measure_types()
    all_stakeholders = measure_model.get_all_stakeholders()
    all_benefits = measure_model.get_all_benefits()

    with st.form("create_measure_form", clear_on_submit=True):
        measure = st.text_area(
            "Measure Description*",
            help="Full description of the biodiversity measure (required)",
            height=150
        )

        concise_measure = st.text_input(
            "Concise Measure",
            help="Optional shortened version of the measure",
        )

        col1, col2 = st.columns(2)
        with col1:
            core_supplementary = st.selectbox(
                "Core/Supplementary*",
                options=["Core (BNG)", "Supplementary"],
                help="Whether this is a core BNG measure or supplementary (required)"
            )

            mapped_unmapped = st.selectbox(
                "Mapped/Unmapped",
                options=["", "Mapped", "Unmapped"],
                help="Optional: Whether this measure is mapped"
            )

        with col2:
            link_to_further_guidance = st.text_input(
                "Link to Further Guidance",
                help="Optional URL to additional information",
            )

        st.markdown("---")
        st.markdown("**Relationships** (Optional - select multiple)")

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_types = st.multiselect(
                "Measure Types",
                options=all_types["measure_type"].to_list(),
                help="Select applicable measure types"
            )

        with col2:
            selected_stakeholders = st.multiselect(
                "Stakeholders",
                options=all_stakeholders["stakeholder"].to_list(),
                help="Select applicable stakeholders"
            )

        with col3:
            selected_benefits = st.multiselect(
                "Benefits",
                options=all_benefits["benefit"].to_list(),
                help="Select benefits delivered by this measure"
            )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Measure", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not measure or not measure.strip():
                st.error("❌ Measure Description is required")
                return

            # Validate URL if provided
            if link_to_further_guidance and not validate_url(link_to_further_guidance):
                st.error("❌ Link to Further Guidance must be a valid URL (e.g., https://example.com)")
                return

            # Get next measure_id using max_meas() macro
            max_id = measure_model.execute_raw_query("SELECT MAX(measure_id) FROM measure").fetchone()[0]
            next_id = (max_id or 0) + 1

            # Create measure
            try:
                measure_model.create({
                    "measure_id": next_id,
                    "measure": measure.strip(),
                    "concise_measure": concise_measure.strip() if concise_measure and concise_measure.strip() else None,
                    "core_supplementary": core_supplementary,
                    "mapped_unmapped": mapped_unmapped if mapped_unmapped else None,
                    "link_to_further_guidance": link_to_further_guidance.strip() if link_to_further_guidance and link_to_further_guidance.strip() else None,
                })

                # Add relationships
                if selected_types:
                    type_ids = [all_types.filter(pl.col("measure_type") == t)["measure_type_id"][0] for t in selected_types]
                    measure_model.add_measure_types(next_id, type_ids)

                if selected_stakeholders:
                    stakeholder_ids = [all_stakeholders.filter(pl.col("stakeholder") == s)["stakeholder_id"][0] for s in selected_stakeholders]
                    measure_model.add_stakeholders(next_id, stakeholder_ids)

                if selected_benefits:
                    benefit_ids = [all_benefits.filter(pl.col("benefit") == b)["benefit_id"][0] for b in selected_benefits]
                    measure_model.add_benefits(next_id, benefit_ids)

                st.success(f"✅ Successfully created measure ID {next_id}!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating measure: {str(e)}")


def show_edit_form(measure_id: int):
    """Display form to edit an existing measure."""
    measure_data = measure_model.get_by_id(measure_id)

    if not measure_data:
        st.error("Measure not found")
        return

    # Get current relationships
    current_types = measure_model.get_types(measure_id)
    current_stakeholders = measure_model.get_stakeholders(measure_id)
    current_benefits = measure_model.get_benefits(measure_id)

    # Get options for dropdowns
    all_types = measure_model.get_all_measure_types()
    all_stakeholders = measure_model.get_all_stakeholders()
    all_benefits = measure_model.get_all_benefits()

    st.subheader(f"✏️ Edit Measure {measure_id}")

    with st.form("edit_measure_form"):
        measure = st.text_area(
            "Measure Description*",
            value=measure_data['measure'],
            height=150
        )

        concise_measure = st.text_input(
            "Concise Measure",
            value=measure_data.get('concise_measure', '') or ''
        )

        col1, col2 = st.columns(2)
        with col1:
            core_supp_options = ["Core (BNG)", "Supplementary"]
            core_supp_index = 0
            if measure_data['core_supplementary'] in core_supp_options:
                core_supp_index = core_supp_options.index(measure_data['core_supplementary'])

            core_supplementary = st.selectbox(
                "Core/Supplementary*",
                options=core_supp_options,
                index=core_supp_index
            )

            mapped_options = ["", "Mapped", "Unmapped"]
            mapped_index = 0
            if measure_data.get('mapped_unmapped') in mapped_options:
                mapped_index = mapped_options.index(measure_data['mapped_unmapped'])

            mapped_unmapped = st.selectbox(
                "Mapped/Unmapped",
                options=mapped_options,
                index=mapped_index
            )

        with col2:
            link_to_further_guidance = st.text_input(
                "Link to Further Guidance",
                value=measure_data.get('link_to_further_guidance', '') or ''
            )

        st.markdown("---")
        st.markdown("**Relationships** (Select multiple)")

        col1, col2, col3 = st.columns(3)
        with col1:
            current_type_names = current_types["measure_type"].to_list() if len(current_types) > 0 else []
            selected_types = st.multiselect(
                "Measure Types",
                options=all_types["measure_type"].to_list(),
                default=current_type_names
            )

        with col2:
            current_stakeholder_names = current_stakeholders["stakeholder"].to_list() if len(current_stakeholders) > 0 else []
            selected_stakeholders = st.multiselect(
                "Stakeholders",
                options=all_stakeholders["stakeholder"].to_list(),
                default=current_stakeholder_names
            )

        with col3:
            current_benefit_names = current_benefits["benefit"].to_list() if len(current_benefits) > 0 else []
            selected_benefits = st.multiselect(
                "Benefits",
                options=all_benefits["benefit"].to_list(),
                default=current_benefit_names
            )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Measure", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not measure or not measure.strip():
                st.error("❌ Measure Description is required")
                return

            # Validate URL if provided
            if link_to_further_guidance and not validate_url(link_to_further_guidance):
                st.error("❌ Link to Further Guidance must be a valid URL (e.g., https://example.com)")
                return

            # Update measure
            try:
                measure_model.update(measure_id, {
                    "measure": measure.strip(),
                    "concise_measure": concise_measure.strip() if concise_measure and concise_measure.strip() else None,
                    "core_supplementary": core_supplementary,
                    "mapped_unmapped": mapped_unmapped if mapped_unmapped else None,
                    "link_to_further_guidance": link_to_further_guidance.strip() if link_to_further_guidance and link_to_further_guidance.strip() else None,
                })

                # Update relationships - delete old and add new
                # Delete existing relationships
                measure_model.execute_raw_query("DELETE FROM measure_has_type WHERE measure_id = ?", [measure_id])
                measure_model.execute_raw_query("DELETE FROM measure_has_stakeholder WHERE measure_id = ?", [measure_id])
                measure_model.execute_raw_query("DELETE FROM measure_has_benefits WHERE measure_id = ?", [measure_id])

                # Add new relationships
                if selected_types:
                    type_ids = [all_types.filter(pl.col("measure_type") == t)["measure_type_id"][0] for t in selected_types]
                    measure_model.add_measure_types(measure_id, type_ids)

                if selected_stakeholders:
                    stakeholder_ids = [all_stakeholders.filter(pl.col("stakeholder") == s)["stakeholder_id"][0] for s in selected_stakeholders]
                    measure_model.add_stakeholders(measure_id, stakeholder_ids)

                if selected_benefits:
                    benefit_ids = [all_benefits.filter(pl.col("benefit") == b)["benefit_id"][0] for b in selected_benefits]
                    measure_model.add_benefits(measure_id, benefit_ids)

                st.success(f"✅ Successfully updated measure ID {measure_id}!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating measure: {str(e)}")


def show_delete_confirmation(measure_id: int):
    """Show confirmation dialog before deleting."""
    measure_data = measure_model.get_by_id(measure_id)
    counts = measure_model.get_relationship_counts(measure_id)

    st.warning(f"⚠️ Are you sure you want to delete this measure?")

    st.markdown(f"**ID:** {measure_id}")
    st.markdown(f"**Concise Measure:** {measure_data.get('concise_measure') or 'N/A'}")
    st.markdown(f"**Type:** {measure_data['core_supplementary']}")

    # Show impact
    total_relationships = sum(counts.values())
    if total_relationships > 0:
        st.error("**This will also delete the following relationships:**")
        for relationship, count in counts.items():
            if count > 0:
                relationship_display = relationship.replace('_', ' ').title()
                st.write(f"- {count} {relationship_display}")
        st.write(f"\n**Total relationships to be removed: {total_relationships}**")

        # Extra warning for measures with many relationships
        if total_relationships > 20:
            st.warning("⚠️ **This is a MAJOR deletion!** This measure has extensive relationships. Consider carefully before proceeding.")
    else:
        st.info("This measure has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Measure", type="primary", use_container_width=True):
            try:
                measure_model.delete_with_cascade(measure_id)
                st.success(f"✅ Successfully deleted measure ID {measure_id}!")
                st.session_state.show_delete_confirm = False
                st.session_state.measure_view = "list"
                st.session_state.selected_measure_id = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting measure: {str(e)}")


def show_list_view():
    """Display list of all measures with types, stakeholders, and counts."""
    st.title("📋 Biodiversity Measures")

    # Create button
    if st.button("➕ Create New Measure", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

    total_count = measure_model.count()
    st.info(f"**{total_count}** measures for biodiversity conservation")

    # Get all measures with relationship counts
    all_measures = measure_model.get_with_relationship_counts()

    # Add semicolon-delimited CSV export button
    col1, col2 = st.columns([4, 1])
    with col2:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"measures_export_{timestamp}.csv"
        csv_data = all_measures.write_csv(separator=";")

        st.download_button(
            label="📥 CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            help="Export all measures as CSV with semicolon delimiter (safer for text with commas)",
        )

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
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title(f"📋 Measure {measure_id}")

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

    # Check for orphan status (measure not linked to any area)
    is_orphan = counts['areas'] == 0

    if is_orphan:
        st.warning("⚠️ **This measure is not linked to any areas or priorities.** Use Quick Actions to create links.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔗 Link to Area/Priority", use_container_width=True, type="secondary"):
            # Set session state to pre-fill the form on relationships page
            st.session_state.quick_link_measure_id = measure_id
            st.session_state.quick_link_action = "create_map"
            st.switch_page("ui/pages/relationships.py")

    with col2:
        if st.button("👁️ View All Links", use_container_width=True, type="secondary"):
            # Navigate to relationships page filtered for this measure
            st.session_state.filter_measure_id = measure_id
            st.switch_page("ui/pages/relationships.py")

    # Show edit form if requested
    if st.session_state.show_edit_form:
        st.markdown("---")
        show_edit_form(measure_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(measure_id)
        st.markdown("---")

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Measure ID:** {measure_data['measure_id']}")
        st.markdown(f"**Core/Supplementary:** {measure_data['core_supplementary']}")
        st.markdown(f"**Mapped/Unmapped:** {measure_data.get('mapped_unmapped') or 'Not specified'}")

        if measure_data.get('concise_measure'):
            st.markdown("**Concise Measure:**")
            st.info(measure_data['concise_measure'])

        st.markdown("**Full Measure:**")
        st.info(measure_data['measure'])

        if measure_data.get('link_to_further_guidance'):
            st.markdown(f"**Guidance:** [{measure_data['link_to_further_guidance']}]({measure_data['link_to_further_guidance']})")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Types", counts['types'])
        st.metric("Stakeholders", counts['stakeholders'])
        st.metric("Benefits", counts['benefits'])
        st.metric("Areas", counts['areas'])
        st.metric("Priorities", counts['priorities'])
        st.metric("Grants", counts['grants'])
        st.metric("Species", counts['species'])

    # Display relationships in tabs
    st.markdown("---")
    st.subheader("Relationships")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Types", "Stakeholders", "Benefits", "Areas", "Priorities", "Grants", "Species"
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
        else:
            st.info("No measure types linked.")

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
        else:
            st.info("No stakeholders linked.")

    with tab3:
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
        else:
            st.info("No benefits linked.")

    with tab4:
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

    with tab5:
        if len(related_priorities) > 0:
            st.dataframe(
                related_priorities.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "priority_id": st.column_config.NumberColumn("ID", width="small"),
                    "biodiversity_priority": st.column_config.TextColumn("Priority", width="large"),
                    "theme": st.column_config.TextColumn("Theme", width="medium"),
                },
            )
            st.caption(f"Total: {len(related_priorities):,} priorities")
        else:
            st.info("No priorities linked to this measure.")

    with tab6:
        if len(related_grants) > 0:
            st.dataframe(
                related_grants.to_pandas(),
                width="stretch",
                hide_index=True,
                column_config={
                    "grant_id": st.column_config.TextColumn("Grant ID", width="small"),
                    "grant_name": st.column_config.TextColumn("Grant Name", width="medium"),
                    "grant_scheme": st.column_config.TextColumn("Scheme", width="medium"),
                    "url": st.column_config.LinkColumn("URL", width="medium"),
                },
            )
            st.caption(f"Total: {len(related_grants):,} grants")
        else:
            st.info("No grants linked to this measure.")

    with tab7:
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
            st.info("No species linked to this measure.")


# Main page logic
if st.session_state.measure_view == "list":
    show_list_view()
elif st.session_state.measure_view == "detail":
    show_detail_view()
