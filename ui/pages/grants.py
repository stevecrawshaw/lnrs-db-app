"""Grants page - View and manage grant funding information."""

import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

import duckdb
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.grant import GrantModel  # noqa: E402
from ui.components.tables import display_data_table  # noqa: E402

logger = logging.getLogger(__name__)

# Initialize model
grant_model = GrantModel()

# Initialize session state
if "grant_view" not in st.session_state:
    st.session_state.grant_view = "list"
if "selected_grant_id" not in st.session_state:
    st.session_state.selected_grant_id = None
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
    """Display form to create a new grant."""
    st.subheader("➕ Create New Grant")

    with st.form("create_grant_form", clear_on_submit=True):
        grant_id = st.text_input(
            "Grant ID*",
            help="Unique identifier for the grant (required)",
        )

        grant_name = st.text_input(
            "Grant Name*",
            help="Name of the grant (required)",
        )

        grant_scheme = st.text_input(
            "Grant Scheme*",
            help="Scheme or program this grant belongs to (required)",
        )

        url = st.text_input(
            "URL",
            help="Optional link to grant information",
        )

        grant_summary = st.text_area(
            "Grant Summary", help="Optional summary of the grant", height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Create Grant", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_create_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not grant_id or not grant_id.strip():
                st.error("❌ Grant ID is required")
                return

            if not grant_name or not grant_name.strip():
                st.error("❌ Grant Name is required")
                return

            if not grant_scheme or not grant_scheme.strip():
                st.error("❌ Grant Scheme is required")
                return

            # Validate URL if provided
            if url and url.strip() and not validate_url(url):
                st.error(
                    "❌ Invalid URL format. Please provide a valid URL (e.g., https://example.com)"
                )
                return

            # Check if grant_id already exists
            existing = grant_model.get_by_id(grant_id.strip())
            if existing:
                st.error(
                    f"❌ Grant ID '{grant_id.strip()}' already exists. "
                    "Please use a different ID."
                )
                return

            # Create grant
            try:
                grant_model.create(
                    {
                        "grant_id": grant_id.strip(),
                        "grant_name": grant_name.strip(),
                        "grant_scheme": grant_scheme.strip(),
                        "url": url.strip() if url and url.strip() else None,
                        "grant_summary": grant_summary.strip()
                        if grant_summary and grant_summary.strip()
                        else None,
                    }
                )
                st.success(f"✅ Successfully created grant '{grant_id.strip()}'!")
                st.session_state.show_create_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating grant: {str(e)}")


def show_edit_form(grant_id: str):
    """Display form to edit an existing grant."""
    grant_data = grant_model.get_by_id(grant_id)

    if not grant_data:
        st.error("Grant not found")
        return

    st.subheader(f"✏️ Edit Grant {grant_id}")

    with st.form("edit_grant_form"):
        grant_name = st.text_input("Grant Name*", value=grant_data["grant_name"])

        grant_scheme = st.text_input("Grant Scheme*", value=grant_data["grant_scheme"])

        url = st.text_input("URL", value=grant_data.get("url", "") or "")

        grant_summary = st.text_area(
            "Grant Summary", value=grant_data.get("grant_summary", "") or "", height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "Update Grant", type="primary", width="stretch"
            )
        with col2:
            cancelled = st.form_submit_button("Cancel", width="stretch")

        if cancelled:
            st.session_state.show_edit_form = False
            st.rerun()

        if submitted:
            # Validate required fields
            if not grant_name or not grant_name.strip():
                st.error("❌ Grant Name is required")
                return

            if not grant_scheme or not grant_scheme.strip():
                st.error("❌ Grant Scheme is required")
                return

            # Validate URL if provided
            if url and url.strip() and not validate_url(url):
                st.error(
                    "❌ Invalid URL format. Please provide a valid URL (e.g., https://example.com)"
                )
                return

            # Update grant
            try:
                grant_model.update(
                    grant_id,
                    {
                        "grant_name": grant_name.strip(),
                        "grant_scheme": grant_scheme.strip(),
                        "url": url.strip() if url and url.strip() else None,
                        "grant_summary": grant_summary.strip()
                        if grant_summary and grant_summary.strip()
                        else None,
                    },
                )
                st.success(f"✅ Successfully updated grant '{grant_id}'!")
                st.session_state.show_edit_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating grant: {str(e)}")


def show_delete_confirmation(grant_id: str):
    """Show confirmation dialog before deleting."""
    grant_data = grant_model.get_by_id(grant_id)

    if not grant_data:
        st.error(f"Grant ID {grant_id} not found")
        return

    counts = grant_model.get_relationship_counts(grant_id)

    st.warning("⚠️ Are you sure you want to delete this grant?")

    st.markdown(f"**Grant ID:** {grant_data['grant_id']}")
    st.markdown(f"**Grant Name:** {grant_data['grant_name']}")
    st.markdown(f"**Scheme:** {grant_data['grant_scheme']}")

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
        st.info("This grant has no relationships and can be safely deleted.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", width="stretch"):
            st.session_state.show_delete_confirm = False
            st.rerun()
    with col2:
        if st.button("🗑️ Delete Grant", type="primary", width="stretch"):
            try:
                grant_model.delete_with_cascade(grant_id)
                st.success(f"✅ Successfully deleted grant '{grant_id}'!")
                st.session_state.show_delete_confirm = False
                st.session_state.grant_view = "list"
                st.session_state.selected_grant_id = None
                st.rerun()
            except duckdb.Error as e:
                error_msg = str(e)
                if "constraint" in error_msg.lower():
                    st.error("❌ Cannot delete: This grant is referenced by other data")
                elif "not found" in error_msg.lower():
                    st.error("❌ Grant not found")
                else:
                    st.error(f"❌ Database error: {error_msg}")
                logger.exception("Operation failed for user")


def show_list_view():
    """Display list of all grants."""
    st.title("💰 Grants & Funding")

    # Create button
    if st.button("➕ Create New Grant", type="primary"):
        st.session_state.show_create_form = True

    # Show create form if requested
    if st.session_state.show_create_form:
        show_create_form()
        st.markdown("---")

    total_count = grant_model.count()
    st.info(f"**{total_count}** grant funding opportunities available")

    # View options
    view_mode = st.radio(
        "View Mode",
        ["Grouped by Scheme", "All Grants (Table)"],
        horizontal=True,
    )

    if view_mode == "Grouped by Scheme":
        # Get grants grouped by scheme
        by_scheme = grant_model.get_by_scheme()

        for scheme, grants in by_scheme.items():
            with st.expander(
                f"**{scheme}** ({len(grants)} grants)",
                expanded=True,
            ):
                # Display grants in this scheme
                grants_display = grants.select(
                    [
                        "grant_id",
                        "grant_name",
                        "url",
                        "grant_summary",
                    ]
                )

                st.dataframe(
                    grants_display.to_pandas(),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "grant_id": st.column_config.TextColumn("ID", width="small"),
                        "grant_name": st.column_config.TextColumn(
                            "Grant Name", width="medium"
                        ),
                        "url": st.column_config.LinkColumn("URL", width="medium"),
                        "grant_summary": st.column_config.TextColumn(
                            "Summary", width="large"
                        ),
                    },
                )

    else:
        # Show all grants as a single table
        all_grants = grant_model.get_all(order_by="grant_scheme, grant_name")

        def on_view_details(grant_id):
            st.session_state.selected_grant_id = grant_id
            st.session_state.grant_view = "detail"

        display_data_table(
            data=all_grants,
            title="All Grants",
            entity_name="grant",
            id_column="grant_id",
            searchable_columns=["grant_name", "grant_scheme", "grant_summary"],
            column_config={
                "grant_id": st.column_config.TextColumn("ID", width="small"),
                "grant_name": st.column_config.TextColumn("Grant Name", width="medium"),
                "grant_scheme": st.column_config.TextColumn("Scheme", width="medium"),
                "url": st.column_config.LinkColumn("URL", width="medium"),
                "grant_summary": st.column_config.TextColumn("Summary", width="large"),
            },
            show_actions=True,
            on_view_details=on_view_details,
        )


def show_detail_view():
    """Display details of a single grant."""
    grant_id = st.session_state.selected_grant_id

    if grant_id is None:
        st.error("No grant selected")
        if st.button("← Back to List"):
            st.session_state.grant_view = "list"
            st.rerun()
        return

    # Get grant data
    grant_data = grant_model.get_by_id(grant_id)

    if not grant_data:
        st.error(f"Grant ID {grant_id} not found")
        if st.button("← Back to List"):
            st.session_state.grant_view = "list"
            st.rerun()
        return

    # Get related data
    related_measures = grant_model.get_related_measures(grant_id)

    # Display detail view
    def back_to_list():
        st.session_state.grant_view = "list"
        st.session_state.selected_grant_id = None
        st.session_state.show_edit_form = False
        st.session_state.show_delete_confirm = False

    st.title("💰 Grant Details")

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
        show_edit_form(grant_id)
        st.markdown("---")

    # Show delete confirmation if requested
    if st.session_state.show_delete_confirm:
        st.markdown("---")
        show_delete_confirmation(grant_id)
        st.markdown("---")

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Grant ID:** {grant_data['grant_id']}")
        st.markdown(f"**Grant Name:** {grant_data['grant_name']}")
        st.markdown(f"**Scheme:** {grant_data['grant_scheme']}")
        if grant_data["url"]:
            st.markdown(f"**URL:** [{grant_data['url']}]({grant_data['url']})")
        else:
            st.markdown("**URL:** _Not provided_")

    with col2:
        st.markdown("**Relationship Counts:**")
        st.metric("Funded Measure Links", len(related_measures))

    if grant_data["grant_summary"]:
        st.markdown("**Summary:**")
        st.info(grant_data["grant_summary"])
    else:
        st.markdown("**Summary:** _Not provided_")

    # Display related measures
    st.markdown("---")
    st.subheader("Funded Measures")

    if len(related_measures) > 0:
        st.dataframe(
            related_measures.to_pandas(),
            width="stretch",
            hide_index=True,
            column_config={
                "measure_id": st.column_config.NumberColumn("ID", width="small"),
                "measure": st.column_config.TextColumn("Measure", width="large"),
                "area_name": st.column_config.TextColumn("Area", width="medium"),
                "biodiversity_priority": st.column_config.TextColumn(
                    "Priority", width="large"
                ),
            },
        )
        st.caption(f"Total: {len(related_measures):,} measure-area-priority links")
    else:
        st.info("No measures are currently linked to this grant.")


# Main page logic
if st.session_state.grant_view == "list":
    show_list_view()
elif st.session_state.grant_view == "detail":
    show_detail_view()
