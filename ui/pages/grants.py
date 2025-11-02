"""Grants page - View grant funding information."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.grant import GrantModel
from ui.components.tables import display_data_table

# Initialize model
grant_model = GrantModel()

# Initialize session state
if "grant_view" not in st.session_state:
    st.session_state.grant_view = "list"
if "selected_grant_id" not in st.session_state:
    st.session_state.selected_grant_id = None


def show_list_view():
    """Display list of all grants."""
    st.title("💰 Grants & Funding")

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
                grants_display = grants.select([
                    "grant_id",
                    "grant_name",
                    "url",
                    "grant_summary",
                ])

                st.dataframe(
                    grants_display.to_pandas(),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "grant_id": st.column_config.TextColumn("ID", width="small"),
                        "grant_name": st.column_config.TextColumn("Grant Name", width="medium"),
                        "url": st.column_config.LinkColumn("URL", width="medium"),
                        "grant_summary": st.column_config.TextColumn("Summary", width="large"),
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
            show_actions=False,  # Grant ID is text, number input won't work
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

    st.title(f"💰 Grant Details")

    # Back button
    if st.button("← Back to List"):
        st.session_state.grant_view = "list"
        st.session_state.selected_grant_id = None
        st.rerun()

    # Display basic information
    st.subheader("Basic Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Grant ID:** {grant_data['grant_id']}")
        st.markdown(f"**Grant Name:** {grant_data['grant_name']}")
        st.markdown(f"**Scheme:** {grant_data['grant_scheme']}")
        if grant_data['url']:
            st.markdown(f"**URL:** [{grant_data['url']}]({grant_data['url']})")

    with col2:
        st.metric("Funded Measure Links", len(related_measures))

    if grant_data['grant_summary']:
        st.markdown("**Summary:**")
        st.info(grant_data['grant_summary'])

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
                "biodiversity_priority": st.column_config.TextColumn("Priority", width="large"),
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
